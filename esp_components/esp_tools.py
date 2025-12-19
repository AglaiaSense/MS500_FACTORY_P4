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


# ========== 工具验证函数 ==========

def verify_esp_tools():
    """验证所有 ESP 工具是否可用"""
    print("Verifying ESP tools...")
    all_ok = True

    # 检查 ESP-IDF Python 环境
    if not os.path.exists(ESP_IDF_PYTHON):
        print(f"[ERROR] ESP_IDF_PYTHON not found: {ESP_IDF_PYTHON}")
        all_ok = False
    else:
        print(f"[OK] ESP_IDF_PYTHON: {ESP_IDF_PYTHON}")

    # 检查本地 NVS 工具
    if not os.path.exists(NVS_TOOL_PATH):
        print(f"[ERROR] NVS_TOOL_PATH not found: {NVS_TOOL_PATH}")
        all_ok = False
    else:
        print(f"[OK] NVS_TOOL_PATH: {NVS_TOOL_PATH}")

    # 检查本地 FATFS 生成工具
    if not os.path.exists(FATFS_GEN_TOOL):
        print(f"[ERROR] FATFS_GEN_TOOL not found: {FATFS_GEN_TOOL}")
        all_ok = False
    else:
        print(f"[OK] FATFS_GEN_TOOL: {FATFS_GEN_TOOL}")

    # 检查 esptool（通过命令行）
    import subprocess
    try:
        result = subprocess.run([ESPTOOL, "version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"[OK] ESPTOOL: {ESPTOOL}")
        else:
            print(f"[ERROR] ESPTOOL command failed")
            all_ok = False
    except Exception as e:
        print(f"[ERROR] ESPTOOL not available: {e}")
        all_ok = False

    if all_ok:
        print("All ESP tools verified successfully!")
    else:
        print("Some ESP tools are missing or unavailable!")

    return all_ok
