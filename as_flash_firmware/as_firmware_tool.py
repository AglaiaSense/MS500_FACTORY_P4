import os
import sys
import subprocess
import csv

# 导入 ESP 组件工具
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from esp_components import get_esptool, get_baud_rate, test_port_connection, run_command

# 设置 Windows 控制台编码为 UTF-8
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# ========== 配置区 ==========
# 使用 esp_components 提供的 esptool 路径
ESPTOOL = get_esptool()
BAUD_RATE = get_baud_rate()

# ESP32-P4 串口配置
PORT = "COM4"  # 修改为实际端口

# ESP32-P4 Flash 配置
CHIP_TYPE = "esp32p4"
FLASH_MODE = "dio"
FLASH_FREQ = "80m"
FLASH_SIZE = "16MB"

# Flash 烧录地址映射表（从 partitions.csv 文件动态加载）
FLASH_MAP = {}

# 分区名称与bin文件的映射关系
PARTITION_TO_BIN = {
    "bootloader": ("bootloader.bin", "0x2000"),      # 固定地址
    "partition-table": ("partition-table.bin", "0x8000"),  # 固定地址
    "otadata": ("ota_data_initial.bin", None),       # 从partitions.csv读取
    "ota_0": ("ms500_p4.bin", None),                 # 从partitions.csv读取
    "factory": ("ms500_p4.bin", None),               # factory分区（用于sdk_uvc）
    "storage": ("storage.bin", None),                # 从partitions.csv读取
    "storage_dl": ("storage_dl.bin", None)           # 从partitions.csv读取
}


#------------------ 读取烧录配置 ------------------

def load_flash_config(bin_dir):
    """
    从指定目录的 partitions.csv 文件读取烧录配置

    解析 ESP-IDF 格式的分区表，结合 PARTITION_TO_BIN 映射生成烧录配置
    只烧录目录中实际存在的 bin 文件

    Args:
        bin_dir: bin 文件所在目录路径

    返回: 烧录文件映射字典 {文件名: 地址}
    """
    global FLASH_MAP

    partitions_csv = os.path.join(bin_dir, "partitions.csv")
    if not os.path.exists(partitions_csv):
        raise RuntimeError(f"未找到分区表文件: {partitions_csv}")

    print("-" * 60)
    print("步骤0: 读取分区表配置")
    print("-" * 60)
    print(f"固件目录: {bin_dir}")
    print(f"分区表文件: {partitions_csv}")
    print()

    # 解析 partitions.csv 获取分区地址
    partitions = {}
    with open(partitions_csv, 'r', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            # 跳过空行和注释行
            if not row or row[0].strip().startswith('#'):
                continue

            # 解析分区信息: Name, Type, SubType, Offset, Size
            if len(row) >= 4:
                name = row[0].strip()
                offset = row[3].strip().rstrip(',')  # 移除末尾的逗号
                # 跳过空地址（自动分配的分区）
                if offset:
                    partitions[name] = offset

    # 构建烧录文件映射
    flash_map = {}

    for partition_name, (bin_file, fixed_addr) in PARTITION_TO_BIN.items():
        # 检查 bin 文件是否存在
        bin_path = os.path.join(bin_dir, bin_file)
        if not os.path.exists(bin_path):
            print(f"  ⊗ 跳过: {bin_file} (文件不存在)")
            continue

        if fixed_addr:
            # 使用固定地址
            address = fixed_addr
        else:
            # 从分区表中查找地址
            if partition_name not in partitions:
                print(f"  ⊗ 跳过: {bin_file} (分区 '{partition_name}' 未在 partitions.csv 中定义)")
                continue
            address = partitions[partition_name]

        flash_map[bin_file] = address
        print(f"  ✓ {address} <- {bin_file}")

    if not flash_map:
        raise RuntimeError("未能从分区表生成烧录配置")

    print(f"\n✓ 成功加载 {len(flash_map)} 个烧录文件配置")
    FLASH_MAP = flash_map
    return flash_map


#------------------ 文件检查 ------------------

def check_bin_files(bin_dir):
    """
    检查 ms500_build 目录中的 bin 文件是否存在
    """
    print("-" * 60)
    print("步骤1: 检查固件文件")
    print("-" * 60)


    missing_files = []
    found_files = []

    for filename in FLASH_MAP.keys():
        file_path = os.path.join(bin_dir, filename)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"  ✓ {filename} ({file_size} bytes)")
            found_files.append(filename)
        else:
            print(f"  ✗ {filename} (未找到)")
            missing_files.append(filename)

    if missing_files:
        print("\n" + "!" * 60)
        print("错误: 以下文件缺失:")
        for f in missing_files:
            print(f"  - {f}")
        print("!" * 60)
        raise RuntimeError("固件文件不完整")

    print(f"\n✓ 所有固件文件检查完成 ({len(found_files)}/{len(FLASH_MAP)})")
    return True


#------------------ 测试串口连接（使用 esp_components 中的统一函数）------------------
# test_port_connection 函数已从 esp_components.esp_tools 导入


#------------------ 烧录固件 ------------------

def flash_firmware(port,bin_dir):
    """
    烧录所有固件文件到 ESP32-P4
    """
    print("\n" + "=" * 60)
    print("步骤3: 烧录固件到 ESP32-P4")
    print("-" * 60)

    # 构建 esptool 烧录命令
    cmd = [
        *ESPTOOL,
        "-p", port,
        "-b", BAUD_RATE,
        "--before", "default_reset",
        "--after", "hard_reset",
        "--chip", CHIP_TYPE,
        "write_flash",
        "--flash_mode", FLASH_MODE,
        "--flash_freq", FLASH_FREQ,
        "--flash_size", FLASH_SIZE
    ]

    # 添加所有固件文件及其地址
    for filename, address in FLASH_MAP.items():
        file_path = os.path.join(bin_dir, filename)
        cmd.extend([address, file_path])

    # 打印烧录命令
    print("执行命令:")
    print(f"  {' '.join(cmd)}")
    print()

    # 打印烧录文件列表
    print("烧录文件列表:")
    for filename, address in FLASH_MAP.items():
        print(f"  {address} <- {filename}")
    print()

    # 执行烧录（使用实时输出模式）
    print("开始烧录...")
    print("-" * 60)

    result = run_command(cmd, print_cmd=False, realtime_output=True)

    if result.returncode != 0:
        print("\n" + "!" * 60)
        print("错误: 固件烧录失败")
        print("!" * 60)
        raise RuntimeError("固件烧录失败")

    print("-" * 60)
    print("\n✓ 固件烧录成功!")
    return True


#------------------ 可被外部调用的主函数 ------------------

def flash_firmware_with_config(port, bin_type):
    """
    根据指定的固件类型和串口烧录固件（可被外部调用）

    参数:
        port: 串口号（如 "COM4"）
        bin_type: 固件类型（如 "ms500_uvc", "sdk_uvc_tw_plate"）

    返回:
        成功返回 True，失败返回 False
    """
    print("-" * 60)
    print("  MS500-P4 固件烧录工具")
    print("-" * 60)
    print(f"  芯片型号: {CHIP_TYPE}")
    print(f"  串口端口: {port}")
    print(f"  波特率: {BAUD_RATE}")
    print(f"  Flash 大小: {FLASH_SIZE}")
    print(f"  固件类型: {bin_type}")
    print("-" * 60)

    try:
        # 构建固件目录路径
        bin_dir = os.path.join(os.path.dirname(__file__), "bin_type", bin_type)

        if not os.path.exists(bin_dir):
            print(f"\n错误: 固件目录不存在: {bin_dir}")
            return False

        # 步骤0: 加载烧录配置
        load_flash_config(bin_dir)

        # 步骤1: 检查固件文件
        check_bin_files(bin_dir)

        # 步骤2: 测试串口连接
        test_port_connection(port)

        # 步骤3: 烧录固件
        flash_firmware(port,bin_dir)

        # 完成
        print("\n" + "=" * 60)
        print("  ✓ 固件烧录完成")
        print("-" * 60)
        print("\n提示:")
        print("  - 设备将自动重启")
        print("  - 可以使用串口监视器查看启动日志")
        print("-" * 60)

        return True

    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        return False
    except Exception as e:
        print(f"\n\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False

