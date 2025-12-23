#!/usr/bin/env python3
"""
模型下载模块
功能：从 NVS 读取 device_id，调用 as_model_auth.py 生成模型
"""

import os
import sys
import subprocess

# 导入 ESP 组件工具
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from esp_components import get_esptool

# 导入 as_nvs_flash 模块
from as_nvs_flash import (
    init_temp_dir as nvs_init_temp_dir,
    get_nvs_raw_bin_path,
    check_nvs_data,
)

# 导入 as_model_auth 模块
from as_model_flash.as_model_auth import generate_model_by_device_id


#------------------  配置区  ------------------

# 分区配置 - NVS 分区
NVS_OFFSET = "0x9000"  # NVS 分区偏移地址
NVS_SIZE = "0x10000"  # 64KB

# 使用 esp_components 提供的工具路径
ESPTOOL = get_esptool()


#------------------  步骤1: 从 NVS 读取 device_id  ------------------

def read_device_id_from_nvs(port):
    """
    从设备的 NVS 中读取 g_camera_id 作为 device_id

    Args:
        port: 串口号

    Returns:
        device_id 字符串，失败返回 None
    """
    print("=" * 60)
    print("Step 1: Read device_id from NVS")
    print("=" * 60)

    try:
        # 步骤 1.1: 从设备读取 NVS 原始数据
        print("\nReading NVS partition from device...")
        nvs_raw_bin = get_nvs_raw_bin_path()

        cmd = [ESPTOOL, "--port", port, "read_flash", NVS_OFFSET, NVS_SIZE, nvs_raw_bin]
        print(f"Execute command: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("\nError: Failed to read NVS from device")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            raise RuntimeError("Failed to read NVS from device")

        print(f"✓ NVS partition read successfully: {nvs_raw_bin}")

        # 步骤 1.2: 解码 NVS 数据
        print("\nDecoding NVS data...")
        nvs_info = check_nvs_data()

        if not nvs_info or not nvs_info.get("decoded"):
            print("\nError: Cannot decode NVS data")
            return None

        # 步骤 1.3: 从 NVS 中提取 g_camera_id (字符串类型)
        info = nvs_info.get("info", {})
        g_camera_id = info.get("g_camera_id", "")

        if not g_camera_id:
            print("\nError: g_camera_id not found in NVS")
            print("Available keys:", list(info.keys()))
            return None

        print(f"\n✓ Found g_camera_id in NVS: {g_camera_id}")

        # g_camera_id 已经是字符串格式，可以直接使用作为 device_id
        # 格式示例: "100B50501A2101026964011000000000"
        device_id = g_camera_id
        print(f"✓ Device ID: {device_id}")
        return device_id

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return None


#------------------  步骤2: 调用 as_model_auth.py 生成模型  ------------------

def generate_model_files(device_id, model_dir):
    """
    调用 as_model_auth.py 生成 AI 模型文件

    Args:
        device_id: 设备 ID
        model_dir: 模型目录名（如 "ped_alerm"）

    Returns:
        生成的模型文件的 temp 目录路径，失败返回 None
    """
    print("\n" + "=" * 60)
    print("Step 2: Generate AI model files")
    print("=" * 60)

    try:
        # 调用 as_model_auth.py 的 generate_model_by_device_id 函数
        print(f"\nCalling generate_model_by_device_id(device_id={device_id}, model_dir={model_dir})...")

        temp_dir = generate_model_by_device_id(
            device_id=device_id,
            model_dir=model_dir
        )

        if not temp_dir:
            print("\nError: Model generation failed")
            return None

        print(f"\n✓ Model generated successfully!")
        print(f"Temp directory: {temp_dir}")

        return temp_dir

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return None


#------------------  主函数  ------------------

def main(port, model_dir):
    """
    主函数 - 读取 device_id 并生成模型

    Args:
        port: 串口号
        model_dir: 模型目录名

    Returns:
        生成的模型文件 temp 目录路径，失败返回 None
    """
    try:
        # 初始化临时目录
        nvs_init_temp_dir()

        # 步骤1: 从 NVS 读取 device_id
        device_id = read_device_id_from_nvs(port)
        if not device_id:
            print("\n✗ Failed to read device_id from NVS")
            return None

        # 步骤2: 生成模型文件
        model_temp_dir = generate_model_files(device_id, model_dir)
        if not model_temp_dir:
            print("\n✗ Failed to generate model files")
            return None

        return model_temp_dir

    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user")
        return None
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 示例：从命令行参数获取串口号和模型目录
    # 用法: python as_model_down.py <port> <model_dir>
    if len(sys.argv) < 3:
        print("Usage: python as_model_down.py <port> <model_dir>")
        print("\nExample:")
        print("  python as_model_down.py COM4 ped_alerm")
        sys.exit(1)

    port_arg = sys.argv[1]
    model_dir_arg = sys.argv[2]

    result = main(port_arg, model_dir_arg)
    sys.exit(0 if result else 1)
