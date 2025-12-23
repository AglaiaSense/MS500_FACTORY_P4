#!/usr/bin/env python3
"""
模型下载模块
功能：从 NVS 读取 g_camera_id，调用 as_model_conversion/as_model_auth.py 生成模型
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

# 导入 as_model_conversion/as_model_auth 模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "as_model_conversion"))
from as_model_auth import generate_model_by_device_id


#------------------  配置区  ------------------

# 分区配置 - NVS 分区
NVS_OFFSET = "0x9000"  # NVS 分区偏移地址
NVS_SIZE = "0x10000"  # 64KB

# 使用 esp_components 提供的工具路径
ESPTOOL = get_esptool()

#------------------  步骤1: 从 NVS 读取 g_camera_id  ------------------

def read_device_id_from_nvs(port):
    """
    从设备的 NVS 中读取 g_camera_id 作为 device_id

    参数:
        port: 串口号

    返回:
        device_id 字符串，失败返回 None
    """
    print("=" * 60)
    print("步骤 1: 从 NVS 读取 device_id")
    print("=" * 60)

    try:
        # 步骤 1.1: 从设备读取 NVS 原始数据
        print("\n正在从设备读取 NVS 分区...")
        nvs_raw_bin = get_nvs_raw_bin_path()

        cmd = [ESPTOOL, "--port", port, "read_flash", NVS_OFFSET, NVS_SIZE, nvs_raw_bin]
        print(f"执行命令: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("\n错误: 从设备读取 NVS 失败")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            raise RuntimeError("从设备读取 NVS 失败")

        print(f"✓ NVS 分区读取成功: {nvs_raw_bin}")

        # 步骤 1.2: 解码 NVS 数据
        print("\n正在解码 NVS 数据...")
        nvs_info = check_nvs_data()

        if not nvs_info or not nvs_info.get("decoded"):
            print("\n错误: 无法解码 NVS 数据")
            return None

        # 步骤 1.3: 从 NVS 中提取 g_camera_id (字符串类型)
        info = nvs_info.get("info", {})
        g_camera_id = info.get("g_camera_id", "")

        if not g_camera_id:
            print("\n错误: 在 NVS 中未找到 g_camera_id")
            print("可用的键:", list(info.keys()))
            return None

        print(f"\n✓ 在 NVS 中找到 g_camera_id: {g_camera_id}")

        # g_camera_id 已经是字符串格式，可以直接使用作为 device_id
        # 格式示例: "100B50501A2101026964011000000000"
        device_id = g_camera_id
        print(f"✓ 设备 ID: {device_id}")
        return device_id

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return None


#------------------  步骤2: 调用 as_model_auth.py 生成模型  ------------------

def generate_model_files(device_id, model_type):
    """
    调用 as_model_conversion/as_model_auth.py 生成 AI 模型文件

    参数:
        device_id: 设备 ID
        model_type: 模型类型（如 "ped_alerm"）

    返回:
        生成的 spiffs_dl 目录路径，失败返回 None
    """
    print("\n" + "=" * 60)
    print("步骤 2: 生成 AI 模型文件")
    print("=" * 60)

    try:
        # 调用 as_model_auth.py 的 generate_model_by_device_id 函数
        print(f"\n调用 generate_model_by_device_id(device_id={device_id}, model_type={model_type})...")

        spiffs_dl_dir = generate_model_by_device_id(
            device_id=device_id,
            model_type=model_type
        )

        if not spiffs_dl_dir:
            print("\n错误: 模型生成失败")
            return None

        print(f"\n✓ 模型生成成功!")
        print(f"SPIFFS DL 目录: {spiffs_dl_dir}")

        return spiffs_dl_dir

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return None


#------------------  主函数  ------------------

def main(port, model_type):
    """
    主函数 - 读取 device_id 并生成模型

    参数:
        port: 串口号
        model_type: 模型类型名

    返回:
        生成的 spiffs_dl 目录路径，失败返回 None
    """
    try:
        # 初始化临时目录
        nvs_init_temp_dir()

        # 步骤1: 从 NVS 读取 device_id
        device_id = read_device_id_from_nvs(port)
        if not device_id:
            print("\n✗ 从 NVS 读取 device_id 失败")
            return None

        # 步骤2: 生成模型文件
        spiffs_dl_dir = generate_model_files(device_id, model_type)
        if not spiffs_dl_dir:
            print("\n✗ 生成模型文件失败")
            return None

        return spiffs_dl_dir

    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        return None
    except Exception as e:
        print(f"\n\n错误: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 方式1：使用变量传参（直接运行时修改这里的变量）
    port = "COM4"
    model_type = "ped_alerm"

    result = main(port, model_type)
    sys.exit(0 if result else 1)

    # 方式2：使用命令行参数（如果需要命令行调用，注释掉上面，取消下面的注释）
    # if len(sys.argv) < 3:
    #     print("使用方法: python as_model_down.py <port> <model_type>")
    #     print("\n示例:")
    #     print("  python as_model_down.py COM4 ped_alerm")
    #     sys.exit(1)
    #
    # port_arg = sys.argv[1]
    # model_type_arg = sys.argv[2]
    #
    # result = main(port_arg, model_type_arg)
    # sys.exit(0 if result else 1)
