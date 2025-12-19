#!/usr/bin/env python3
"""
MS500 AI 模型自动烧录工具（全新版本）

功能说明:
1. 使用 as_nvs_tool.py 获取 NVS 中的 u_camera_id 值
2. 调用 as_model_auth.py 的 generate_model_by_device_id() 函数生成模型 AI 文件
3. 使用 ESP-IDF 的 NVS 分区生成模块，将模型文件生成 bin
4. 将 bin 文件烧录到 storage_dl 分区
5. 如果烧录成功，在 NVS 中新增 is_model_update=1，生成新的 nvs.bin 并烧录
6. 更新成功后重启 ESP32

使用前准备:
1. 准备模型文件:
   - 在 model/ 目录下创建模型目录 (例如: model/person_alerm/)
   - 将 packerOut.zip 文件放入该目录
   - (可选) 如需替换 network_info.txt，也放入该目录

2. 配置文件:
   - 编辑 model/model_config.json 文件
   - 设置 model_dir (模型目录名，如 "person_alerm")
   - device_id 会自动从 NVS 中的 u_camera_id 获取

3. 设备连接:
   - 将 ESP32-P4 设备连接到电脑
   - 确认串口号 (默认 COM4，可在代码中修改 PORT 变量)
   - 确保设备处于可烧录状态

使用方法:
    cd pc_client/python_factory
    python as_model_flash.py
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path

# 导入 ESP 组件工具
from esp_components import (
    get_esp_idf_python,
    get_fatfs_gen_tool,
    get_esptool,
)

# 导入 as_nvs 模块
from as_nvs import (
    init_temp_dir as nvs_init_temp_dir,
    get_nvs_raw_bin_path,
    check_nvs_data,
    generate_nvs_data,
    get_nvs_bin_path,
)

# 导入 as_model_auth 模块（需要添加到路径）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "model"))
from as_model_auth import generate_model_by_device_id

# ========== 配置区 ==========
# 串口号
PORT = "COM4"

# 烧录波特率（提高波特率可加快烧录速度）
# 常用值：115200, 460800, 921600, 1500000
# 注意：更高的波特率需要硬件支持，如果出现错误可降低波特率
BAUD_RATE = "115200"

# 临时文件目录
TEMP_DIR = "temp"

# 分区配置 - storage_dl 分区
STORAGE_DL_OFFSET = "0x8A0000"  # storage_dl 分区偏移地址
STORAGE_DL_SIZE = "0x700000"  # 7MB

# 分区配置 - NVS 分区
NVS_OFFSET = "0x9000"  # NVS 分区偏移地址
NVS_SIZE = "0x10000"  # 64KB

# 模型配置文件路径
MODEL_CONFIG_FILE = os.path.join("model", "model_config.json")

# 使用 esp_components 提供的工具路径
ESP_IDF_PYTHON = get_esp_idf_python()
FATFS_GEN_TOOL = get_fatfs_gen_tool()
ESPTOOL = get_esptool()


# ------------------  初始化  ------------------

def init_temp_dir():
    """初始化临时目录"""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        print(f"Create temp directory: {os.path.abspath(TEMP_DIR)}")


def cleanup_temp_files():
    """清理所有临时文件"""
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
            print(f"Temp directory deleted: {TEMP_DIR}")
        except Exception as e:
            print(f"Warning: Cannot delete temp directory {TEMP_DIR}: {e}")


# ------------------  步骤1: 从 NVS 读取 device_id  ------------------

def read_device_id_from_nvs(port):
    """
    从设备的 NVS 中读取 g_camera_id 作为 device_id

    Args:
        port: 串口号

    Returns:
        device_id 字符串，失败返回 None
    """
    print("=" * 60)
    print("Step 1: Read device_id from NVS")
    print("=" * 60)

    try:
        # 步骤 1.1: 从设备读取 NVS 原始数据
        print("\nReading NVS partition from device...")
        nvs_raw_bin = get_nvs_raw_bin_path()

        cmd = [ESPTOOL, "--port", port, "read_flash", NVS_OFFSET, NVS_SIZE, nvs_raw_bin]
        print(f"Execute command: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("\nError: Failed to read NVS from device")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            raise RuntimeError("Failed to read NVS from device")

        print(f"✓ NVS partition read successfully: {nvs_raw_bin}")

        # 步骤 1.2: 解码 NVS 数据
        print("\nDecoding NVS data...")
        nvs_info = check_nvs_data()

        if not nvs_info or not nvs_info.get("decoded"):
            print("\nError: Cannot decode NVS data")
            return None

        # 步骤 1.3: 从 NVS 中提取 g_camera_id (字符串类型)
        info = nvs_info.get("info", {})
        g_camera_id = info.get("g_camera_id", "")

        if not g_camera_id:
            print("\nError: g_camera_id not found in NVS")
            print("Available keys:", list(info.keys()))
            return None

        print(f"\n✓ Found g_camera_id in NVS: {g_camera_id}")

        # g_camera_id 已经是字符串格式，可以直接使用作为 device_id
        # 格式示例: "100B50501A2101026964011000000000"
        device_id = g_camera_id
        print(f"✓ Device ID: {device_id}")
        return device_id

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return None


# ------------------  步骤2: 调用 as_model_auth.py 生成模型  ------------------

def generate_model_files(device_id):
    """
    调用 as_model_auth.py 生成 AI 模型文件

    Args:
        device_id: 设备ID

    Returns:
        生成的模型文件的 temp 目录路径，失败返回 None
    """
    print("\n" + "=" * 60)
    print("Step 2: Generate AI model files")
    print("=" * 60)

    try:
        # 调用 as_model_auth.py 的 generate_model_by_device_id 函数
        print(f"\nCalling generate_model_by_device_id(device_id={device_id})...")

        temp_dir = generate_model_by_device_id(
            device_id=device_id,
            config_file=MODEL_CONFIG_FILE
        )

        if not temp_dir:
            print("\nError: Model generation failed")
            return None

        print(f"\n✓ Model generated successfully!")
        print(f"Temp directory: {temp_dir}")

        return temp_dir

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return None


# ------------------  步骤3: 创建 storage_dl.bin  ------------------

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


# ------------------  步骤4: 烧录 storage_dl.bin  ------------------

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


# ------------------  步骤5: 更新 NVS 添加 is_model_update 参数  ------------------

def update_nvs_with_model_flag():
    """
    在 NVS 中添加 is_model_update=1 参数

    Returns:
        生成的新 NVS bin 文件路径，失败返回 None
    """
    print("\n" + "=" * 60)
    print("Step 5: Update NVS with is_model_update flag")
    print("=" * 60)

    try:
        # 读取现有的 NVS 数据
        print("\nReading existing NVS data...")
        nvs_info = check_nvs_data()

        if not nvs_info or not nvs_info.get("decoded"):
            print("\nError: Cannot decode NVS data")
            return None

        # 获取现有信息
        info = nvs_info.get("info", {})
        print(f"\nExisting NVS info:")
        for key, value in info.items():
            print(f"  {key}: {value}")

        # 添加 is_model_update 参数
        info["is_model_update"] = "1"
        print(f"\n✓ Added is_model_update=1")

        # 生成新的 NVS bin 文件
        print("\nGenerating new NVS bin file...")
        generate_nvs_data(info)

        # 获取生成的 NVS bin 文件路径
        nvs_bin_path = get_nvs_bin_path()

        if not os.path.exists(nvs_bin_path):
            print(f"\nError: NVS bin file not found: {nvs_bin_path}")
            return None

        print(f"✓ New NVS bin file generated: {nvs_bin_path}")
        return nvs_bin_path

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return None


# ------------------  步骤6: 烧录新的 NVS bin 文件  ------------------

def flash_nvs_bin(port, nvs_bin):
    """
    烧录新的 NVS bin 文件到 Flash

    Args:
        port: 串口号
        nvs_bin: NVS bin 文件路径

    Returns:
        烧录是否成功
    """
    print("\n" + "=" * 60)
    print("Step 6: Flash new NVS bin to Flash")
    print("=" * 60)

    try:
        cmd = [ESPTOOL, "--port", port, "--baud", BAUD_RATE, "write_flash", NVS_OFFSET, nvs_bin]
        print(f"Execute command: {' '.join(cmd)}")
        print(f"Using baud rate: {BAUD_RATE}")
        print("Flashing NVS...\n")

        # 不捕获输出，让 esptool 的进度信息实时显示
        result = subprocess.run(cmd)

        if result.returncode != 0:
            print("\nError: Failed to flash NVS bin")
            return False

        print("\n✓ NVS bin flashed successfully!")
        return True

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


# ------------------  步骤7: 重启 ESP32  ------------------

def reset_esp32(port):
    """
    重启 ESP32 设备

    Args:
        port: 串口号

    Returns:
        重启是否成功
    """
    print("\n" + "=" * 60)
    print("Step 7: Reset ESP32")
    print("=" * 60)

    try:
        # 使用 esptool 的 run 命令重启设备
        cmd = [ESPTOOL, "--port", port, "run"]
        print(f"Execute command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            print("\nWarning: Reset command returned non-zero exit code")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            # 即使返回错误，设备可能已经重启
            print("Device may have been reset anyway")

        print("✓ ESP32 reset command sent")
        return True

    except subprocess.TimeoutExpired:
        print("Reset command timed out (expected behavior)")
        print("✓ ESP32 reset command sent")
        return True
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


# ------------------  主流程  ------------------

def main():
    """主函数 - 完整的 AI 模型自动烧录流程"""

    print("=" * 60)
    print("  MS500 AI Model Auto Flash Tool")
    print("=" * 60)

    try:
        # 初始化临时目录
        nvs_init_temp_dir()
        init_temp_dir()

        # 步骤1: 从 NVS 读取 device_id (u_camera_id)
        device_id = read_device_id_from_nvs(PORT)
        if not device_id:
            print("\n✗ Failed to read device_id from NVS")
            return 1

        # 步骤2: 调用 as_model_auth.py 生成模型
        model_temp_dir = generate_model_files(device_id)
        if not model_temp_dir:
            print("\n✗ Failed to generate model files")
            return 1

        # 步骤3: 创建 storage_dl.bin
        storage_dl_bin = create_storage_dl_bin(model_temp_dir)
        if not storage_dl_bin:
            print("\n✗ Failed to create storage_dl.bin")
            return 1

        # 步骤4: 烧录 storage_dl.bin
        if not flash_storage_dl_bin(PORT, storage_dl_bin):
            print("\n✗ Failed to flash storage_dl.bin")
            return 1

        # 步骤5: 更新 NVS，添加 is_model_update=1
        nvs_bin = update_nvs_with_model_flag()
        if not nvs_bin:
            print("\n✗ Failed to update NVS with is_model_update flag")
            return 1

        # 步骤6: 烧录新的 NVS bin
        if not flash_nvs_bin(PORT, nvs_bin):
            print("\n✗ Failed to flash new NVS bin")
            return 1

        # 步骤7: 重启 ESP32
        if not reset_esp32(PORT):
            print("\n✗ Failed to reset ESP32")
            return 1

        # 完成
        print("\n" + "=" * 60)
        print("  ✓ AI Model Auto Flash Completed Successfully")
        print("=" * 60)
        print(f"Device ID: {device_id}")
        print(f"Model temp dir: {model_temp_dir}")
        print(f"Storage DL partition: {STORAGE_DL_OFFSET}")
        print(f"NVS partition: {NVS_OFFSET}")
        print(f"is_model_update: 1")
        print("\nDevice has been reset. Model update will be processed on startup.")
        print("Check app_update_dnn_use_sd_usb() function for update logic.")

        return 0

    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
