"""
NVS 读取和解析模块

功能：
1. 初始化临时目录
2. 从设备读取 NVS 分区数据
3. 解析 NVS 数据并转换为 CSV 格式
4. 检查设备注册状态
"""

import os
import sys
import subprocess

# 导入 ESP 组件工具
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from esp_components import get_esp_idf_python, get_nvs_tool_path, get_esptool, run_command

# 导入分区工具
from as_flash_firmware import get_nvs_info

# ========== 配置区 ==========
# 使用 esp_components 提供的工具路径
ESP_IDF_PYTHON = get_esp_idf_python()
NVS_TOOL_PATH = get_nvs_tool_path()
ESPTOOL = get_esptool()

# 临时文件目录（在 as_nvs_flash 目录下）
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")

# 临时文件路径
READ_BIN = os.path.join(TEMP_DIR, "read.bin")
READ_CSV = os.path.join(TEMP_DIR, "read.csv")


#------------------  初始化临时目录  ------------------


def init_temp_dir():
    """
    初始化临时文件目录
    """
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)


#------------------  NVS 数据格式转换  ------------------


def convert_to_csv(nvs_output, output_file):
    """
    将 nvs_tool.py 的输出转换为 CSV 格式
    """
    print(f"  转换为 CSV 格式: {output_file}")

    # 解析 nvs_tool.py 的 minimal 输出
    # 格式: namespace:key = value
    entries = []

    for line in nvs_output.splitlines():
        line = line.strip()

        if not line or line.startswith("Page"):
            continue

        # 解析 namespace:key = value 格式
        if " = " in line:
            key_part, value_part = line.split(" = ", 1)

            if ":" in key_part:
                namespace, key = key_part.split(":", 1)
                namespace = namespace.strip()
                key = key.strip()

                # 解析值
                value = value_part.strip()

                # 处理字节字符串 b'...'
                if value.startswith("b'") and value.endswith("'"):
                    value = value[2:-1]  # 移除 b' 和 '
                    # 移除末尾的 \x00
                    value = value.replace("\\x00", "")

                # 推断类型
                data_type = "string"
                if value.isdigit():
                    data_type = "u32"

                entries.append(
                    {
                        "namespace": namespace,
                        "key": key,
                        "type": data_type,
                        "value": value,
                    }
                )

    # 写入 CSV 文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("key,type,encoding,value\n")

        current_ns = None
        for entry in entries:
            # 写入 namespace 行
            if entry["namespace"] != current_ns:
                current_ns = entry["namespace"]
                f.write(f"{current_ns},namespace,,\n")

            # 写入数据行
            f.write(f"{entry['key']},data,{entry['type']},{entry['value']}\n")

    print(f"  CSV 文件已保存: {os.path.abspath(output_file)}")


#------------------  从设备读取 NVS 和 MAC  ------------------


def read_flash_and_mac(port, bin_type):
    """
    从设备读取 NVS 分区数据并获取 MAC 地址

    Args:
        port: 串口号
        bin_type: 固件类型（用于获取分区信息），默认 sdk_uvc_tw_plate

    Returns:
        MAC 地址字符串
    """
    print("-" * 60)
    print("步骤 1: 连接设备并读取 Flash NVS 分区")
    print("-" * 60)

    # 初始化临时目录
    init_temp_dir()

    # 获取 NVS 分区信息
    nvs_partition_info = get_nvs_info(bin_type)
    if not nvs_partition_info:
        raise RuntimeError(f"Failed to get NVS partition info for bin_type: {bin_type}")

    nvs_offset = nvs_partition_info["offset"]
    nvs_size = nvs_partition_info["size"]
    print(f"NVS partition (from {bin_type}):")
    print(f"  Offset: {nvs_offset}")
    print(f"  Size:   {nvs_size}")

    cmd = [*ESPTOOL, "--port", port, "read_flash", nvs_offset, nvs_size, READ_BIN]
    result = run_command(cmd)

    # 检查是否成功
    if result.returncode != 0:
        print("\n" + "!" * 60)
        print("错误: 无法连接到设备或读取 Flash")
        print("!" * 60)
        print("\n请检查:")
        print("  1. 设备是否正确连接到 " + port)
        print("  2. COM 端口号是否正确")
        print("  3. 设备是否处于下载模式（Bootloader）")
        print("  4. 串口是否被其他程序占用")

        # 打印详细错误信息
        print("\n" + "-" * 60)
        print("详细错误信息:")
        print("-" * 60)

        # 打印标准输出（如果有）
        if result.stdout.strip():
            print(result.stdout)

        # 打印标准错误输出（通常包含错误详情）
        if result.stderr.strip():
            print(result.stderr)
        else:
            print("（无错误详情）")

        print("-" * 60)
        raise RuntimeError("读取 Flash 失败")

    # 从输出中提取 MAC 地址
    mac = None
    for line in result.stdout.splitlines():
        if "Detecting chip type" in line:
            print(f"  检测到芯片: {line.split('...')[-1].strip()}")
        if "Chip is" in line:
            print(f"  {line.strip()}")
        if "MAC:" in line:
            mac = line.split("MAC:")[-1].strip()
            print(f"  MAC 地址: {mac}")

    if not mac:
        raise RuntimeError("无法从设备读取 MAC 地址")

    print(f"✓ 成功读取 NVS 数据到文件: {READ_BIN}")
    return mac


#------------------  检查 NVS 数据  ------------------


def check_nvs_data():
    """
    检查并解码 NVS 数据，判断设备是否已有注册信息

    Returns:
        dict: NVS 信息字典，包含 has_data, decoded, info 等字段
        None: 如果 NVS 为空或无法解析
    """
    print("\n" + "=" * 60)
    print("步骤 2: 检查并解码 NVS 数据")
    print("-" * 60)

    # 检查 NVS raw 文件是否存在
    full_path = os.path.abspath(READ_BIN)
    if not os.path.exists(READ_BIN):
        print(f"错误: NVS 原始文件未找到")
        print(f"  搜索路径: {full_path}")
        return None

    file_size = os.path.getsize(READ_BIN)
    print(f"  文件大小: {file_size} 字节")

    # 读取文件的前 256 字节，快速检查 NVS 分区状态
    with open(READ_BIN, "rb") as f:
        first_bytes = f.read(256)

    # 检查是否是空白分区（全是 0xFF）
    if all(b == 0xFF for b in first_bytes):
        print("  检测到: NVS 分区为空白（全是 0xFF）")
        print("  ✓ 设备未注册，可以写入新数据")
        return None

    # NVS 分区有数据，尝试解码
    print("  检测到: NVS 分区有数据")

    # 检查官方工具是否存在
    if not os.path.exists(NVS_TOOL_PATH):
        print(f"\n  错误: 找不到官方 nvs_tool.py")
        print(f"  搜索路径: {NVS_TOOL_PATH}")
        return {"has_data": True, "decoded": False}

    # 使用官方 nvs_tool.py 解析（minimal 格式）
    print("\n  尝试解码 NVS 数据...")
    cmd = [ESP_IDF_PYTHON, NVS_TOOL_PATH, READ_BIN, "-d", "minimal"]
    result = run_command(cmd)

    if result.returncode != 0:
        print("  警告: 无法解码 NVS 数据")
        print(f"  错误信息: {result.stderr if result.stderr else result.stdout}")
        print("\n  可能的原因:")
        print("    1. NVS 分区数据损坏")
        print("    2. NVS 分区格式不兼容")
        print("    3. 分区数据已加密")
        return {"has_data": True, "decoded": False}

    # 解码成功，打印原始输出
    print("  ✓ NVS 数据解码成功!")

    print("\n" + "-" * 60)
    print("  NVS 数据内容:")
    print("-" * 60)
    if result.stdout.strip():
        print(result.stdout)
    print("-" * 60)

    # 转换为 CSV 格式
    try:
        convert_to_csv(result.stdout, READ_CSV)
    except Exception as e:
        print(f"  警告: 转换 CSV 失败: {e}")
        return {"has_data": True, "decoded": False}

    # 解析 CSV，提取关键信息
    nvs_info = {}
    if os.path.exists(READ_CSV):
        try:
            with open(READ_CSV, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[1:]:  # 跳过标题行
                    parts = line.strip().split(",")
                    if len(parts) >= 4:
                        key = parts[0]
                        value = parts[3] if len(parts) > 3 else ""
                        if key and key != "factory":  # 跳过 namespace
                            nvs_info[key] = value
        except Exception as e:
            print(f"  解析 CSV 失败: {e}")

    if nvs_info:
        # 检查并修正 g_camera_id 的前缀
        if "g_camera_id" in nvs_info:
            original_id = nvs_info["g_camera_id"]
            # 如果 g_camera_id 长度为 32 字符且前 4 位不是 "100B"，则替换为 "100B"
            if len(original_id) == 32 and original_id[:4] != "100B":
                corrected_id = "100B" + original_id[4:]
                nvs_info["g_camera_id"] = corrected_id
                print(f"\n  ⚠ g_camera_id 前缀已修正:")
                print(f"    原始值: {original_id}")
                print(f"    修正值: {corrected_id}")

        print("\n  设备注册信息:")
        for key, value in nvs_info.items():
            print(f"    {key}: {value}")

        return {"has_data": True, "decoded": True, "info": nvs_info}
    else:
        print("  警告: 未提取到有效数据")
        return {"has_data": True, "decoded": False}


#------------------  获取 NVS 原始 BIN 文件路径  ------------------


def get_nvs_raw_bin_path():
    """
    获取 NVS 原始 BIN 文件路径
    """
    return READ_BIN


#------------------  主函数  ------------------


def main():
    """
    主函数 - 可直接运行此文件进行 NVS 读取和解析

    使用方法:
        python as_nvs_read.py [PORT] [BIN_TYPE]

    参数:
        PORT: 串口号，默认为 COM4
        BIN_TYPE: 固件类型，默认为 sdk_uvc_tw_plate

    示例:
        python as_nvs_read.py
        python as_nvs_read.py COM5
        python as_nvs_read.py COM4 ped_alarm
    """
    import sys

    # 获取参数
    port = sys.argv[1] if len(sys.argv) > 1 else "COM4"
    bin_type = sys.argv[2] if len(sys.argv) > 2 else "sdk_uvc_tw_plate"

    print("-" * 60)
    print("  NVS 读取和解析工具")
    print("-" * 60)
    print(f"串口: {port}")
    print(f"固件类型: {bin_type}")
    print("-" * 60)

    try:
        # 读取 Flash 和 MAC 地址
        mac = read_flash_and_mac(port, bin_type)
        print(f"\n✓ MAC 地址: {mac}")

        # 检查 NVS 数据
        nvs_info = check_nvs_data()

        if nvs_info and nvs_info.get("decoded"):
            print("\n" + "=" * 60)
            print("  NVS 数据摘要")
            print("-" * 60)
            info = nvs_info.get("info", {})
            for key, value in info.items():
                print(f"  {key}: {value}")
            print("-" * 60)
        else:
            print("\n✓ NVS 分区为空或无法解码")

        print("\n✓ 操作成功完成!")
        return 0

    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        return 1
    except Exception as e:
        print(f"\n\n错误: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
