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
from esp_components import get_esptool, get_baud_rate

# 导入分区工具
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "as_flash_firmware"))
from as_spifs_partition import get_nvs_info

# 导入 as_nvs_flash 模块
from as_nvs_flash import (
    check_nvs_data,
    generate_nvs_data,
    get_nvs_bin_path,
)


#------------------  配置区  ------------------

# 使用 esp_components 提供的工具路径
ESPTOOL = get_esptool()
BAUD_RATE = get_baud_rate()


#------------------  步骤5: 更新 NVS 添加 is_model_update 参数  ------------------

def update_nvs_with_model_flag():
    """
    在 NVS 中添加 is_model_update=1 参数

    Returns:
        生成的新 NVS bin 文件路径，失败返回 None
    """
    print("\n" + "=" * 60)
    print("步骤 5: 使用 is_model_update 标志更新 NVS")
    print("=" * 60)

    try:
        # 读取现有的 NVS 数据
        print("\n读取现有 NVS 数据...")
        nvs_info = check_nvs_data()

        if not nvs_info or not nvs_info.get("decoded"):
            print("\n错误: 无法解码 NVS 数据")
            return None

        # 获取现有信息
        info = nvs_info.get("info", {})
        print(f"\n现有 NVS 信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")

        # 添加 is_model_update 参数
        info["is_model_update"] = "1"
        print(f"\n✓ 已添加 is_model_update=1")

        # 生成新的 NVS bin 文件
        # 传入 nvs_info 以保留所有原有参数
        print("\n生成新的 NVS bin 文件...")
        generate_nvs_data(info, existing_nvs=nvs_info)

        # 获取生成的 NVS bin 文件路径
        nvs_bin_path = get_nvs_bin_path()

        if not os.path.exists(nvs_bin_path):
            print(f"\n错误: NVS bin 文件未找到: {nvs_bin_path}")
            return None

        print(f"✓ 新的 NVS bin 文件已生成: {nvs_bin_path}")
        return nvs_bin_path

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return None


#------------------  步骤6: 烧录新的 NVS bin 文件  ------------------

def flash_nvs_bin(port, nvs_bin, bin_type):
    """
    烧录新的 NVS bin 文件到 Flash

    Args:
        port: 串口号
        nvs_bin: NVS bin 文件路径
        bin_type: 固件类型（用于获取分区信息）

    Returns:
        烧录是否成功
    """
    print("\n" + "=" * 60)
    print("步骤 6: 烧录新的 NVS bin 到 Flash")
    print("=" * 60)

    try:
        # 获取 NVS 分区信息
        nvs_info = get_nvs_info(bin_type)
        if not nvs_info:
            raise RuntimeError(f"Failed to get NVS partition info for bin_type: {bin_type}")

        nvs_offset = nvs_info["offset"]
        print(f"\nNVS partition offset (from {bin_type}): {nvs_offset}")

        # NVS 文件较小，使用默认波特率更稳定
        cmd = [ESPTOOL, "--port", port, "write_flash", nvs_offset, nvs_bin]
        print(f"执行命令: {' '.join(cmd)}")
        print("正在烧录 NVS...\n")

        # 不捕获输出，让 esptool 的进度信息实时显示
        result = subprocess.run(cmd)

        if result.returncode != 0:
            print("\n错误: NVS bin 烧录失败")
            return False

        print("\n✓ NVS bin 烧录成功!")
        return True

    except Exception as e:
        print(f"\n错误: {e}")
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
    print("步骤 7: 重启 ESP32")
    print("=" * 60)

    try:
        # 使用 esptool 的 run 命令重启设备
        cmd = [ESPTOOL, "--port", port, "run"]
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            print("\n警告: 重启命令返回非零退出码")
            print(f"标准输出: {result.stdout}")
            print(f"标准错误: {result.stderr}")
            # 即使返回错误，设备可能已经重启
            print("设备可能已经重启")

        print("✓ ESP32 重启命令已发送")
        return True

    except subprocess.TimeoutExpired:
        print("重启命令超时（预期行为）")
        print("✓ ESP32 重启命令已发送")
        return True
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False


#------------------  主函数  ------------------

def main(port, bin_type, reset_device=True):
    """
    主函数 - 更新 NVS 标志并烧录，可选重启设备

    Args:
        port: 串口号
        bin_type: 固件类型（用于获取分区信息）
        reset_device: 是否在完成后重启设备（默认 True）

    Returns:
        成功返回 True，失败返回 False
    """
    try:
        # 步骤5: 更新 NVS，添加 is_model_update=1
        nvs_bin = update_nvs_with_model_flag()
        if not nvs_bin:
            print("\n✗ 使用 is_model_update 标志更新 NVS 失败")
            return False

        # 步骤6: 烧录新的 NVS bin
        if not flash_nvs_bin(port, nvs_bin, bin_type):
            print("\n✗ 烧录新的 NVS bin 失败")
            return False

        # 步骤7: 重启 ESP32（可选）
        if reset_device:
            if not reset_esp32(port):
                print("\n✗ 重启 ESP32 失败")
                return False

        print("\n✓ 模型标志更新成功完成")
        return True

    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        return False
    except Exception as e:
        print(f"\n\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 示例：从命令行参数获取串口号和固件类型
    # 用法: python as_model_flag.py <port> <bin_type> [--no-reset]
    if len(sys.argv) < 3:
        print("用法: python as_model_flag.py <port> <bin_type> [--no-reset]")
        print("\n示例:")
        print("  python as_model_flag.py COM4 sdk_uvc_tw_plate")
        print("  python as_model_flag.py COM4 sdk_uvc_tw_plate --no-reset")
        sys.exit(1)

    port_arg = sys.argv[1]
    bin_type_arg = sys.argv[2]
    reset_arg = "--no-reset" not in sys.argv

    result = main(port_arg, bin_type_arg, reset_device=reset_arg)
    sys.exit(0 if result else 1)
