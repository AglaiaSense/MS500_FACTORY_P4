import os
import sys
import subprocess

# 导入 ESP 组件工具
from esp_components import (
    get_esp_idf_python,
    get_nvs_tool_path,
    get_nvs_gen_module,
)

# ========== 配置区 ==========
# 使用 esp_components 提供的工具路径
ESP_IDF_PYTHON = get_esp_idf_python()
NVS_TOOL_PATH = get_nvs_tool_path()
NVS_GEN_MODULE = get_nvs_gen_module()

# 临时文件目录
TEMP_DIR = "temp"

# 临时文件路径
NVS_RAW_BIN = os.path.join(TEMP_DIR, "ms500_nvs.bin")
DECODED_CSV = os.path.join(TEMP_DIR, "factory_decoded.csv")
FACTORY_CSV = os.path.join(TEMP_DIR, "factory_data.csv")
FACTORY_BIN = os.path.join(TEMP_DIR, "factory_nvs.bin")

# NVS 分区配置
NVS_OFFSET = "0x9000"
NVS_SIZE = "0x10000"  # 64KB


#------------------ 初始化临时目录 ------------------

def init_temp_dir():
    """
    初始化临时文件目录
    """
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        # print(f"创建临时目录: {os.path.abspath(TEMP_DIR)}")


#------------------ NVS 数据格式转换 ------------------

def convert_to_csv(nvs_output, output_file):
    """
    将 nvs_tool.py 的输出转换为 CSV 格式
    """
    print(f"  转换为 CSV 格式: {output_file}")

    # 解析 nvs_tool.py 的 minimal 输出
    # 格式: namespace:key = value
    entries = []
    current_namespace = None

    for line in nvs_output.splitlines():
        line = line.strip()

        if not line or line.startswith("Page"):
            continue

        # 解析 namespace:key = value 格式
        if " = " in line:
            key_part, value_part = line.split(" = ", 1)

            if ":" in key_part:
                namespace, key = key_part.split(":", 1)
                namespace = namespace.strip()
                key = key.strip()

                # 解析值
                value = value_part.strip()

                # 处理字节字符串 b'...'
                if value.startswith("b'") and value.endswith("'"):
                    value = value[2:-1]  # 移除 b' 和 '
                    # 移除末尾的 \x00
                    value = value.replace("\\x00", "")

                # 推断类型
                data_type = "string"
                if value.isdigit():
                    data_type = "u32"

                entries.append({
                    "namespace": namespace,
                    "key": key,
                    "type": data_type,
                    "value": value
                })

    # 写入 CSV 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("key,type,encoding,value\n")

        current_ns = None
        for entry in entries:
            # 写入 namespace 行
            if entry["namespace"] != current_ns:
                current_ns = entry["namespace"]
                f.write(f"{current_ns},namespace,,\n")

            # 写入数据行
            f.write(f"{entry['key']},data,{entry['type']},{entry['value']}\n")

    print(f"  CSV 文件已保存: {os.path.abspath(output_file)}")


#------------------ 步骤2：检查 NVS 数据 ------------------

def check_nvs_data():
    """
    检查并解码 NVS 数据，判断设备是否已有注册信息
    """
    print("\n" + "=" * 60)
    print("步骤2: 检查并解码 NVS 数据")
    print("=" * 60)

    # 检查 NVS raw 文件是否存在
    full_path = os.path.abspath(NVS_RAW_BIN)
    if not os.path.exists(NVS_RAW_BIN):
        print(f"错误: NVS raw 文件不存在")
        print(f"  查找路径: {full_path}")
        return None

    # print(f"  NVS 文件路径: {full_path}")
    file_size = os.path.getsize(NVS_RAW_BIN)
    print(f"  文件大小: {file_size} 字节")

    # 读取文件的前 256 字节，快速检查 NVS 分区状态
    with open(NVS_RAW_BIN, 'rb') as f:
        first_bytes = f.read(256)

    # 检查是否是空白分区（全是 0xFF）
    if all(b == 0xFF for b in first_bytes):
        print("  检测到: NVS 分区为空白（全是 0xFF）")
        print("  ✓ 设备未注册，可以写入新数据")
        return None

    # NVS 分区有数据，尝试解码
    print("  检测到: NVS 分区有数据")

    # 检查官方工具是否存在
    if not os.path.exists(NVS_TOOL_PATH):
        print(f"\n  错误: 找不到官方 nvs_tool.py")
        print(f"  查找路径: {NVS_TOOL_PATH}")
        return {"has_data": True, "decoded": False}

    # 使用官方 nvs_tool.py 解析（minimal 格式）
    print("\n  尝试解码 NVS 数据...")
    cmd = [ESP_IDF_PYTHON, NVS_TOOL_PATH, NVS_RAW_BIN, "-d", "minimal"]
    print(f"  执行命令: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("  警告: 无法解码 NVS 数据")
        print(f"  错误信息: {result.stderr if result.stderr else result.stdout}")
        print("\n  可能原因:")
        print("    1. NVS 分区数据损坏")
        print("    2. NVS 分区格式不兼容")
        print("    3. 分区数据被加密")
        return {"has_data": True, "decoded": False}

    # 解码成功，打印原始输出
    print("  ✓ NVS 数据解码成功!")

    print("\n" + "-" * 60)
    print("  NVS 数据内容:")
    print("-" * 60)
    if result.stdout.strip():
        print(result.stdout)
    print("-" * 60)

    # 转换为 CSV 格式
    try:
        convert_to_csv(result.stdout, DECODED_CSV)
    except Exception as e:
        print(f"  警告: 转换 CSV 失败: {e}")
        return {"has_data": True, "decoded": False}

    # 解析 CSV，提取关键信息
    nvs_info = {}
    if os.path.exists(DECODED_CSV):
        try:
            with open(DECODED_CSV, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[1:]:  # 跳过标题行
                    parts = line.strip().split(',')
                    if len(parts) >= 4:
                        key = parts[0]
                        value = parts[3] if len(parts) > 3 else ''
                        if key and key != 'factory':  # 跳过 namespace
                            nvs_info[key] = value
        except Exception as e:
            print(f"  解析 CSV 失败: {e}")

    if nvs_info:
        print("\n  设备已注册信息:")
        for key, value in nvs_info.items():
            print(f"    {key}: {value}")

        return {
            "has_data": True,
            "decoded": True,
            "info": nvs_info
        }
    else:
        print("  警告: 未提取到有效数据")
        return {"has_data": True, "decoded": False}


#------------------ 步骤4合并：生成 NVS 数据 ,生成NVS BIN 文件 ------------------

def generate_nvs_data(info):
    """
    生成 NVS CSV 和 BIN 文件（合并步骤4和步骤5）
    支持动态写入所有参数，不再限制固定字段
    """
    print("\n" + "=" * 60)
    print("步骤4: 生成 NVS 数据（CSV 和 BIN）")
    print("=" * 60)

    # 生成 CSV 文件
    print("\n生成 NVS CSV 文件...")
    with open(FACTORY_CSV, "w", encoding='utf-8') as f:
        f.write("key,type,encoding,value\n")
        f.write("factory,namespace,,\n")

        # 动态写入所有参数
        # 自动推断类型：数字类型使用 u32，字符串类型使用 string
        for key, value in info.items():
            # 推断类型
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                data_type = "u32"
                value_str = str(value)
            else:
                data_type = "string"
                value_str = str(value)

            f.write(f"{key},data,{data_type},{value_str}\n")

    print(f"✓ CSV 文件已生成: {FACTORY_CSV}")

    # 打印 CSV 文件内容
    print(f"\nCSV 文件路径: {os.path.abspath(FACTORY_CSV)}")
    print("CSV 文件内容:")
    print("-" * 40)
    try:
        with open(FACTORY_CSV, 'r', encoding='utf-8') as f:
            csv_content = f.read()
            print(csv_content)
    except Exception as e:
        print(f"无法读取 CSV 文件: {e}")
    print("-" * 40)

    # 生成 NVS BIN 文件
    print("\n生成 NVS BIN 文件...")

    # 使用 ESP-IDF 的 NVS 分区生成模块
    cmd = [ESP_IDF_PYTHON, "-m", NVS_GEN_MODULE, "generate", FACTORY_CSV, FACTORY_BIN, NVS_SIZE]
    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    # 打印返回码
    print(f"命令返回码: {result.returncode}")

    if result.returncode != 0:
        print("\n" + "!" * 60)
        print("错误: 生成 NVS BIN 失败")
        print("!" * 60)

        # 打印详细错误信息
        print("\n" + "-" * 60)
        print("详细错误信息:")
        print("-" * 60)

        print("STDOUT:")
        if result.stdout.strip():
            print(result.stdout)
        else:
            print("（stdout 为空）")

        print("\nSTDERR:")
        if result.stderr.strip():
            print(result.stderr)
        else:
            print("（stderr 为空）")

        print("-" * 60)
        raise RuntimeError("生成 NVS 分区失败")

    print(f"✓ NVS BIN 文件已生成: {FACTORY_BIN}")
    print(f"  文件路径: {os.path.abspath(FACTORY_BIN)}")

    # 验证文件是否真的生成
    if os.path.exists(FACTORY_BIN):
        file_size = os.path.getsize(FACTORY_BIN)
        print(f"  文件大小: {file_size} 字节")


#------------------ 获取 NVS BIN 文件路径 ------------------

def get_nvs_bin_path():
    """
    获取生成的 NVS BIN 文件路径
    """
    return FACTORY_BIN


def get_nvs_raw_bin_path():
    """
    获取 NVS 原始 BIN 文件路径
    """
    return NVS_RAW_BIN
