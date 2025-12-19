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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from esp_components import get_esp_idf_python, get_nvs_tool_path, get_esptool

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

# NVS 分区配置
NVS_OFFSET = "0x9000"
NVS_SIZE = "0x10000"  # 64KB


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
    print(f"  Converting to CSV format: {output_file}")

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

    print(f"  CSV file saved: {os.path.abspath(output_file)}")


#------------------  从设备读取 NVS 和 MAC  ------------------


def read_flash_and_mac(port):
    """
    从设备读取 NVS 分区数据并获取 MAC 地址

    Args:
        port: 串口号

    Returns:
        MAC 地址字符串
    """
    print("=" * 60)
    print("Step 1: Connect device and read Flash NVS partition")
    print("=" * 60)

    # 初始化临时目录
    init_temp_dir()

    cmd = [ESPTOOL, "--port", port, "read_flash", NVS_OFFSET, NVS_SIZE, READ_BIN]
    print(f"Execute command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    # 检查是否成功
    if result.returncode != 0:
        print("\n" + "!" * 60)
        print("Error: Cannot connect to device or read Flash")
        print("!" * 60)
        print("\nPlease check:")
        print("  1. Device is connected to " + port)
        print("  2. COM port number is correct")
        print("  3. Device is in download mode (Bootloader)")
        print("  4. Serial port is not used by other programs")

        # 打印详细错误信息
        print("\n" + "-" * 60)
        print("Detailed error info:")
        print("-" * 60)

        # 打印标准输出（如果有）
        if result.stdout.strip():
            print(result.stdout)

        # 打印标准错误输出（通常包含错误详情）
        if result.stderr.strip():
            print(result.stderr)
        else:
            print("(No error details)")

        print("-" * 60)
        raise RuntimeError("Failed to read Flash")

    # 从输出中提取 MAC 地址
    mac = None
    for line in result.stdout.splitlines():
        if "Detecting chip type" in line:
            print(f"  Detected chip: {line.split('...')[-1].strip()}")
        if "Chip is" in line:
            print(f"  {line.strip()}")
        if "MAC:" in line:
            mac = line.split("MAC:")[-1].strip()
            print(f"  MAC address: {mac}")

    if not mac:
        raise RuntimeError("Cannot read MAC address from device")

    print(f"✓ Successfully read NVS data to file: {READ_BIN}")
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
    print("Step 2: Check and decode NVS data")
    print("=" * 60)

    # 检查 NVS raw 文件是否存在
    full_path = os.path.abspath(READ_BIN)
    if not os.path.exists(READ_BIN):
        print(f"Error: NVS raw file not found")
        print(f"  Search path: {full_path}")
        return None

    file_size = os.path.getsize(READ_BIN)
    print(f"  File size: {file_size} bytes")

    # 读取文件的前 256 字节，快速检查 NVS 分区状态
    with open(READ_BIN, "rb") as f:
        first_bytes = f.read(256)

    # 检查是否是空白分区（全是 0xFF）
    if all(b == 0xFF for b in first_bytes):
        print("  Detected: NVS partition is blank (all 0xFF)")
        print("  ✓ Device not registered, can write new data")
        return None

    # NVS 分区有数据，尝试解码
    print("  Detected: NVS partition has data")

    # 检查官方工具是否存在
    if not os.path.exists(NVS_TOOL_PATH):
        print(f"\n  Error: Cannot find official nvs_tool.py")
        print(f"  Search path: {NVS_TOOL_PATH}")
        return {"has_data": True, "decoded": False}

    # 使用官方 nvs_tool.py 解析（minimal 格式）
    print("\n  Trying to decode NVS data...")
    cmd = [ESP_IDF_PYTHON, NVS_TOOL_PATH, READ_BIN, "-d", "minimal"]
    print(f"  Execute command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("  Warning: Cannot decode NVS data")
        print(f"  Error info: {result.stderr if result.stderr else result.stdout}")
        print("\n  Possible reasons:")
        print("    1. NVS partition data corrupted")
        print("    2. NVS partition format incompatible")
        print("    3. Partition data is encrypted")
        return {"has_data": True, "decoded": False}

    # 解码成功，打印原始输出
    print("  ✓ NVS data decoded successfully!")

    print("\n" + "-" * 60)
    print("  NVS data content:")
    print("-" * 60)
    if result.stdout.strip():
        print(result.stdout)
    print("-" * 60)

    # 转换为 CSV 格式
    try:
        convert_to_csv(result.stdout, READ_CSV)
    except Exception as e:
        print(f"  Warning: Failed to convert CSV: {e}")
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
            print(f"  Failed to parse CSV: {e}")

    if nvs_info:
        print("\n  Device registration info:")
        for key, value in nvs_info.items():
            print(f"    {key}: {value}")

        return {"has_data": True, "decoded": True, "info": nvs_info}
    else:
        print("  Warning: No valid data extracted")
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
        python as_nvs_read.py [PORT]

    参数:
        PORT: 串口号，默认为 COM4

    示例:
        python as_nvs_read.py
        python as_nvs_read.py COM5
    """
    import sys

    # 获取串口号参数
    port = sys.argv[1] if len(sys.argv) > 1 else "COM4"

    print("=" * 60)
    print("  NVS Read and Parse Tool")
    print("=" * 60)
    print(f"Port: {port}")
    print("=" * 60)

    try:
        # 读取 Flash 和 MAC 地址
        mac = read_flash_and_mac(port)
        print(f"\n✓ MAC Address: {mac}")

        # 检查 NVS 数据
        nvs_info = check_nvs_data()

        if nvs_info and nvs_info.get("decoded"):
            print("\n" + "=" * 60)
            print("  NVS Data Summary")
            print("=" * 60)
            info = nvs_info.get("info", {})
            for key, value in info.items():
                print(f"  {key}: {value}")
            print("=" * 60)
        else:
            print("\n✓ NVS partition is empty or cannot be decoded")

        print("\n✓ Operation completed successfully!")
        return 0

    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
