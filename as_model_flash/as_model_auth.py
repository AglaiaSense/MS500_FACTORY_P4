#!/usr/bin/env python3
"""
AI 模型认证和打包工具（重构版本）
将模型文件上传到 AITRIOS 平台并完成打包发布流程

【重构说明】
- 不再依赖 model_config.json 文件
- 所有参数通过函数参数传入
- 支持灵活的模型目录和设备 ID 配置

使用方法:
    from as_model_auth import generate_model_by_device_id

    temp_dir = generate_model_by_device_id(
        device_id="100B50501A2101026964011000000000",
        model_dir="ped_alerm"
    )
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path
from typing import Optional

# 导入 model_conversion 模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "as_model_conversion"))
from model_conversion import model_convert


#------------------  核心函数  ------------------

def generate_model_by_device_id(
    device_id: str,
    model_dir: str,
    base_path: Optional[str] = None
) -> Optional[str]:
    """
    根据传入的 device_id 和 model_dir 生成模型文件

    Args:
        device_id: 设备 ID（32位十六进制字符串）
        model_dir: 模型目录名（如 "ped_alerm"），位于 as_model_conversion/type_model/ 下
        base_path: 基础路径，默认为项目根目录

    Returns:
        生成的模型文件解压后的 temp 目录路径，失败返回 None
    """
    print("\n" + "=" * 60)
    print("  Generate Model by Device ID")
    print("=" * 60)
    print(f"Device ID: {device_id}")
    print(f"Model Dir: {model_dir}")

    try:
        # 确定基础路径
        if base_path is None:
            # 默认为项目根目录（as_model_flash 的父目录）
            base_path = os.path.dirname(os.path.dirname(__file__))

        # 构建模型目录路径：base_path/as_model_conversion/type_model/model_dir
        model_full_path = os.path.join(base_path, "as_model_conversion", "type_model", model_dir)
        if not os.path.exists(model_full_path):
            print(f"Error: Model directory not found: {model_full_path}")
            return None

        print(f"Model path: {model_full_path}")

        # 查找 packerOut.zip 文件
        packerOut_path = os.path.join(model_full_path, "packerOut.zip")
        if not os.path.exists(packerOut_path):
            print(f"Error: packerOut.zip not found in {model_full_path}")
            return None

        print(f"PackerOut path: {packerOut_path}")

        # 创建输出目录和临时目录
        output_dir = os.path.join(model_full_path, "output")
        temp_base_dir = os.path.join(model_full_path, "temp")
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(temp_base_dir, exist_ok=True)

        print(f"Output directory: {output_dir}")
        print(f"Temp directory: {temp_base_dir}")

        # 使用 model_conversion.py 进行模型转换
        print("\n### Using model_conversion.py for model conversion")
        print("Note: model_conversion.py uses curl command to avoid SSL errors")

        # 调用 model_convert 函数
        downloaded_file = model_convert(device_id, packerOut_path, output_dir)

        if not downloaded_file:
            print("Error: Model conversion failed")
            return None

        print(f"\n✓ Model conversion successful!")
        print(f"Output file: {downloaded_file}")

        # 解压文件并返回解压后的目录路径
        zip_filename = os.path.basename(downloaded_file)
        folder_name = os.path.splitext(zip_filename)[0]
        extract_dir = os.path.join(temp_base_dir, folder_name)

        # 如果目录已存在，先删除
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)

        os.makedirs(extract_dir, exist_ok=True)

        print(f"\nExtracting {downloaded_file}")
        print(f"Target directory: {extract_dir}")

        with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        print(f"✓ Extracted to {extract_dir}")

        # 如果存在 network_info.txt，进行替换
        network_info_path = os.path.join(model_full_path, "network_info.txt")
        if os.path.exists(network_info_path):
            print("\n### Processing network_info.txt")
            # 查找并替换 network_info.txt
            replaced = False
            for root, dirs, files in os.walk(extract_dir):
                if 'network_info.txt' in files:
                    target_path = os.path.join(root, 'network_info.txt')
                    print(f"Replacing {target_path} with {network_info_path}")
                    shutil.copy2(network_info_path, target_path)
                    print(f"✓ network_info.txt replaced successfully")
                    replaced = True
                    break

            if not replaced:
                print("Warning: network_info.txt not found in extracted files")
        else:
            print("\n### network_info.txt not found in model directory, skipping replacement")

        # 返回解压后的具体目录路径（包含 network.fpk, network_info.txt, readme.json）
        print(f"\n✓ Model directory: {extract_dir}")
        return str(extract_dir)

    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


#------------------  主函数  ------------------

def main():
    """主函数 - 用于测试"""
    if len(sys.argv) < 3:
        print("Usage: python as_model_auth.py <device_id> <model_dir>")
        print("\nExample:")
        print("  python as_model_auth.py 100B50501A2101026964011000000000 ped_alerm")
        sys.exit(1)

    device_id_arg = sys.argv[1]
    model_dir_arg = sys.argv[2]

    result = generate_model_by_device_id(device_id_arg, model_dir_arg)

    if result:
        print(f"\n✓ Success! Model extracted to: {result}")
        sys.exit(0)
    else:
        print(f"\n✗ Failed to generate model")
        sys.exit(1)


if __name__ == "__main__":
    main()
