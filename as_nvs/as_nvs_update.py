"""
NVS 更新和烧录模块

功能：
1. 生成 NVS CSV 文件
2. 生成 NVS BIN 文件
3. 烧录 NVS 数据到设备
"""

import os
import sys
import subprocess

# 导入 ESP 组件工具
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from esp_components import get_esp_idf_python, get_nvs_gen_module, get_esptool

# ========== 配置区 ==========
# 使用 esp_components 提供的工具路径
ESP_IDF_PYTHON = get_esp_idf_python()
NVS_GEN_MODULE = get_nvs_gen_module()
ESPTOOL = get_esptool()

# 临时文件目录（在 as_nvs 目录下）
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")

# 临时文件路径
FACTORY_CSV = os.path.join(TEMP_DIR, "factory_data.csv")
FACTORY_BIN = os.path.join(TEMP_DIR, "factory_nvs.bin")

# NVS 分区配置
NVS_OFFSET = "0x9000"
NVS_SIZE = "0x10000"  # 64KB


#------------------  生成 NVS 数据  ------------------


def generate_nvs_data(info):
    """
    生成 NVS CSV 和 BIN 文件
    支持动态写入所有参数，不再限制固定字段

    Args:
        info: 设备信息字典，包含所有需要写入 NVS 的键值对
    """
    print("\n" + "=" * 60)
    print("Step 4: Generate NVS data (CSV and BIN)")
    print("=" * 60)

    # 确保临时目录存在
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    # 生成 CSV 文件
    print("\nGenerating NVS CSV file...")
    with open(FACTORY_CSV, "w", encoding="utf-8") as f:
        f.write("key,type,encoding,value\n")
        f.write("factory,namespace,,\n")

        # 动态写入所有参数
        # 自动推断类型：数字类型使用 u32，字符串类型使用 string
        for key, value in info.items():
            # 推断类型
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                data_type = "u32"
                value_str = str(value)
            else:
                data_type = "string"
                value_str = str(value)

            f.write(f"{key},data,{data_type},{value_str}\n")

    print(f"✓ CSV file generated: {FACTORY_CSV}")

    # 打印 CSV 文件内容
    print(f"\nCSV file path: {os.path.abspath(FACTORY_CSV)}")
    print("CSV file content:")
    print("-" * 40)
    try:
        with open(FACTORY_CSV, "r", encoding="utf-8") as f:
            csv_content = f.read()
            print(csv_content)
    except Exception as e:
        print(f"Cannot read CSV file: {e}")
    print("-" * 40)

    # 生成 NVS BIN 文件
    print("\nGenerating NVS BIN file...")

    # 使用 ESP-IDF 的 NVS 分区生成模块
    cmd = [
        ESP_IDF_PYTHON,
        "-m",
        NVS_GEN_MODULE,
        "generate",
        FACTORY_CSV,
        FACTORY_BIN,
        NVS_SIZE,
    ]
    print(f"Execute command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    # 打印返回码
    print(f"Command return code: {result.returncode}")

    if result.returncode != 0:
        print("\n" + "!" * 60)
        print("Error: Failed to generate NVS BIN")
        print("!" * 60)

        # 打印详细错误信息
        print("\n" + "-" * 60)
        print("Detailed error info:")
        print("-" * 60)

        print("STDOUT:")
        if result.stdout.strip():
            print(result.stdout)
        else:
            print("(stdout is empty)")

        print("\nSTDERR:")
        if result.stderr.strip():
            print(result.stderr)
        else:
            print("(stderr is empty)")

        print("-" * 60)
        raise RuntimeError("Failed to generate NVS partition")

    print(f"✓ NVS BIN file generated: {FACTORY_BIN}")
    print(f"  File path: {os.path.abspath(FACTORY_BIN)}")

    # 验证文件是否真的生成
    if os.path.exists(FACTORY_BIN):
        file_size = os.path.getsize(FACTORY_BIN)
        print(f"  File size: {file_size} bytes")


#------------------  烧录 NVS 数据  ------------------


def flash_nvs(port):
    """
    烧录 NVS 数据到设备（仅烧录 NVS，不烧录固件）

    Args:
        port: 串口号
    """
    print("\n" + "=" * 60)
    print("Step 5: Flash NVS data to device")
    print("=" * 60)

    cmd = [ESPTOOL, "--port", port, "write_flash", NVS_OFFSET, FACTORY_BIN]
    print(f"Execute command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("\n" + "!" * 60)
        print("Error: Failed to flash NVS data")
        print("!" * 60)

        # 打印详细错误信息
        print("\n" + "-" * 60)
        print("Detailed error info:")
        print("-" * 60)

        # 打印标准输出（如果有）
        if result.stdout.strip():
            print(result.stdout)

        # 打印标准错误输出
        if result.stderr.strip():
            print(result.stderr)
        else:
            print("(No error details)")

        print("-" * 60)
        raise RuntimeError("Failed to flash NVS data")

    print("✓ NVS data flashed successfully!")


#------------------  获取 NVS BIN 文件路径  ------------------


def get_nvs_bin_path():
    """
    获取生成的 NVS BIN 文件路径
    """
    return FACTORY_BIN
