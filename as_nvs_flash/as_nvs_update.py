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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from esp_components import get_esp_idf_python, get_nvs_gen_module, get_esptool, run_command

# 导入分区工具
from as_flash_firmware import get_nvs_info

# ========== 配置区 ==========
# 使用 esp_components 提供的工具路径
ESP_IDF_PYTHON = get_esp_idf_python()
NVS_GEN_MODULE = get_nvs_gen_module()
ESPTOOL = get_esptool()

# 临时文件目录（在 as_nvs_flash 目录下）
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")

# 临时文件路径
UPDATE_CSV = os.path.join(TEMP_DIR, "update.csv")
UPDATE_BIN = os.path.join(TEMP_DIR, "update.bin")


#------------------  生成 NVS 数据  ------------------


def generate_nvs_data(info, existing_nvs=None, bin_type="sdk_uvc_tw_plate"):
    """
    生成 NVS CSV 和 BIN 文件
    支持动态写入所有参数，并保留原有 NVS 中的参数

    Args:
        info: 设备信息字典，包含所有需要写入 NVS 的键值对（新数据）
        existing_nvs: 可选，原有的 NVS 数据字典（从 as_nvs_read.check_nvs_data() 获取）
                     如果提供，会保留原有参数，新参数会覆盖同名的旧参数
        bin_type: 固件类型（用于获取分区信息），默认 sdk_uvc_tw_plate
    """
    print("\n" + "=" * 60)
    print("步骤 4: 生成 NVS 数据（CSV 和 BIN）")
    print("=" * 60)

    # 获取 NVS 分区大小
    nvs_partition_info = get_nvs_info(bin_type)
    if not nvs_partition_info:
        raise RuntimeError(f"Failed to get NVS partition info for bin_type: {bin_type}")

    nvs_size = nvs_partition_info["size"]
    print(f"NVS partition size (from {bin_type}): {nvs_size}")

    # 确保临时目录存在
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    # 合并原有 NVS 数据和新数据
    # 原有参数作为基础，新参数会覆盖同名参数
    merged_data = {}

    if existing_nvs and existing_nvs.get("decoded") and existing_nvs.get("info"):
        print("\n保留现有的 NVS 参数...")
        existing_info = existing_nvs.get("info", {})
        merged_data.update(existing_info)
        print(f"  找到 {len(existing_info)} 个现有参数")

        # 显示被保留的参数
        preserved_keys = [k for k in existing_info.keys() if k not in info]
        if preserved_keys:
            print(f"  保留的参数: {', '.join(preserved_keys)}")

    # 新数据覆盖原有数据
    if info:
        print(f"\n添加/更新 {len(info)} 个新参数...")
        merged_data.update(info)

        # 显示被更新的参数
        updated_keys = [k for k in info.keys()]
        if updated_keys:
            print(f"  更新的参数: {', '.join(updated_keys)}")

    # 生成 CSV 文件
    print("\n生成 NVS CSV 文件...")
    with open(UPDATE_CSV, "w", encoding="utf-8") as f:
        f.write("key,type,encoding,value\n")
        f.write("factory,namespace,,\n")

        # 动态写入所有参数
        # 自动推断类型：数字类型使用 u32，字符串类型使用 string
        for key, value in merged_data.items():
            # 推断类型
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                data_type = "u32"
                value_str = str(value)
            else:
                data_type = "string"
                value_str = str(value)

            f.write(f"{key},data,{data_type},{value_str}\n")

    print(f"✓ CSV 文件已生成: {UPDATE_CSV}")

    # 打印 CSV 文件内容
    print(f"\nCSV 文件路径: {os.path.abspath(UPDATE_CSV)}")
    print("CSV 文件内容:")
    print("-" * 40)
    try:
        with open(UPDATE_CSV, "r", encoding="utf-8") as f:
            csv_content = f.read()
            print(csv_content)
    except Exception as e:
        print(f"无法读取 CSV 文件: {e}")
    print("-" * 40)

    # 生成 NVS BIN 文件
    print("\n生成 NVS BIN 文件...")

    # 使用 ESP-IDF 的 NVS 分区生成模块
    cmd = [
        ESP_IDF_PYTHON,
        "-m",
        NVS_GEN_MODULE,
        "generate",
        UPDATE_CSV,
        UPDATE_BIN,
        nvs_size,
    ]
    result = run_command(cmd)

    # 打印返回码
    print(f"命令返回码: {result.returncode}")

    if result.returncode != 0:
        print("\n" + "!" * 60)
        print("错误: 生成 NVS BIN 失败")
        print("!" * 60)

        # 打印详细错误信息
        print("\n" + "-" * 60)
        print("详细错误信息:")
        print("-" * 60)

        print("标准输出:")
        if result.stdout.strip():
            print(result.stdout)
        else:
            print("（标准输出为空）")

        print("\n标准错误:")
        if result.stderr.strip():
            print(result.stderr)
        else:
            print("（标准错误为空）")

        print("-" * 60)
        raise RuntimeError("生成 NVS 分区失败")

    print(f"✓ NVS BIN 文件已生成: {UPDATE_BIN}")
    print(f"  文件路径: {os.path.abspath(UPDATE_BIN)}")

    # 验证文件是否真的生成
    if os.path.exists(UPDATE_BIN):
        file_size = os.path.getsize(UPDATE_BIN)
        print(f"  文件大小: {file_size} 字节")


#------------------  烧录 NVS 数据  ------------------


def flash_nvs(port, bin_type="sdk_uvc_tw_plate"):
    """
    烧录 NVS 数据到设备（仅烧录 NVS，不烧录固件）

    Args:
        port: 串口号
        bin_type: 固件类型（用于获取分区信息），默认 sdk_uvc_tw_plate
    """
    print("\n" + "=" * 60)
    print("步骤 5: 烧录 NVS 数据到设备")
    print("=" * 60)

    # 获取 NVS 分区偏移地址
    nvs_partition_info = get_nvs_info(bin_type)
    if not nvs_partition_info:
        raise RuntimeError(f"Failed to get NVS partition info for bin_type: {bin_type}")

    nvs_offset = nvs_partition_info["offset"]
    print(f"NVS partition offset (from {bin_type}): {nvs_offset}")

    cmd = [ESPTOOL, "--port", port, "write_flash", nvs_offset, UPDATE_BIN]
    result = run_command(cmd)

    if result.returncode != 0:
        print("\n" + "!" * 60)
        print("错误: 烧录 NVS 数据失败")
        print("!" * 60)

        # 打印详细错误信息
        print("\n" + "-" * 60)
        print("详细错误信息:")
        print("-" * 60)

        # 打印标准输出（如果有）
        if result.stdout.strip():
            print(result.stdout)

        # 打印标准错误输出
        if result.stderr.strip():
            print(result.stderr)
        else:
            print("（无错误详情）")

        print("-" * 60)
        raise RuntimeError("烧录 NVS 数据失败")

    print("✓ NVS 数据烧录成功!")


#------------------  获取 NVS BIN 文件路径  ------------------


def get_nvs_bin_path():
    """
    获取生成的 NVS BIN 文件路径
    """
    return UPDATE_BIN
