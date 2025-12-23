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

# 导入工厂生产模块
import as_factory_info
import as_factory_firmware
import as_factory_model


#------------------  配置区  ------------------

# 串口号
PORT = "COM4"

# 固件类型（对应 as_flash_firmware/bin_type/ 下的目录名）
# 可选: "ms500_uvc", "sdk_uvc_tw_plate" "ped_alarm"
BIN_TYPE = "ped_alarm"

# 模型类型（对应 as_model_conversion/type_model/ 下的目录名）
# 可选: "ped_alarm", "sdk_uvc_tw_plate" 等
MODEL_TYPE = "ped_alarm"


#------------------  主流程  ------------------

def main():
    """主函数 - 完整的工厂生产流程"""

    print("=" * 80)
    print("  MS500 工厂生产主程序")
    print("=" * 80)
    print(f"串口: {PORT}")
    print(f"固件类型: {BIN_TYPE}")
    print(f"模型类型: {MODEL_TYPE}")
    print("=" * 80)
    print("\n【工厂生产流程】")
    print("  1. 参数注册（NVS 烧录）")
    print("  2. 固件烧录")
    print("  3. 模型烧录")
    print("=" * 80)

    try:
        # 步骤1: 调用 as_factory_info.py 进行参数注册
        print("\n" + "=" * 80)
        print("【步骤 1/3】 参数注册（NVS 烧录）")
        print("=" * 80)

        as_factory_info.main()
        print("\n✓ 步骤 1 完成: 参数注册成功")

        # 步骤2: 调用 as_factory_firmware.py 进行固件烧录
        print("\n" + "=" * 80)
        print("【步骤 2/3】 固件烧录")
        print("=" * 80)

        result = as_factory_firmware.main(port=PORT, bin_type=BIN_TYPE)
        if not result:
            print("\n✗ 步骤 2 失败: 固件烧录失败")
            return 1

        print("\n✓ 步骤 2 完成: 固件烧录成功")

        # 步骤3: 调用 as_factory_model.py 进行模型烧录
        print("\n" + "=" * 80)
        print("【步骤 3/3】 模型烧录")
        print("=" * 80)

        result = as_factory_model.main(port=PORT, model_type=MODEL_TYPE)
        if result != 0:
            print("\n✗ 步骤 3 失败: 模型烧录失败")
            return 1

        print("\n✓ 步骤 3 完成: 模型烧录成功")

        # 完成
        print("\n" + "=" * 80)
        print("  ✓ 工厂生产流程完成")
        print("=" * 80)
        print(f"串口: {PORT}")
        print(f"固件类型: {BIN_TYPE}")
        print(f"模型类型: {MODEL_TYPE}")
        print("\n提示:")
        print("  - 设备已完成所有烧录步骤")
        print("  - 设备已自动重启")
        print("  - 可以使用串口监视器查看启动日志")
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
