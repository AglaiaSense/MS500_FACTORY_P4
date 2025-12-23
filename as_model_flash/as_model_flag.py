#!/usr/bin/env python3
"""
模型更新标志模块
功能：更新 NVS 中的 is_model_update 参数并烧录
"""

import os
import sys
import subprocess

# 导入 ESP 组件工具
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from esp_components import get_esptool

# 导入 as_nvs_flash 模块
from as_nvs_flash import (
    check_nvs_data,
    generate_nvs_data,
    get_nvs_bin_path,
)


#------------------  配置区  ------------------

# 烧录波特率
BAUD_RATE = "115200"

# 分区配置 - NVS 分区
NVS_OFFSET = "0x9000"  # NVS 分区偏移地址

# 使用 esp_components 提供的工具路径
ESPTOOL = get_esptool()


#------------------  步骤5: 更新 NVS 添加 is_model_update 参数  ------------------

def update_nvs_with_model_flag():
    """
    在 NVS 中添加 is_model_update=1 参数

    Returns:
        生成的新 NVS bin 文件路径，失败返回 None
    """
    print("\n" + "=" * 60)
    print("Step 5: Update NVS with is_model_update flag")
    print("=" * 60)

    try:
        # 读取现有的 NVS 数据
        print("\nReading existing NVS data...")
        nvs_info = check_nvs_data()

        if not nvs_info or not nvs_info.get("decoded"):
            print("\nError: Cannot decode NVS data")
            return None

        # 获取现有信息
        info = nvs_info.get("info", {})
        print(f"\nExisting NVS info:")
        for key, value in info.items():
            print(f"  {key}: {value}")

        # 添加 is_model_update 参数
        info["is_model_update"] = "1"
        print(f"\n✓ Added is_model_update=1")

        # 生成新的 NVS bin 文件
        # 传入 nvs_info 以保留所有原有参数
        print("\nGenerating new NVS bin file...")
        generate_nvs_data(info, existing_nvs=nvs_info)

        # 获取生成的 NVS bin 文件路径
        nvs_bin_path = get_nvs_bin_path()

        if not os.path.exists(nvs_bin_path):
            print(f"\nError: NVS bin file not found: {nvs_bin_path}")
            return None

        print(f"✓ New NVS bin file generated: {nvs_bin_path}")
        return nvs_bin_path

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return None


#------------------  步骤6: 烧录新的 NVS bin 文件  ------------------

def flash_nvs_bin(port, nvs_bin):
    """
    烧录新的 NVS bin 文件到 Flash

    Args:
        port: 串口号
        nvs_bin: NVS bin 文件路径

    Returns:
        烧录是否成功
    """
    print("\n" + "=" * 60)
    print("Step 6: Flash new NVS bin to Flash")
    print("=" * 60)

    try:
        cmd = [ESPTOOL, "--port", port, "--baud", BAUD_RATE, "write_flash", NVS_OFFSET, nvs_bin]
        print(f"Execute command: {' '.join(cmd)}")
        print(f"Using baud rate: {BAUD_RATE}")
        print("Flashing NVS...\n")

        # 不捕获输出，让 esptool 的进度信息实时显示
        result = subprocess.run(cmd)

        if result.returncode != 0:
            print("\nError: Failed to flash NVS bin")
            return False

        print("\n✓ NVS bin flashed successfully!")
        return True

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


#------------------  步骤7: 重启 ESP32  ------------------

def reset_esp32(port):
    """
    重启 ESP32 设备

    Args:
        port: 串口号

    Returns:
        重启是否成功
    """
    print("\n" + "=" * 60)
    print("Step 7: Reset ESP32")
    print("=" * 60)

    try:
        # 使用 esptool 的 run 命令重启设备
        cmd = [ESPTOOL, "--port", port, "run"]
        print(f"Execute command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            print("\nWarning: Reset command returned non-zero exit code")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            # 即使返回错误，设备可能已经重启
            print("Device may have been reset anyway")

        print("✓ ESP32 reset command sent")
        return True

    except subprocess.TimeoutExpired:
        print("Reset command timed out (expected behavior)")
        print("✓ ESP32 reset command sent")
        return True
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


#------------------  主函数  ------------------

def main(port, reset_device=True):
    """
    主函数 - 更新 NVS 标志并烧录，可选重启设备

    Args:
        port: 串口号
        reset_device: 是否在完成后重启设备（默认 True）

    Returns:
        成功返回 True，失败返回 False
    """
    try:
        # 步骤5: 更新 NVS，添加 is_model_update=1
        nvs_bin = update_nvs_with_model_flag()
        if not nvs_bin:
            print("\n✗ Failed to update NVS with is_model_update flag")
            return False

        # 步骤6: 烧录新的 NVS bin
        if not flash_nvs_bin(port, nvs_bin):
            print("\n✗ Failed to flash new NVS bin")
            return False

        # 步骤7: 重启 ESP32（可选）
        if reset_device:
            if not reset_esp32(port):
                print("\n✗ Failed to reset ESP32")
                return False

        print("\n✓ Model flag update completed successfully")
        return True

    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user")
        return False
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 示例：从命令行参数获取串口号
    # 用法: python as_model_flag.py <port> [--no-reset]
    if len(sys.argv) < 2:
        print("Usage: python as_model_flag.py <port> [--no-reset]")
        print("\nExample:")
        print("  python as_model_flag.py COM4")
        print("  python as_model_flag.py COM4 --no-reset")
        sys.exit(1)

    port_arg = sys.argv[1]
    reset_arg = "--no-reset" not in sys.argv

    result = main(port_arg, reset_device=reset_arg)
    sys.exit(0 if result else 1)
