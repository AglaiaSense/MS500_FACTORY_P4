#!/usr/bin/env python3
"""
模型转换工具主函数
功能：根据 device_id 和模型路径调用 model_convert 进行模型转换
"""

import os
import sys
from pathlib import Path

# 导入 model_convert 函数
from model_conversion import model_convert


#------------------  主函数  ------------------

def main(device_id, model_path, output_dir=None):
    """
    模型转换主函数

    Args:
        device_id: 设备 ID（32位十六进制字符串）
        model_path: 模型文件路径（通常是 packerOut.zip）
        output_dir: 输出目录，如果为 None 则保存到当前目录

    Returns:
        转换后的文件路径，失败返回 None
    """
    print("=" * 60)
    print("  Model Conversion Tool")
    print("=" * 60)
    print(f"Device ID: {device_id}")
    print(f"Model Path: {model_path}")
    print(f"Output Dir: {output_dir if output_dir else 'Current directory'}")
    print("=" * 60)

    # 检查模型文件是否存在
    if not os.path.exists(model_path):
        print(f"Error: Model file not found: {model_path}")
        return None

    # 调用 model_convert 函数
    try:
        result_path = model_convert(
            device_id=device_id,
            model_path=model_path,
            output_dir=output_dir
        )

        if result_path:
            print("\n" + "=" * 60)
            print("  ✓ Model Conversion Completed Successfully")
            print("=" * 60)
            print(f"Output file: {result_path}")
            return result_path
        else:
            print("\n" + "=" * 60)
            print("  ✗ Model Conversion Failed")
            print("=" * 60)
            return None

    except Exception as e:
        print(f"\nError during as_model_conversion conversion: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 示例：从命令行参数获取 device_id 和 model_path
    # 用法: python as_model_tools.py <device_id> <model_path> [output_dir]

    # if len(sys.argv) < 3:
    #     print("Usage: python as_model_tools.py <device_id> <model_path> [output_dir]")
    #     print("\nExample:")
    #     print("  python as_model_tools.py 100B50501A2101059064011000000000 type_model/ped_alerm/packerOut.zip")
    #     print("  python as_model_tools.py 100B50501A2101059064011000000000 type_model/ped_alerm/packerOut.zip output/")
    #     sys.exit(1)

    device_id_arg = "100B50501A2101059064011000000000"
    model_path_arg = "type_model/ped_alerm/packerOut.zip"
    output_dir_arg = "type_model/ped_alerm/packerOut.zip output/"

    result = main(device_id_arg, model_path_arg, output_dir_arg)
    sys.exit(0 if result else 1)
