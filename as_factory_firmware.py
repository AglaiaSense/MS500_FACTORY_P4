#!/usr/bin/env python3
"""
MS500 固件工厂烧录工具

功能说明:
调用 as_flash_firmware/as_firmware_tool.py 进行固件烧录

使用前准备:
1. 准备固件文件:
   - 在 as_flash_firmware/bin_type/ 目录下创建固件类型目录
   - 将固件 bin 文件和 partitions.csv 放入该目录

2. 设备连接:
   - 将 ESP32-P4 设备连接到电脑
   - 确认串口号 (默认 COM4，可在代码中修改 PORT 变量)
   - 确保设备处于可烧录状态

使用方法:
    python as_factory_firmware.py
"""

import os
import sys

# 导入固件烧录模块
from as_flash_firmware.as_firmware_tool import flash_firmware_with_config


#------------------  配置区  ------------------

# 串口号
PORT = "COM4"

# 固件类型（对应 as_flash_firmware/bin_type/ 下的目录名）
# 可选: "ms500_uvc", "sdk_uvc_tw_plate" 等
# BIN_TYPE = "ms500_uvc"
BIN_TYPE = "ped_alarm"


#------------------  主函数  ------------------

def main(port=None, bin_type=None):
    """
    主函数 - 固件烧录流程

    参数:
        port: 串口号，默认使用全局配置
        bin_type: 固件类型，默认使用全局配置

    返回:
        成功返回 True，失败返回 False
    """
    # 使用传入的参数或全局配置
    use_port = port if port is not None else PORT
    use_bin_type = bin_type if bin_type is not None else BIN_TYPE

    print("=" * 80)
    print("  MS500 固件工厂烧录工具")
    print("=" * 80)
    print(f"串口: {use_port}")
    print(f"固件类型: {use_bin_type}")
    print("=" * 80)

    try:
        # 调用 as_firmware_tool.py 的 flash_firmware_with_config 函数
        success = flash_firmware_with_config(use_port, use_bin_type)

        if success:
            print("\n" + "=" * 80)
            print("  ✓ 固件烧录完成")
            print("=" * 80)
            return True
        else:
            print("\n" + "=" * 80)
            print("  ✗ 固件烧录失败")
            print("=" * 80)
            return False

    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        return False
    except Exception as e:
        print(f"\n\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
