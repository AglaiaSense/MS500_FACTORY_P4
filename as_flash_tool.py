import os
import sys
import subprocess

# 导入 ESP 组件工具
from esp_components import get_esptool

# 设置 Windows 控制台编码为 UTF-8
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# ========== 配置区 ==========
# 使用 esp_components 提供的 esptool 路径
ESPTOOL = get_esptool()

# ESP32-P4 串口配置
PORT = "COM4"  # 修改为实际端口
BAUDRATE = "460800"

# ESP32-P4 Flash 配置
CHIP_TYPE = "esp32p4"
FLASH_MODE = "dio"
FLASH_FREQ = "80m"
FLASH_SIZE = "16MB"

# 固件文件目录
BUILD_DIR = "ms500_build"

# Flash 烧录地址映射表
FLASH_MAP = {
    "bootloader.bin": "0x2000",
    "ms500_p4.bin": "0x20000",
    "partition-table.bin": "0x8000",
    "ota_data_initial.bin": "0x19000",
    "storage.bin": "0x720000"
}


#------------------ 文件检查 ------------------

def check_bin_files():
    """
    检查 ms500_build 目录中的 bin 文件是否存在
    """
    print("=" * 60)
    print("步骤1: 检查固件文件")
    print("=" * 60)

    if not os.path.exists(BUILD_DIR):
        raise RuntimeError(f"错误: 找不到目录 '{BUILD_DIR}'")

    missing_files = []
    found_files = []

    for filename in FLASH_MAP.keys():
        file_path = os.path.join(BUILD_DIR, filename)
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


#------------------ 测试串口连接 ------------------

def test_connection(port):
    """
    测试串口连接并读取芯片信息
    """
    print("\n" + "=" * 60)
    print("步骤2: 测试串口连接")
    print("=" * 60)

    cmd = [ESPTOOL, "--port", port, "chip_id"]
    print(f"执行命令: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("\n" + "!" * 60)
        print("错误: 无法连接到设备")
        print("!" * 60)
        print("\n请检查:")
        print(f"  1. 设备是否正确连接到 {port}")
        print("  2. COM 端口号是否正确")
        print("  3. 设备是否处于下载模式（Bootloader）")
        print("  4. 串口是否被其他程序占用")

        # 打印详细错误信息
        print("\n" + "-" * 60)
        print("详细错误信息:")
        print("-" * 60)
        if result.stdout.strip():
            print(result.stdout)
        if result.stderr.strip():
            print(result.stderr)
        else:
            print("(无错误详情)")
        print("-" * 60)

        raise RuntimeError("串口连接失败")

    # 打印连接成功信息
    for line in result.stdout.splitlines():
        if "Detecting chip type" in line or "Chip is" in line or "MAC:" in line:
            print(f"  {line.strip()}")

    print("\n✓ 串口连接测试成功")
    return True


#------------------ 烧录固件 ------------------

def flash_firmware(port):
    """
    烧录所有固件文件到 ESP32-P4
    """
    print("\n" + "=" * 60)
    print("步骤3: 烧录固件到 ESP32-P4")
    print("=" * 60)

    # 构建 esptool 烧录命令
    cmd = [
        ESPTOOL,
        "-p", port,
        "-b", BAUDRATE,
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
        file_path = os.path.join(BUILD_DIR, filename)
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

    # 执行烧录
    print("开始烧录...")
    print("-" * 60)

    result = subprocess.run(cmd, capture_output=True, text=True)

    # 打印烧录过程输出
    if result.stdout:
        print(result.stdout)

    if result.returncode != 0:
        print("\n" + "!" * 60)
        print("错误: 固件烧录失败")
        print("!" * 60)

        if result.stderr.strip():
            print("\n详细错误信息:")
            print("-" * 60)
            print(result.stderr)
            print("-" * 60)

        raise RuntimeError("固件烧录失败")

    print("-" * 60)
    print("\n✓ 固件烧录成功!")
    return True


#------------------ 主函数 ------------------

def main():
    """
    固件烧录主流程
    """
    print("=" * 60)
    print("  MS500-P4 固件烧录工具")
    print("=" * 60)
    print(f"  芯片型号: {CHIP_TYPE}")
    print(f"  串口端口: {PORT}")
    print(f"  波特率: {BAUDRATE}")
    print(f"  Flash 大小: {FLASH_SIZE}")
    print("=" * 60)

    try:
        # 步骤1: 检查固件文件
        check_bin_files()

        # 步骤2: 测试串口连接
        test_connection(PORT)

        # 步骤3: 烧录固件
        flash_firmware(PORT)

        # 完成
        print("\n" + "=" * 60)
        print("  ✓ 固件烧录完成")
        print("=" * 60)
        print("\n提示:")
        print("  - 设备将自动重启")
        print("  - 可以使用串口监视器查看启动日志")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
