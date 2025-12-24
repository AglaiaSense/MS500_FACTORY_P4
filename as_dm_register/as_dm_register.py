#!/usr/bin/env python3
"""
MS500 DM Register Script

专门用于注册设备的独立服务脚本
使用 as_dm_api 模块进行服务器通信

注册步骤:
1. 参数检测和打印
2. 查询摄像头是否已注册（如果已注册则提示并退出）
3. 创建摄像头
4. 创建 Unit
5. 创建账户
6. 使用用户名/密码获取设备 token
7. 保存结果到响应配置文件

Usage:
    python as_dm_register.py
    或者从外部调用:
    from as_dm_register import register_device
    result = register_device(server_url, c_sn, u_sn, g_camera_id, u_url)
"""

import json
import os
import sys

# 导入 as_dm_api 模块
from .as_dm_api import (
    StreamingEndpoint,
    ADMIN_TOKEN,
    DEFAULT_TIMEOUT,
    query_camera,
    create_camera,
    create_unit,
    create_account,
    get_device_token
)

# ------------------ 配置文件路径 ------------------

# 配置文件路径（当前目录下的 as_request.json 和 as_respond.json）
REQUEST_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'as_request.json')
RESPOND_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'as_respond.json')


# ------------------ 辅助函数 ------------------

def create_error_result(message="Registration failed"):
    """创建错误返回结果"""
    return {
        'success': False,
        'error': message,
        'c_sn': '',
        'u_sn': '',
        'device_token': '',
        'u_camera_id': 0,
        'u_unit_id': 0,
        'u_account_id': 0,
        'password': '',
        'u_url': '',
        'server_url': ''
    }


def print_parameters(server_url, c_sn, u_sn, g_camera_id=None, u_url=''):
    """打印并检测参数

    Args:
        server_url: 服务器地址
        c_sn: 摄像头序列号
        u_sn: Unit序列号
        g_camera_id: 全局摄像头ID（可选）
        u_url: Unit URL（可选）

    Returns:
        bool: 参数是否有效
    """
    print("\n" + "-"*70)
    print("Parameter Check")
    print("-" * 60)
    print(f"Server URL    : {server_url}")
    print(f"Camera SN     : {c_sn}")
    print(f"Unit SN       : {u_sn}")
    print(f"Global Camera ID : {g_camera_id if g_camera_id else 'Not provided'}")
    print(f"Unit URL      : {u_url if u_url else 'Not provided'}")
    print("-" * 60)

    # 检查必需参数
    if not server_url:
        print("ERROR: server_url is required")
        return False

    if not c_sn:
        print("ERROR: c_sn is required")
        return False

    if not u_sn:
        print("ERROR: u_sn is required")
        return False

    print("All required parameters are valid")
    return True


def check_camera_registered(api: StreamingEndpoint, c_sn: str):
    """查询摄像头是否已注册

    Args:
        api: StreamingEndpoint API连接实例
        c_sn: 摄像头序列号

    Returns:
        tuple: (is_registered: bool, camera_id: int, message: str)
    """
    print("\n" + "-"*70)
    print("Step 1: Check if Camera is Already Registered")
    print("-" * 60)

    success, camera_id, message = query_camera(api, c_sn)

    if not success:
        print(f"ERROR: {message}")
        return False, 0, message

    if camera_id > 0:
        print(f"WARNING: Camera already registered with ID: {camera_id}")
        print(f"Camera SN '{c_sn}' is already in the system!")
        print("Please modify the serial number in configuration file.")
        return True, camera_id, f"Camera SN '{c_sn}' already registered"

    print("Camera not found in database, continue registration...")
    return False, 0, "Camera not registered"


def save_response_config(respond_path, request_config, response_data):
    """保存响应配置到文件

    Args:
        respond_path: 响应配置文件路径
        request_config: 请求配置字典
        response_data: 响应数据字典

    Returns:
        bool: 是否保存成功
    """
    # 构造完整的响应配置
    respond_config = {
        'request': request_config,
        'response': response_data
    }

    # 写入响应配置文件
    try:
        with open(respond_path, 'w', encoding='utf-8') as file:
            json.dump(respond_config, file, indent=4, ensure_ascii=False)
        print(f"Response configuration saved successfully: {respond_path}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to save response configuration: {e}")
        return False


# ------------------ 主注册函数 ------------------

def register_device(server_url, c_sn, u_sn, g_camera_id=None, u_url=''):
    """设备注册函数（可从外部调用）

    Args:
        server_url: 服务器地址
        c_sn: 摄像头序列号
        u_sn: Unit序列号
        g_camera_id: 全局摄像头ID（可选，从NVS读取）
        u_url: Unit URL（可选）

    Returns:
        dict: 注册结果
            - success: 是否成功
            - error: 错误消息（如果失败）
            - c_sn: 摄像头序列号
            - u_sn: Unit序列号
            - device_token: 设备令牌
            - u_camera_id: 摄像头ID
            - u_unit_id: Unit ID
            - u_account_id: 账户ID
            - password: 密码
            - u_url: Unit URL
            - server_url: 服务器地址
    """

    # 1. 打印并检测参数
    if not print_parameters(server_url, c_sn, u_sn, g_camera_id, u_url):
        return create_error_result("Parameter validation failed")

    # 使用固定的管理员token创建API连接
    api = StreamingEndpoint(server_url, ADMIN_TOKEN)

    # 2. 查询摄像头是否已注册
    is_registered, camera_id, message = check_camera_registered(api, c_sn)
    if is_registered:
        return create_error_result(message)

    # 3. 创建摄像头
    print("\n" + "-"*70)
    print("Step 2: Create Camera")
    print("-" * 60)

    success, u_camera_id, message = create_camera(api, c_sn, g_camera_id, DEFAULT_TIMEOUT)
    if not success:
        print(f"ERROR: {message}")
        return create_error_result(message)

    # 4. 创建 Unit
    print("\n" + "-"*70)
    print("Step 3: Create Unit")
    print("-" * 60)

    success, u_unit_id, message = create_unit(api, u_sn, u_camera_id, u_url, DEFAULT_TIMEOUT)
    if not success:
        print(f"ERROR: {message}")
        return create_error_result(message)

    # 5. 创建账户
    print("\n" + "-"*70)
    print("Step 4: Create Account")
    print("-" * 60)

    success, u_account_id, password, message = create_account(api, u_sn, DEFAULT_TIMEOUT)
    if not success:
        print(f"ERROR: {message}")
        return create_error_result(message)

    # 6. 获取设备 token
    print("\n" + "-"*70)
    print("Step 5: Get Device Token")
    print("-" * 60)

    success, device_token, message = get_device_token(api, u_sn, password, DEFAULT_TIMEOUT)
    if not success:
        print(f"ERROR: {message}")
        return create_error_result(message)

    # 7. 保存结果到响应配置文件
    print("\n" + "-"*70)
    print("Saving Response Configuration")
    print("-" * 60)

    request_config = {
        'server_url': server_url,
        'c_sn': c_sn,
        'u_sn': u_sn,
        'u_url': u_url
    }

    response_data = {
        'u_camera_id': u_camera_id,
        'u_unit_id': u_unit_id,
        'u_account_id': u_account_id,
        'password': password,
        'device_token': device_token
    }

    # 如果提供了 g_camera_id，也保存到响应配置
    if g_camera_id:
        response_data['c_sensor'] = g_camera_id

    if not save_response_config(RESPOND_CONFIG_PATH, request_config, response_data):
        return create_error_result("Failed to save response configuration")

    # 完成
    print("\n" + "-"*70)
    print("MS500 Device Registration Completed!")
    print("-" * 60)
    print(f"Camera SN     : {c_sn}")
    print(f"Unit SN       : {u_sn}")
    print(f"Camera ID     : {u_camera_id}")
    print(f"Unit ID       : {u_unit_id}")
    print(f"Account ID    : {u_account_id}")
    print(f"Password      : {password}")
    print(f"Device Token  : {device_token}")
    if g_camera_id:
        print(f"Global Camera ID : {g_camera_id}")
    print("-" * 60)
    print("Registration data saved to as_respond.json")

    # 返回统一格式的结果
    result = {
        'success': True,
        'c_sn': c_sn,
        'u_sn': u_sn,
        'device_token': device_token,
        'u_camera_id': u_camera_id,
        'u_unit_id': u_unit_id,
        'u_account_id': u_account_id,
        'password': password,
        'u_url': u_url,
        'server_url': server_url
    }

    # 如果提供了 g_camera_id，也添加到结果中
    if g_camera_id:
        result['c_sensor'] = g_camera_id

    return result


def main():
    """主函数，从配置文件读取参数并执行注册"""

    # 检查请求配置文件是否存在
    if not os.path.exists(REQUEST_CONFIG_PATH):
        print(f"Request configuration file not found: {REQUEST_CONFIG_PATH}")
        print("Please create as_request.json in the as_dm_register directory")
        return create_error_result("Request configuration file not found")

    # 读取请求配置
    try:
        with open(REQUEST_CONFIG_PATH, 'r', encoding='utf-8') as file:
            request_config = json.load(file)
    except Exception as e:
        print(f"Failed to read request configuration file: {e}")
        return create_error_result("Failed to read request configuration file")

    # 提取参数
    server_url = request_config.get('server_url', '').strip()
    c_sn = request_config.get('c_sn', '').strip()
    u_sn = request_config.get('u_sn', '').strip()
    g_camera_id = request_config.get('g_camera_id', None)  # 可选参数
    u_url = request_config.get('u_url', '').strip()

    # 调用注册函数
    return register_device(server_url, c_sn, u_sn, g_camera_id, u_url)


if __name__ == "__main__":
    try:
        result = main()
        exit_code = 0 if result.get('success', False) else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nRegistration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        sys.exit(1)
