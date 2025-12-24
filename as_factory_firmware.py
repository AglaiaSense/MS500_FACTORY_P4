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


#------------------  主函数  ------------------

def main(port, bin_type):
    """
    主函数 - 固件烧录流程

    参数:
        port: 串口号（必需）
        bin_type: 固件类型（必需）

    返回:
        成功返回 True，失败返回 False
    """
    use_port = port
    use_bin_type = bin_type

    print("-" * 60)
    print("  固件工厂烧录 开始")
    print(f"串口: {use_port}")
    print(f"固件类型: {use_bin_type}")
    print("-" * 60)

    try:
        # 调用 as_firmware_tool.py 的 flash_firmware_with_config 函数
        success = flash_firmware_with_config(use_port, use_bin_type)

        if success:
            print("\n" + "=" * 80)
            print("  ✓ 固件烧录完成")
            print("-" * 60)
            return True
        else:
            print("\n" + "=" * 80)
            print("  ✗ 固件烧录失败")
            print("-" * 60)
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

    # 默认参数
    PORT = "COM4"               # 串口号
    BIN_TYPE = "sdk_uvc_tw_plate"  # 固件类型

    # 执行主函数
    sys.exit(main(PORT, BIN_TYPE))