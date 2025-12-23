#!/usr/bin/env python3
"""
MS500 AI 模型工厂烧录工具

功能说明:
1. 调用 as_model_down.py 获取 g_camera_id 并下载生成模型，得到 spiffs_dl 目录
2. 调用 as_model_flash.py 创建 storage_dl.bin 并烧录
3. 调用 as_model_flag.py 添加 is_model_update=1 并更新烧录 NVS bin

使用前准备:
1. 准备模型文件:
   - 在 as_model_conversion/type_model/ 目录下创建模型目录 (例如: ped_alerm)
   - 将 packerOut.zip 文件放入该目录
   - 将 network_info.txt 文件放入该目录

2. 设备连接:
   - 将 ESP32-P4 设备连接到电脑
   - 确认串口号 (默认 COM4，可在代码中修改 PORT 变量)
   - 确保设备处于可烧录状态

使用方法:
    python as_factory_model.py
"""

import os
import sys

# 导入子模块
from as_model_flash import as_model_down
from as_model_flash import as_model_flash
from as_model_flash import as_model_flag


#------------------  配置区  ------------------

# 串口号
PORT = "COM4"

# 模型类型（对应 as_model_conversion/type_model/ 下的目录名）
MODEL_TYPE = "ped_alerm"

# 固件类型（对应 as_flash_firmware/bin_type/ 下的目录名）
# BIN_TYPE = "sdk_uvc_tw_plate"
BIN_TYPE = "ped_alarm"


#------------------  主流程  ------------------

def main(port=None, model_type=None, bin_type=None):
    """
    主函数 - 完整的 AI 模型工厂烧录流程

    参数:
        port: 串口号，默认使用全局配置
        model_type: 模型类型，默认使用全局配置
        bin_type: 固件类型，默认使用全局配置

    返回:
        成功返回 0，失败返回 1
    """
    # 使用传入的参数或全局配置
    use_port = port if port is not None else PORT
    use_model_type = model_type if model_type is not None else MODEL_TYPE
    use_bin_type = bin_type if bin_type is not None else BIN_TYPE

    print("=" * 80)
    print("  MS500 AI 模型工厂烧录工具")
    print("=" * 80)
    print(f"串口: {use_port}")
    print(f"模型类型: {use_model_type}")
    print(f"固件类型: {use_bin_type}")
    print("=" * 80)

    try:
        # 步骤1: 调用 as_model_down.py 获取 device_id 并生成模型
        print("\n" + "=" * 80)
        print("【步骤 1/3】 获取 device_id 并生成模型")
        print("=" * 80)

        spiffs_dl_dir = as_model_down.main(use_port, use_model_type, use_bin_type)
        if not spiffs_dl_dir:
            print("\n✗ 步骤 1 失败: 生成模型失败")
            return 1

        print(f"\n✓ 步骤 1 完成: spiffs_dl 目录已生成")
        print(f"  路径: {spiffs_dl_dir}")

        # 步骤2: 调用 as_model_flash.py 创建并烧录 storage_dl.bin
        print("\n" + "=" * 80)
        print("【步骤 2/3】 创建并烧录 storage_dl.bin")
        print("=" * 80)

        if not as_model_flash.main(use_port, spiffs_dl_dir, use_bin_type):
            print("\n✗ 步骤 2 失败: 烧录模型失败")
            return 1

        print(f"\n✓ 步骤 2 完成: storage_dl.bin 已烧录")

        # 步骤3: 调用 as_model_flag.py 添加 is_model_update=1 并更新 NVS
        print("\n" + "=" * 80)
        print("【步骤 3/3】 更新 NVS 标志并重启设备")
        print("=" * 80)

        if not as_model_flag.main(use_port, use_bin_type, reset_device=True):
            print("\n✗ 步骤 3 失败: 更新 NVS 标志失败")
            return 1

        print(f"\n✓ 步骤 3 完成: is_model_update=1 已设置并烧录")

        # 完成
        print("\n" + "=" * 80)
        print("  ✓ AI 模型工厂烧录完成")
        print("=" * 80)
        print(f"串口: {use_port}")
        print(f"模型类型: {use_model_type}")
        print(f"固件类型: {use_bin_type}")
        print(f"SPIFFS DL 目录: {spiffs_dl_dir}")
        print(f"is_model_update: 1")
        print("\n设备已重启。模型更新将在启动时处理。")

        return 0

    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        return 1
    except Exception as e:
        print(f"\n\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
