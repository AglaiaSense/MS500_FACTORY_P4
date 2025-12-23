#!/usr/bin/env python3
"""
模型烧录模块
功能：创建 storage_dl.bin 并烧录到设备
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# 导入 ESP 组件工具
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from esp_components import (
    get_esp_idf_python,
    get_fatfs_gen_tool,
    get_esptool,
)


#------------------  配置区  ------------------

# 烧录波特率
BAUD_RATE = "115200"

# 临时文件目录
TEMP_DIR = "temp"

# 分区配置 - storage_dl 分区
STORAGE_DL_OFFSET = "0x8A0000"  # storage_dl 分区偏移地址
STORAGE_DL_SIZE = "0x700000"  # 7MB

# 使用 esp_components 提供的工具路径
ESP_IDF_PYTHON = get_esp_idf_python()
FATFS_GEN_TOOL = get_fatfs_gen_tool()
ESPTOOL = get_esptool()


#------------------  初始化  ------------------

def init_temp_dir():
    """初始化临时目录"""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        print(f"Create temp directory: {os.path.abspath(TEMP_DIR)}")


#------------------  步骤3: 创建 storage_dl.bin  ------------------

def create_storage_dl_bin(model_temp_dir):
    """
    创建 storage_dl.bin 文件（FAT 文件系统镜像）

    Args:
        model_temp_dir: 模型文件解压后的 temp 目录

    Returns:
        生成的 storage_dl.bin 文件路径，失败返回 None
    """
    print("\n" + "=" * 60)
    print("Step 3: Create storage_dl.bin")
    print("=" * 60)

    try:
        # 查找 temp 目录下的所有文件
        temp_path = Path(model_temp_dir)
        if not temp_path.exists():
            print(f"\nError: Temp directory not found: {model_temp_dir}")
            return None

        print(f"\nScanning temp directory: {model_temp_dir}")

        # 创建临时目录用于存放模型文件
        storage_dir = os.path.join(TEMP_DIR, "storage_dl_content")
        if os.path.exists(storage_dir):
            shutil.rmtree(storage_dir)
        os.makedirs(storage_dir, exist_ok=True)

        # 复制 temp 目录下的所有文件到 storage_dir/dnn/ 目录
        # 目标结构: storage_dl_content/dnn/文件
        # 原因: FAT 文件系统使用 8.3 格式，目录名 "dnn" 符合限制（3字符）

        # 创建 dnn 子目录
        dnn_dir = os.path.join(storage_dir, "dnn")
        os.makedirs(dnn_dir, exist_ok=True)

        copied_count = 0
        for item in temp_path.rglob("*"):
            if item.is_file():
                filename = item.name
                dest_path = os.path.join(dnn_dir, filename)

                # 如果文件名已存在，添加后缀避免冲突
                if os.path.exists(dest_path):
                    counter = 1
                    base_name = item.stem
                    extension = item.suffix
                    while os.path.exists(dest_path):
                        new_name = f"{base_name}_{counter}{extension}"
                        dest_path = os.path.join(dnn_dir, new_name)
                        counter += 1
                    filename = os.path.basename(dest_path)

                # 复制文件
                shutil.copy2(item, dest_path)
                print(f"  Copied: {item.name} -> dnn/{filename}")
                copied_count += 1

        if copied_count == 0:
            print("\nError: No files found in temp directory")
            return None

        print(f"\n✓ Total {copied_count} files copied to {storage_dir}")

        # 生成 storage_dl.bin 文件
        storage_dl_bin = os.path.join(TEMP_DIR, "storage_dl.bin")

        # 检查 FATFS 生成工具是否存在
        if not os.path.exists(FATFS_GEN_TOOL):
            print(f"\nError: FATFS generation tool not found: {FATFS_GEN_TOOL}")
            raise RuntimeError("FATFS generation tool not found")

        # 使用 wl_fatfsgen.py 生成 FAT 镜像
        # 注意：使用 --long_name_support 启用长文件名支持（LFN）
        # 这样可以支持 network_info.txt 等超过 8.3 格式的文件名
        cmd = [
            ESP_IDF_PYTHON,
            FATFS_GEN_TOOL,
            storage_dir,  # 输入目录
            "--output_file", storage_dl_bin,  # 输出文件
            "--partition_size", STORAGE_DL_SIZE,  # 分区大小
            "--long_name_support",  # 启用长文件名支持
        ]

        print(f"\nExecute command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("\nError: Failed to generate storage_dl.bin")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            raise RuntimeError("Failed to generate storage_dl.bin")

        print(f"✓ storage_dl.bin generated: {storage_dl_bin}")

        # 验证文件
        if os.path.exists(storage_dl_bin):
            file_size = os.path.getsize(storage_dl_bin)
            print(f"  File size: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
        else:
            raise RuntimeError("storage_dl.bin file not generated")

        return storage_dl_bin

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return None


#------------------  步骤4: 烧录 storage_dl.bin  ------------------

def flash_storage_dl_bin(port, storage_dl_bin):
    """
    烧录 storage_dl.bin 到 Flash 指定分区

    Args:
        port: 串口号
        storage_dl_bin: storage_dl.bin 文件路径

    Returns:
        烧录是否成功
    """
    print("\n" + "=" * 60)
    print("Step 4: Flash storage_dl.bin to Flash")
    print("=" * 60)

    try:
        cmd = [ESPTOOL, "--port", port, "--baud", BAUD_RATE, "write_flash", STORAGE_DL_OFFSET, storage_dl_bin]
        print(f"Execute command: {' '.join(cmd)}")
        print(f"Using baud rate: {BAUD_RATE}")
        print("Flashing... (this may take a while)\n")

        # 不捕获输出，让 esptool 的进度信息实时显示
        result = subprocess.run(cmd)

        if result.returncode != 0:
            print("\nError: Failed to flash storage_dl.bin")
            return False

        print("\n✓ storage_dl.bin flashed successfully!")
        return True

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


#------------------  主函数  ------------------

def main(port, model_temp_dir):
    """
    主函数 - 创建并烧录 storage_dl.bin

    Args:
        port: 串口号
        model_temp_dir: 模型文件 temp 目录

    Returns:
        成功返回 True，失败返回 False
    """
    try:
        # 初始化临时目录
        init_temp_dir()

        # 步骤3: 创建 storage_dl.bin
        storage_dl_bin = create_storage_dl_bin(model_temp_dir)
        if not storage_dl_bin:
            print("\n✗ Failed to create storage_dl.bin")
            return False

        # 步骤4: 烧录 storage_dl.bin
        if not flash_storage_dl_bin(port, storage_dl_bin):
            print("\n✗ Failed to flash storage_dl.bin")
            return False

        print("\n✓ Model flash completed successfully")
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
    # 示例：从命令行参数获取串口号和模型 temp 目录
    # 用法: python as_model_flash.py <port> <model_temp_dir>
    if len(sys.argv) < 3:
        print("Usage: python as_model_flash.py <port> <model_temp_dir>")
        print("\nExample:")
        print("  python as_model_flash.py COM4 temp/ped_alerm")
        sys.exit(1)

    port_arg = sys.argv[1]
    model_temp_dir_arg = sys.argv[2]

    result = main(port_arg, model_temp_dir_arg)
    sys.exit(0 if result else 1)
