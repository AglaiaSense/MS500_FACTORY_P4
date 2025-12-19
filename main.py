import os
import sys
import subprocess
import time

# 导入 ESP 组件工具
from esp_components import get_esptool

# 导入 NVS 工具模块
from as_nvs import (
    read_flash_and_mac,
    check_nvs_data,
    generate_nvs_data,
    flash_nvs,
    init_temp_dir,
)

# ========== 配置区 ==========
# 使用 esp_components 提供的 esptool 路径
ESPTOOL = get_esptool()
PORT = "COM4"  # 修改为实际端口

# 临时文件目录
TEMP_DIR = "temp"

# NVS 分区配置
NVS_OFFSET = "0x9000"
NVS_SIZE = "0x10000"  # 64KB


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
    print("=" * 60)
    print("测试: 读取设备 MAC 地址")
    print("=" * 60)

    cmd = [ESPTOOL, "--port", port, "read_mac"]
    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

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
# 此功能已移至 as_nvs.read_flash_and_mac()


#------------------ 步骤3：调用服务器注册 ------------------

def request_server(mac):
    """
    调用 as_service_register.py 注册设备并获取设备信息
    """
    print("\n" + "=" * 60)
    print("步骤3: 向服务器注册设备")
    print("=" * 60)

    try:
        # 导入 as_service_register 模块
        import as_service_register

        # 调用注册函数
        result = as_service_register.main()

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
# 此功能已移至 as_nvs.flash_nvs()


#------------------ 主流程 ------------------

def main():
    """
    工厂生产流程主函数
    """


    print("=" * 60)
    print("  MS500-EP 工厂生产程序")
    print("=" * 60)

    try:
        # 步骤1：读取 MAC 和 NVS 数据
        mac = read_flash_and_mac(PORT)

        # 步骤2：检查 NVS 数据
        existing_info = check_nvs_data()

        if existing_info:
            response = input("\n是否继续重新注册? (y/n): ")
            if response.lower() != "y":
                print("操作已取消")
                return

        # 步骤3：向服务器注册设备
        device_info = request_server(mac)

        # 步骤4：生成 NVS 数据（CSV 和 BIN）
        generate_nvs_data(device_info)

        # 步骤5：烧录 NVS 数据
        flash_nvs(PORT)

        # 完成
        print("\n" + "=" * 60)
        print("  ✓ 生产流程完成")

    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 正常生产模式
    main()

    # 仅测试串口连接（取消下面注释使用）
    # PORT = "COM4"
    # test_read_mac(PORT)
