#!/usr/bin/env python3
"""
模型烧录模块
功能：使用 spiffs_dl 目录创建 storage_dl.bin 并烧录到设备
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# 导入 ESP 组件工具
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from esp_components import (
    get_esp_idf_python,
    get_fatfs_gen_tool,
    get_esptool,
    get_baud_rate,
    run_command,
)

# 导入分区工具
from as_flash_firmware import get_storage_dl_info


#------------------  配置区  ------------------

# 临时文件目录
TEMP_DIR = "temp"

# 使用 esp_components 提供的工具路径
ESP_IDF_PYTHON = get_esp_idf_python()
FATFS_GEN_TOOL = get_fatfs_gen_tool()
ESPTOOL = get_esptool()
BAUD_RATE = get_baud_rate()


#------------------  初始化  ------------------

def init_temp_dir():
    """初始化临时目录"""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        print(f"创建临时目录: {os.path.abspath(TEMP_DIR)}")


#------------------  步骤3: 创建 storage_dl.bin  ------------------

def create_storage_dl_bin(spiffs_dl_dir, bin_type):
    """
    使用 spiffs_dl 目录创建 storage_dl.bin 文件（FAT 文件系统镜像）

    参数:
        spiffs_dl_dir: spiffs_dl 目录路径（包含 network.fpk 和 network_info.txt）
        bin_type: 固件类型（用于获取分区信息）

    返回:
        生成的 storage_dl.bin 文件路径，失败返回 None
    """
    print("\n" + "=" * 60)
    print("步骤 3: 创建 storage_dl.bin")
    print("-" * 60)

    try:
        # 获取 storage_dl 分区信息
        storage_dl_info = get_storage_dl_info(bin_type)
        if not storage_dl_info:
            raise RuntimeError(f"Failed to get storage_dl partition info for bin_type: {bin_type}")

        storage_dl_size = storage_dl_info["size"]
        print(f"\nstorage_dl partition size (from {bin_type}): {storage_dl_size}")
        # 验证 spiffs_dl 目录存在
        if not os.path.exists(spiffs_dl_dir):
            print(f"\n错误: spiffs_dl 目录未找到: {spiffs_dl_dir}")
            return None

        print(f"\nspiffs_dl 目录: {spiffs_dl_dir}")

        # 创建 FAT 文件系统目录结构
        # 目标结构: storage_dl_content/dnn/文件
        storage_dir = os.path.join(TEMP_DIR, "storage_dl_content")
        if os.path.exists(storage_dir):
            shutil.rmtree(storage_dir)
        os.makedirs(storage_dir, exist_ok=True)

        # 创建 dnn 子目录
        dnn_dir = os.path.join(storage_dir, "dnn")
        os.makedirs(dnn_dir, exist_ok=True)

        # 复制 spiffs_dl 目录下的所有文件到 dnn 目录
        copied_count = 0
        for item in Path(spiffs_dl_dir).iterdir():
            if item.is_file():
                dest_path = os.path.join(dnn_dir, item.name)
                shutil.copy2(item, dest_path)
                print(f"  已复制: {item.name} -> dnn/{item.name}")
                copied_count += 1

        if copied_count == 0:
            print("\n错误: spiffs_dl 目录中没有文件")
            return None

        print(f"\n✓ 共 {copied_count} 个文件复制到 {storage_dir}")

        # 生成 storage_dl.bin 文件
        storage_dl_bin = os.path.join(TEMP_DIR, "storage_dl.bin")

        # 检查 FATFS 生成工具是否存在
        if not os.path.exists(FATFS_GEN_TOOL):
            print(f"\n错误: FATFS 生成工具未找到: {FATFS_GEN_TOOL}")
            raise RuntimeError("FATFS 生成工具未找到")

        # 使用 wl_fatfsgen.py 生成 FAT 镜像
        # 注意：使用 --long_name_support 启用长文件名支持（LFN）
        # 这样可以支持 network_info.txt 等超过 8.3 格式的文件名
        cmd = [
            ESP_IDF_PYTHON,
            FATFS_GEN_TOOL,
            storage_dir,  # 输入目录
            "--output_file", storage_dl_bin,  # 输出文件
            "--partition_size", storage_dl_size,  # 分区大小（从分区表获取）
            "--long_name_support",  # 启用长文件名支持
        ]

        result = run_command(cmd)

        if result.returncode != 0:
            print("\n错误: 生成 storage_dl.bin 失败")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            raise RuntimeError("生成 storage_dl.bin 失败")

        print(f"✓ storage_dl.bin 已生成: {storage_dl_bin}")

        # 验证文件
        if os.path.exists(storage_dl_bin):
            file_size = os.path.getsize(storage_dl_bin)
            print(f"  文件大小: {file_size} 字节 ({file_size / 1024 / 1024:.2f} MB)")
        else:
            raise RuntimeError("storage_dl.bin 文件未生成")

        return storage_dl_bin

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return None


#------------------  步骤4: 烧录 storage_dl.bin  ------------------

def flash_storage_dl_bin(port, storage_dl_bin, bin_type):
    """
    烧录 storage_dl.bin 到 Flash 指定分区

    参数:
        port: 串口号
        storage_dl_bin: storage_dl.bin 文件路径
        bin_type: 固件类型（用于获取分区信息）

    返回:
        烧录是否成功
    """
    print("\n" + "=" * 60)
    print("步骤 4: 烧录 storage_dl.bin 到 Flash")
    print("-" * 60)

    try:
        # 获取 storage_dl 分区信息
        storage_dl_info = get_storage_dl_info(bin_type)
        if not storage_dl_info:
            raise RuntimeError(f"Failed to get storage_dl partition info for bin_type: {bin_type}")

        storage_dl_offset = storage_dl_info["offset"]
        print(f"\nstorage_dl partition offset (from {bin_type}): {storage_dl_offset}")

        cmd = [*ESPTOOL, "--port", port, "--baud", BAUD_RATE, "write_flash", storage_dl_offset, storage_dl_bin]
        print(f"使用波特率: {BAUD_RATE}")
        print("正在烧录... (可能需要一段时间)\n")

        # 不捕获输出，让 esptool 的进度信息实时显示
        result = run_command(cmd, print_cmd=False, realtime_output=True)

        if result.returncode != 0:
            print("\n错误: 烧录 storage_dl.bin 失败")
            return False

        print("\n✓ storage_dl.bin 烧录成功!")
        return True

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False


#------------------  主函数  ------------------

def main(port, spiffs_dl_dir, bin_type):
    """
    主函数 - 创建并烧录 storage_dl.bin

    参数:
        port: 串口号
        spiffs_dl_dir: spiffs_dl 目录路径
        bin_type: 固件类型（用于获取分区信息）

    返回:
        成功返回 True，失败返回 False
    """
    try:
        # 初始化临时目录
        init_temp_dir()

        # 步骤3: 创建 storage_dl.bin
        storage_dl_bin = create_storage_dl_bin(spiffs_dl_dir, bin_type)
        if not storage_dl_bin:
            print("\n✗ 创建 storage_dl.bin 失败")
            return False

        # 步骤4: 烧录 storage_dl.bin
        if not flash_storage_dl_bin(port, storage_dl_bin, bin_type):
            print("\n✗ 烧录 storage_dl.bin 失败")
            return False

        print("\n✓ 模型烧录完成")
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
    # 方式1：使用变量传参（直接运行时修改这里的变量）
    port = "COM4"
    spiffs_dl_dir = "as_model_conversion/temp/100B50501A2101059064011000000000/spiffs_dl"
    bin_type = "sdk_uvc_tw_plate"  # 固件类型

    result = main(port, spiffs_dl_dir, bin_type)
    sys.exit(0 if result else 1)

    # 方式2：使用命令行参数（如果需要命令行调用，注释掉上面，取消下面的注释）
    # if len(sys.argv) < 4:
    #     print("使用方法: python as_model_flash.py <port> <spiffs_dl_dir> <bin_type>")
    #     print("\n示例:")
    #     print("  python as_model_flash.py COM4 as_model_conversion/temp/xxx/spiffs_dl sdk_uvc_tw_plate")
    #     sys.exit(1)
    #
    # port_arg = sys.argv[1]
    # spiffs_dl_dir_arg = sys.argv[2]
    # bin_type_arg = sys.argv[3]
    #
    # result = main(port_arg, spiffs_dl_dir_arg, bin_type_arg)
    # sys.exit(0 if result else 1)
