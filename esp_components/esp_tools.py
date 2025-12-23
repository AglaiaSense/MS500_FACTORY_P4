"""
ESP-IDF 工具路径配置模块
统一管理所有 ESP-IDF 相关工具的路径和配置
"""

import os
from pathlib import Path

# 获取esp_components目录的绝对路径
ESP_COMPONENTS_DIR = Path(__file__).parent.absolute()

# ========== ESP-IDF 工具路径配置 ==========

# ESP-IDF Python 环境路径（使用本地esp_components中的Python环境）
ESP_IDF_PYTHON = str(ESP_COMPONENTS_DIR / "python_env" / "Scripts" / "python.exe")

# ESP-IDF NVS 工具路径（使用本地工具）
NVS_TOOL_PATH = str(ESP_COMPONENTS_DIR / "nvs_tools" / "nvs_tool.py")

# FAT 文件系统镜像生成工具路径（使用本地工具）
FATFS_GEN_TOOL = str(ESP_COMPONENTS_DIR / "fatfs_tools" / "wl_fatfsgen.py")

# ESP32 烧录工具（使用本地Python环境中的esptool）
ESPTOOL = str(ESP_COMPONENTS_DIR / "python_env" / "Scripts" / "esptool.exe")

# 使用 ESP-IDF 的 NVS 分区生成模块（仅用于生成 BIN）
NVS_GEN_MODULE = "esp_idf_nvs_partition_gen"

# 默认串口波特率配置
BAUD_RATE = "460800"


# ========== 工具获取函数 ==========

def get_esp_idf_python():
    """获取 ESP-IDF Python 环境路径"""
    return ESP_IDF_PYTHON


def get_nvs_tool_path():
    """获取 NVS 工具路径（本地esp_components版本）"""
    return NVS_TOOL_PATH


def get_fatfs_gen_tool():
    """获取 FATFS 生成工具路径（本地esp_components版本）"""
    return FATFS_GEN_TOOL


def get_esptool():
    """获取 esptool 命令"""
    return ESPTOOL


def get_nvs_gen_module():
    """获取 NVS 分区生成模块名称"""
    return NVS_GEN_MODULE


def get_baud_rate():
    """获取默认串口波特率"""
    return BAUD_RATE


# ========== 串口测试函数 ==========

def test_port_connection(port):
    """
    测试串口连接并读取芯片信息

    参数:
        port: 串口号（例如：COM4, /dev/ttyUSB0）

    返回:
        连接成功返回 True，失败返回 False

    异常:
        连接失败时抛出 RuntimeError
    """
    import subprocess

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
        print("   2. COM 端口号是否正确")
        print("   3. 设备是否处于下载模式（Bootloader）")
        print("   4. 串口是否被其他程序占用")

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


# ========== 工具验证函数 ==========

