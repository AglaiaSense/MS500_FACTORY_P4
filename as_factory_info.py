import os
import sys
import subprocess
import time

# 导入 ESP 组件工具
from esp_components import get_esptool, run_command

# 导入 NVS 工具模块
from as_nvs_flash import (
    read_flash_and_mac,
    check_nvs_data,
    generate_nvs_data,
    flash_nvs,
    init_temp_dir,
)

# 导入配置模块
import as_ms500_config

# ========== 配置区 ==========
# 使用 esp_components 提供的 esptool 路径
ESPTOOL = get_esptool()

# 临时文件目录
TEMP_DIR = "temp"


#------------------ 临时文件清理 ------------------

def cleanup_temp_files():
    """
    清理所有临时文件
    """
    import shutil
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
            print(f"已删除临时目录: {TEMP_DIR}")
        except Exception as e:
            print(f"警告: 无法删除临时目录 {TEMP_DIR}: {e}")


#------------------ 测试串口连接 ------------------

def test_read_mac(port):
    """
    测试串口连接并读取 MAC 地址（仅用于测试）
    """
    print("-" * 60)
    print("测试: 读取设备 MAC 地址")
    print("-" * 60)

    cmd = [*ESPTOOL, "--port", port, "read_mac"]
    result = run_command(cmd)

    # 检查是否成功
    if result.returncode != 0:
        print("\n" + "!" * 60)
        print("错误: 无法连接到设备")
        print("!" * 60)
        print("\n请检查:")
        print("  1. 设备是否正确连接到 " + port)
        print("  2. COM 端口号是否正确")
        print("  3. 设备是否处于下载模式（Bootloader）")
        print("  4. 串口是否被其他程序占用")

        # 打印详细错误信息
        print("\n" + "-" * 60)
        print("详细错误信息:")
        print("-" * 60)

        # 打印标准输出（如果有）
        if result.stdout.strip():
            print(result.stdout)

        # 打印标准错误输出
        if result.stderr.strip():
            print(result.stderr)
        else:
            print("（无错误详情）")

        print("-" * 60)
        return None

    # 打印完整输出
    print(result.stdout)

    # 提取 MAC 地址
    mac = None
    for line in result.stdout.splitlines():
        if "MAC:" in line:
            mac = line.split("MAC:")[-1].strip()
            break

    if mac:
        print(f"\n✓ 成功读取 MAC 地址: {mac}")
    else:
        print("\n警告: 未找到 MAC 地址")

    return mac


#------------------ 步骤1：读取 MAC 和 NVS 数据 ------------------
# 此功能已移至 as_nvs_flash.read_flash_and_mac()


#------------------ 步骤3：调用服务器注册 ------------------

def request_server(mac, existing_info=None):
    """
    调用 as_dm_register.register_device() 注册设备并获取设备信息

    Args:
        mac: MAC 地址
        existing_info: 可选，从 NVS 读取的现有信息
    """
    print("\n" + "=" * 60)
    print("步骤3: 向服务器注册设备")
    print("-" * 60)

    try:
        # 从配置模块读取参数
        server_url = as_ms500_config.get_server_url()
        c_sn = as_ms500_config.get_c_sn()
        u_sn = as_ms500_config.get_u_sn()
        u_url = as_ms500_config.get_u_url()

        print(f"Reading parameters from configuration:")
        print(f"  server_url: {server_url}")
        print(f"  c_sn: {c_sn}")
        print(f"  u_sn: {u_sn}")
        print(f"  u_url: {u_url}")

        # 从 existing_info 中提取 g_camera_id
        g_camera_id = None
        if existing_info and existing_info.get("decoded") and existing_info.get("info"):
            g_camera_id = existing_info.get("info", {}).get("g_camera_id")
            if g_camera_id:
                print(f"从 NVS 中读取到 g_camera_id: {g_camera_id}")

        # 导入 as_dm_register 模块
        from as_dm_register import register_device

        # 调用注册函数，传入参数
        result = register_device(server_url, c_sn, u_sn, g_camera_id, u_url)

        if not result.get('success'):
            error_msg = result.get('error', 'Unknown error')
            raise RuntimeError(f"服务器注册失败: {error_msg}")

        print("✓ 设备注册成功!")

        # 返回统一格式的数据
        return {
            "c_sn": result.get('c_sn', ''),
            "u_sn": result.get('u_sn', ''),
            "device_token": result.get('device_token', ''),
            "u_camera_id": result.get('u_camera_id', 0),
            "u_unit_id": result.get('u_unit_id', 0),
            "u_account_id": result.get('u_account_id', 0),
            "password": result.get('password', ''),
            "u_url": result.get('u_url', ''),
            "server_url": result.get('server_url', ''),
            "mac": mac
        }

    except Exception as e:
        print(f"错误: 设备注册失败 - {e}")
        raise RuntimeError(f"无法注册设备: {e}")


#------------------ 步骤5：烧录 NVS 数据 ------------------
# 此功能已移至 as_nvs_flash.flash_nvs()


#------------------ 主流程 ------------------

def main(port, bin_type):
    """
    工厂生产流程主函数

    Args:
        port: 串口号（必需）
        bin_type: 固件类型（必需）
    """
    use_port = port
    use_bin_type = bin_type


    print("-" * 60)
    print("参数注册 开始")
    print(f"串口: {use_port}")
    print(f"固件类型: {use_bin_type}")
    print("-" * 60)

    try:
        # 步骤1：读取 MAC 和 NVS 数据
        mac = read_flash_and_mac(use_port, use_bin_type)

        # 步骤2：检查 NVS 数据
        existing_info = check_nvs_data()

        if existing_info:
            # 检查 g_camera_id 是否有效
            if existing_info.get("g_camera_id_valid"):
                print("\n✓ 设备已注册且 g_camera_id 有效")
                response = input("\n是否继续重新注册? (y/n): ")
                if response.lower() != "y":
                    print("操作已取消")
                    return
            else:
                # g_camera_id 无效，需要重新注册
                print("\n⚠ 设备已有 NVS 数据，但 g_camera_id 无效，需要先启动MS500设备进行camera_id的生成")
                return

        # 步骤3：向服务器注册设备
        # 传入 existing_info 以便从中提取 g_camera_id 用于 c_sensor 参数
        device_info = request_server(mac, existing_info=existing_info)

        # 步骤4：生成 NVS 数据（CSV 和 BIN）
        # 传入 existing_info 以保留原有参数（如 g_camera_id, wake_count 等）
        generate_nvs_data(device_info, existing_nvs=existing_info, bin_type=use_bin_type)

        # 步骤5：烧录 NVS 数据
        flash_nvs(use_port, use_bin_type)

        # 完成
        print("\n" + "=" * 60)
        print("  ✓ 参数注册 完成")

    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n错误: {e}")
        sys.exit(1)


if __name__ == "__main__":

    # 从配置文件读取参数
    PORT = as_ms500_config.get_port()
    BIN_TYPE = as_ms500_config.get_bin_type()

    # 执行主函数
    sys.exit(main(PORT, BIN_TYPE))

