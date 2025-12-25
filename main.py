#!/usr/bin/env python3
"""
MS500 工厂生产主程序

功能说明:
整合完整的工厂生产流程：
1. 参数注册（NVS 烧录）
2. 固件烧录
3. 模型烧录

使用前准备:
1. 设备连接:
   - 将 ESP32-P4 设备连接到电脑
   - 确认串口号 (默认 COM4，可在代码中修改 PORT 变量)
   - 确保设备处于可烧录状态

2. 准备固件文件:
   - 在 as_flash_firmware/bin_type/ 目录下准备固件文件

3. 准备模型文件:
   - 在 as_model_conversion/type_model/ 目录下准备模型文件

使用方法:
    python main.py
"""

import sys
import os

# 导入工厂生产模块
import as_factory_info
import as_factory_firmware
import as_factory_model

# 导入配置模块
import as_ms500_config


#------------------  代码控制开关（类似 C 的 #if 0）  ------------------
# 设置为 False 可禁用对应步骤，True 为启用

ENABLE_STEP1_REGISTER = True   # 步骤1: 参数注册（NVS 烧录）
ENABLE_STEP2_FIRMWARE = True   # 步骤2: 固件烧录
ENABLE_STEP3_MODEL = True      # 步骤3: 模型烧录


#------------------  主流程  ------------------

def main():
    """主函数 - 完整的工厂生产流程"""

    try:
        # 从配置模块读取参数
        PORT = as_ms500_config.get_port()
        BIN_TYPE = as_ms500_config.get_bin_type()
        MODEL_TYPE = as_ms500_config.get_model_type()

        print("  MS500 Factory Production Program")
        print(f"Port: {PORT}")
        print(f"Firmware Type: {BIN_TYPE}")
        print(f"Model Type: {MODEL_TYPE}")
        print(f"\nEnabled Steps: ", end="")

        enabled_steps = []
        if ENABLE_STEP1_REGISTER:
            enabled_steps.append("参数注册")
        if ENABLE_STEP2_FIRMWARE:
            enabled_steps.append("固件烧录")
        if ENABLE_STEP3_MODEL:
            enabled_steps.append("模型烧录")
        print(" -> ".join(enabled_steps) if enabled_steps else "无")

        # 步骤1: 调用 as_factory_info.py 进行参数注册
        if ENABLE_STEP1_REGISTER:
            print("\n" + "=" * 80)
            print("【步骤 1/3】 参数注册（NVS 烧录）")
            print("=" * 80)
            as_factory_info.main(port=PORT, bin_type=BIN_TYPE)
            print("\n✓ 步骤 1 完成: 参数注册成功")
        else:
            print("\n⊘ 步骤 1 已跳过: 参数注册（ENABLE_STEP1_REGISTER = False）")

        # 步骤2: 调用 as_factory_firmware.py 进行固件烧录
        if ENABLE_STEP2_FIRMWARE:
            print("\n" + "=" * 80)
            print("【步骤 2/3】 固件烧录")
            print("=" * 80)
            result = as_factory_firmware.main(port=PORT, bin_type=BIN_TYPE)
            if not result:
                print("\n✗ 步骤 2 失败: 固件烧录失败")
                return 1
            print("\n✓ 步骤 2 完成: 固件烧录成功")
        else:
            print("\n⊘ 步骤 2 已跳过: 固件烧录（ENABLE_STEP2_FIRMWARE = False）")

        # 步骤3: 调用 as_factory_model.py 进行模型烧录
        if ENABLE_STEP3_MODEL:
            print("\n" + "=" * 80)
            print("【步骤 3/3】 模型烧录")
            print("=" * 80)

            result = as_factory_model.main(port=PORT, model_type=MODEL_TYPE, bin_type=BIN_TYPE)
            if result != 0:
                print("\n✗ 步骤 3 失败: 模型烧录失败")
                return 1
            print("\n✓ 步骤 3 完成: 模型烧录成功")
        else:
            print("\n⊘ 步骤 3 已跳过: 模型烧录（ENABLE_STEP3_MODEL = False）")

        # 完成
        print("\n" + "=" * 80)
        print("  ✓ 工厂生产流程完成")
        print("=" * 80)

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
