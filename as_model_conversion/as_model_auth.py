#!/usr/bin/env python3
"""
AI 模型认证和打包工具（优化版本）
将模型文件上传到 AITRIOS 平台并完成打包发布流程

【优化说明】
- 不再依赖 model_config.json 文件
- 外部只需传入 device_id 和 model_type
- type_model 目录仅存放模型文件（packerOut.zip 和 network_info.txt）
- 工作目录统一在 as_model_conversion/temp/{device_id}/ 下
- 分层处理：目录创建 → 模型转换 → ZIP解压 → 文件复制 → 组装spiffs_dl

使用方法:
    from as_model_auth import generate_model_by_device_id

    spiffs_dir = generate_model_by_device_id(
        device_id="100B50501A2101059064011000000000",
        model_type="ped_alerm"
    )
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Tuple

# 导入 model_conversion 模块
from model_conversion import model_convert


#------------------  步骤 1: 创建工作目录  ------------------

def create_work_directories(device_id: str, base_path: Optional[str] = None) -> Tuple[str, str, str]:
    """
    创建工作目录结构

    Args:
        device_id: 设备 ID（32位十六进制字符串）
        base_path: 基础路径，默认为 as_model_conversion 目录

    Returns:
        (device_work_dir, output_dir, spiffs_dl_dir) 三个目录路径
    """
    print("\n" + "=" * 60)
    print("  Step 1: Create Work Directories")
    print("=" * 60)

    # 确定基础路径（当前文件在 as_model_conversion 目录下）
    if base_path is None:
        base_path = os.path.dirname(__file__)

    # 创建 temp/{device_id}/ 目录结构
    device_work_dir = os.path.join(base_path, "temp", device_id)
    output_dir = os.path.join(device_work_dir, "output")
    spiffs_dl_dir = os.path.join(device_work_dir, "spiffs_dl")

    # 如果目录已存在，先删除（确保干净的工作环境）
    if os.path.exists(device_work_dir):
        print(f"Removing existing directory: {device_work_dir}")
        shutil.rmtree(device_work_dir)

    # 创建目录
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(spiffs_dl_dir, exist_ok=True)

    print(f"✓ Device work directory: {device_work_dir}")
    print(f"✓ Output directory: {output_dir}")
    print(f"✓ SPIFFS DL directory: {spiffs_dl_dir}")

    return device_work_dir, output_dir, spiffs_dl_dir


#------------------  步骤 2: 模型转换  ------------------

def convert_model(device_id: str, model_type: str, output_dir: str, base_path: Optional[str] = None) -> Optional[str]:
    """
    使用 model_convert 进行模型转换

    Args:
        device_id: 设备 ID
        model_type: 模型类型（如 "ped_alerm"）
        output_dir: 输出目录
        base_path: 基础路径

    Returns:
        转换后的文件路径，失败返回 None
    """
    print("\n" + "=" * 60)
    print("  Step 2: Model Conversion")
    print("=" * 60)

    # 确定基础路径（当前文件在 as_model_conversion 目录下）
    if base_path is None:
        base_path = os.path.dirname(__file__)

    # 构建模型文件路径：type_model/{model_type}/packerOut.zip
    packerOut_path = os.path.join(base_path, "type_model", model_type, "packerOut.zip")

    if not os.path.exists(packerOut_path):
        print(f"Error: packerOut.zip not found: {packerOut_path}")
        return None

    print(f"Model type: {model_type}")
    print(f"PackerOut path: {packerOut_path}")
    print(f"Output directory: {output_dir}")

    # 调用 model_convert 函数
    print("\n### Calling model_convert function...")
    converted_file = model_convert(device_id, packerOut_path, output_dir)

    if not converted_file:
        print("Error: Model conversion failed")
        return None

    print(f"\n✓ Model conversion successful!")
    print(f"✓ Output file: {converted_file}")

    return converted_file


#------------------  步骤 3: ZIP 解压缩  ------------------

def extract_zip_file(zip_file_path: str, device_work_dir: str) -> Optional[str]:
    """
    解压缩 ZIP 文件到 output 目录

    Args:
        zip_file_path: ZIP 文件路径
        device_work_dir: 设备工作目录

    Returns:
        解压后的目录路径，失败返回 None
    """
    print("\n" + "=" * 60)
    print("  Step 3: Extract ZIP File")
    print("=" * 60)

    # 解压目录：temp/{device_id}/output
    extract_dir = os.path.join(device_work_dir, "output")

    print(f"ZIP file: {zip_file_path}")
    print(f"Extract to: {extract_dir}")

    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        print(f"✓ Extracted successfully")

        # 查找解压后的实际内容目录（可能在子目录中）
        extracted_items = os.listdir(extract_dir)
        if len(extracted_items) == 1 and os.path.isdir(os.path.join(extract_dir, extracted_items[0])):
            # 如果解压后只有一个子目录，返回该子目录路径
            actual_extract_dir = os.path.join(extract_dir, extracted_items[0])
            print(f"✓ Actual content directory: {actual_extract_dir}")
            return actual_extract_dir
        else:
            # 否则返回 extract_dir
            return extract_dir

    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return None


#------------------  步骤 4: 复制烧录文件  ------------------

def copy_flash_files(extract_dir: str, model_type: str, spiffs_dl_dir: str, base_path: Optional[str] = None) -> bool:
    """
    复制烧录所需文件到 spiffs_dl 目录
    需要的文件：
    1. 解压后的 network.fpk
    2. type_model 目录下的 network_info.txt

    Args:
        extract_dir: 解压后的目录
        model_type: 模型类型
        spiffs_dl_dir: SPIFFS DL 目录
        base_path: 基础路径

    Returns:
        成功返回 True，失败返回 False
    """
    print("\n" + "=" * 60)
    print("  Step 4: Copy Flash Files")
    print("=" * 60)

    # 确定基础路径（当前文件在 as_model_conversion 目录下）
    if base_path is None:
        base_path = os.path.dirname(__file__)

    try:
        # 1. 查找并复制 network.fpk
        network_fpk_found = False
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.endswith('.fpk'):
                    source_fpk = os.path.join(root, file)
                    target_fpk = os.path.join(spiffs_dl_dir, file)
                    shutil.copy2(source_fpk, target_fpk)
                    print(f"✓ Copied {file}")
                    print(f"  From: {source_fpk}")
                    print(f"  To: {target_fpk}")
                    network_fpk_found = True
                    break
            if network_fpk_found:
                break

        if not network_fpk_found:
            print("Error: network.fpk not found in extracted files")
            return False

        # 2. 复制 network_info.txt
        network_info_source = os.path.join(base_path, "type_model", model_type, "network_info.txt")

        if not os.path.exists(network_info_source):
            print(f"Warning: network_info.txt not found: {network_info_source}")
            print("Checking if network_info.txt exists in extracted files...")

            # 尝试从解压文件中查找
            network_info_found = False
            for root, dirs, files in os.walk(extract_dir):
                if "network_info.txt" in files:
                    source_info = os.path.join(root, "network_info.txt")
                    target_info = os.path.join(spiffs_dl_dir, "network_info.txt")
                    shutil.copy2(source_info, target_info)
                    print(f"✓ Copied network_info.txt from extracted files")
                    print(f"  From: {source_info}")
                    print(f"  To: {target_info}")
                    network_info_found = True
                    break

            if not network_info_found:
                print("Error: network_info.txt not found anywhere")
                return False
        else:
            target_info = os.path.join(spiffs_dl_dir, "network_info.txt")
            shutil.copy2(network_info_source, target_info)
            print(f"✓ Copied network_info.txt")
            print(f"  From: {network_info_source}")
            print(f"  To: {target_info}")

        print(f"\n✓ All flash files copied successfully")
        return True

    except Exception as e:
        print(f"Error during file copy: {e}")
        import traceback
        traceback.print_exc()
        return False


#------------------  步骤 5: 组装 SPIFFS_DL 目录  ------------------

def assemble_spiffs_dl(spiffs_dl_dir: str) -> bool:
    """
    验证并组装 spiffs_dl 目录

    Args:
        spiffs_dl_dir: SPIFFS DL 目录路径

    Returns:
        成功返回 True，失败返回 False
    """
    print("\n" + "=" * 60)
    print("  Step 5: Assemble SPIFFS_DL Directory")
    print("=" * 60)

    # 检查必需文件
    required_files = []
    for file in os.listdir(spiffs_dl_dir):
        if file.endswith('.fpk') or file == 'network_info.txt':
            required_files.append(file)

    print(f"SPIFFS DL directory: {spiffs_dl_dir}")
    print(f"Files in directory:")
    for file in required_files:
        file_path = os.path.join(spiffs_dl_dir, file)
        file_size = os.path.getsize(file_path)
        print(f"  - {file} ({file_size} bytes)")

    # 验证必需文件
    has_fpk = any(f.endswith('.fpk') for f in required_files)
    has_network_info = 'network_info.txt' in required_files

    if not has_fpk:
        print("Error: No .fpk file found")
        return False

    if not has_network_info:
        print("Error: network_info.txt not found")
        return False

    print(f"\n✓ SPIFFS_DL directory assembled successfully")
    print(f"✓ Ready for flashing")

    return True


#------------------  核心函数：整合所有步骤  ------------------

def generate_model_by_device_id(
    device_id: str,
    model_type: str,
    base_path: Optional[str] = None
) -> Optional[str]:
    """
    根据传入的 device_id 和 model_type 生成模型文件

    【5步分层处理】
    1. 创建工作目录（temp/{device_id}/output 和 temp/{device_id}/spiffs_dl）
    2. 模型转换（调用 model_convert）
    3. ZIP 解压缩
    4. 复制烧录文件（network.fpk + network_info.txt）
    5. 组装 spiffs_dl 目录

    Args:
        device_id: 设备 ID（32位十六进制字符串）
        model_type: 模型类型（如 "ped_alerm"），对应 type_model 下的目录名
        base_path: 基础路径，默认为 as_model_conversion 目录

    Returns:
        生成的 spiffs_dl 目录路径，失败返回 None
    """
    print("\n" + "=" * 80)
    print("  Generate Model by Device ID - 5-Step Process")
    print("=" * 80)
    print(f"Device ID: {device_id}")
    print(f"Model Type: {model_type}")

    try:
        # 确定基础路径（当前文件在 as_model_conversion 目录下）
        if base_path is None:
            base_path = os.path.dirname(__file__)

        # 步骤 1: 创建工作目录
        device_work_dir, output_dir, spiffs_dl_dir = create_work_directories(device_id, base_path)

        # 步骤 2: 模型转换
        converted_file = convert_model(device_id, model_type, output_dir, base_path)
        if not converted_file:
            return None

        # 步骤 3: ZIP 解压缩
        extract_dir = extract_zip_file(converted_file, device_work_dir)
        if not extract_dir:
            return None

        # 步骤 4: 复制烧录文件
        if not copy_flash_files(extract_dir, model_type, spiffs_dl_dir, base_path):
            return None

        # 步骤 5: 组装 spiffs_dl 目录
        if not assemble_spiffs_dl(spiffs_dl_dir):
            return None

        # 返回 spiffs_dl 目录路径
        print("\n" + "=" * 80)
        print("  ✓ All Steps Completed Successfully")
        print("=" * 80)
        print(f"✓ SPIFFS DL directory: {spiffs_dl_dir}")

        return str(spiffs_dl_dir)

    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


#------------------  主函数  ------------------

def main():
    """主函数 - 用于测试"""
    if len(sys.argv) < 3:
        print("Usage: python as_model_auth.py <device_id> <model_type>")
        print("\nExample:")
        print("  python as_model_auth.py 100B50501A2101026964011000000000 ped_alerm")
        sys.exit(1)

    device_id_arg = sys.argv[1]
    model_type_arg = sys.argv[2]

    result = generate_model_by_device_id(device_id_arg, model_type_arg)

    if result:
        print(f"\n✓ Success! SPIFFS DL directory: {result}")
        sys.exit(0)
    else:
        print(f"\n✗ Failed to generate model")
        sys.exit(1)


if __name__ == "__main__":
    # 方式1：使用变量传参（直接运行时修改这里的变量）
    device_id = "100B50501A2101059064011000000000"
    model_type = "ped_alerm"

    # 调用主函数
    result = generate_model_by_device_id(device_id, model_type)

    if result:
        print(f"\n✓ Success! SPIFFS DL directory: {result}")
        sys.exit(0)
    else:
        print(f"\n✗ Failed to generate model")
        sys.exit(1)

    # 方式2：使用命令行参数（如果需要命令行调用，注释掉上面，取消下面的注释）
    # main()
