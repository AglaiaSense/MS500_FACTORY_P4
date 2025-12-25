#!/usr/bin/env python3
"""
MS500 DM (Device Management) API Module

设备管理服务器 API 通信模块
提供与 DM 服务器交互的所有 API 函数
"""

import json
import hashlib
import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

disable_warnings(InsecureRequestWarning)

# ------------------ API 路径宏定义 ------------------

API_CAMERA = '/camera/c/'
API_UNIT = '/camera/u/'
API_ACCOUNT = '/account/a/'
API_TOKEN_AUTH = '/api-token-auth/'

# ------------------ 服务器 Token 映射表 ------------------

SERVER_TOKENS = {
    "http://192.168.0.6:8000": "9b47d0133201679526cfc29825beff5f275574fa",
    "https://dm-be.leopardaws.com": "60e5c2a244f629d33290d23d75a63ba8e7f55555",
    "https://gs-be.leopardaws.com": "24db61d56ddaa9575ad6e4f906c02e94a3aecd68"
}

# ------------------ 默认超时时间 ------------------

DEFAULT_TIMEOUT = 300  # milliseconds


# ------------------ StreamingEndpoint 类 ------------------

class StreamingEndpoint:
    """服务器API连接类，用于与后端服务器通信"""

    def __init__(self, url, headers=None):
        """初始化API连接

        Args:
            url: 服务器地址
            headers: 认证头信息，可以是字符串(token)或字典
        """
        self.url = url
        self.session = requests.session()

        if headers:
            # 兼容处理：如果传入字符串，自动转换为字典格式
            if isinstance(headers, str):
                headers = {"Authorization": f"Token {headers}"}
            self.session.headers.update(headers)

        self.session.headers.update({'Content-Type': 'application/json'})

    def get_data_from_site(self, payload: dict, path: str = '', timeout: int = None):
        """从服务器获取数据"""
        try:
            req = self.session.get(self.url + path, params=payload, timeout=timeout, verify=False)
        except requests.exceptions.ConnectTimeout:
            return False, f"Connection timed out for {self.url}"
        except requests.exceptions.ConnectionError:
            return False, f"Server address error for {self.url}"
        except requests.exceptions.ReadTimeout:
            return False, f"{self.url} server response time out"

        if req.status_code == 200:
            result = json.loads(req.text)
            return True, result
        elif req.status_code == 204:
            # 204 No Content - 查询成功但没有数据，返回空结果
            return True, {'results': []}
        else:
            return False, f"Failed to get data {req.status_code}: {req.reason}"

    def post_data_to_site(self, payload: dict, path: str = '', timeout: int = None, file=None, useJson: bool = False):
        """向服务器POST数据"""
        try:
            if useJson:
                req = self.session.post(self.url + path, json=payload, files=file, timeout=timeout, verify=False)
            else:
                req = self.session.post(self.url + path, data=payload, files=file, timeout=timeout, verify=False)
        except requests.exceptions.ConnectTimeout:
            return False, f"Connection timed out for {self.url}"
        except requests.exceptions.ConnectionError:
            return False, f"Server address error for {self.url}"

        if req.status_code < 300:
            result = json.loads(req.text)
            return True, result
        else:
            # 尝试获取详细错误信息
            try:
                error_detail = req.json()
                return False, f"Failed to post data {req.status_code}: {req.reason}. Detail: {error_detail}"
            except:
                return False, f"Failed to post data {req.status_code}: {req.reason}. Response: {req.text}"


# ------------------ Token 获取函数 ------------------

def get_admin_token_for_server(server_url: str) -> str:
    """根据服务器地址获取对应的管理员 token

    Args:
        server_url: 服务器地址

    Returns:
        str: 对应的管理员 token

    Raises:
        ValueError: 如果找不到对应的 token
    """
    token = SERVER_TOKENS.get(server_url)

    if not token:
        available_servers = "\n".join([f"  - {server}" for server in SERVER_TOKENS.keys()])
        raise ValueError(
            f"找不到服务器 '{server_url}' 对应的 token\n"
            f"可用的服务器列表：\n{available_servers}"
        )

    print(f"已为服务器 {server_url} 获取到对应的 token")
    return token


# ------------------ 密码生成函数 ------------------

def generate_password_from_sn(u_sn: str) -> str:
    """基于u_sn生成固定密码

    密码格式：MS + MD5前6位 + !
    例如：MS79b2a1!

    Args:
        u_sn: Unit序列号

    Returns:
        str: 生成的密码
    """
    # 使用MD5哈希
    hash_obj = hashlib.md5(u_sn.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()

    # 生成密码：MS前缀 + MD5前6位 + ! 后缀
    password = 'MS' + hash_hex[:6] + '!'

    print(f"Generated password for {u_sn}: {password}")
    return password


# ------------------ API 函数：查询摄像头 ------------------

def query_camera(api: StreamingEndpoint, c_sn: str, timeout: int = DEFAULT_TIMEOUT):
    """查询摄像头是否已注册

    Args:
        api: StreamingEndpoint API连接实例
        c_sn: 摄像头序列号
        timeout: 超时时间（毫秒）

    Returns:
        tuple: (success: bool, camera_id: int or 0, message: str)
            - success: 是否成功查询
            - camera_id: 如果已注册返回 camera_id，否则返回 0
            - message: 错误消息或成功提示
    """
    print(f"Querying camera with c_sn: {c_sn}")

    ret, result = api.get_data_from_site({'c_sn': c_sn}, path=API_CAMERA, timeout=timeout)

    if not ret:
        return False, 0, f"Query camera failed: {result}"

    # 检查摄像头是否已存在
    if isinstance(result, dict) and len(result.get('results', [])) > 0:
        camera_data = result.get('results', [])[0]
        existing_camera_id = camera_data.get('id', 0)
        return True, existing_camera_id, f"Camera already registered with ID: {existing_camera_id}"

    return True, 0, "Camera not found in database"


# ------------------ API 函数：创建摄像头 ------------------

def create_camera(api: StreamingEndpoint, c_sn: str, g_camera_id: str = None, timeout: int = DEFAULT_TIMEOUT):
    """创建摄像头

    Args:
        api: StreamingEndpoint API连接实例
        c_sn: 摄像头序列号
        g_camera_id: 全局摄像头ID（可选，从NVS读取）
        timeout: 超时时间（毫秒）

    Returns:
        tuple: (success: bool, camera_id: int or 0, message: str)
            - success: 是否成功创建
            - camera_id: 创建的摄像头ID，失败返回0
            - message: 错误消息或成功提示
    """
    print(f"Creating camera with c_sn: {c_sn}")

    # 准备摄像头数据
    camera_data = {'c_sn': str(c_sn), 'c_order': 1, 'c_status': "NVCONNCTD"}

    # 添加 c_sensor 参数（从 NVS 的 g_camera_id 读取）
    if g_camera_id:
        camera_data['c_sensor'] = str(g_camera_id)
        print(f"Adding c_sensor parameter: {g_camera_id}")

    print(f"Camera data: {camera_data}")

    # 调用API创建摄像头
    ret, result = api.post_data_to_site(camera_data, API_CAMERA, timeout, useJson=True)

    if not ret or not isinstance(result, dict):
        return False, 0, f"Create camera failed: {result}"

    u_camera_id = result.get('id', 0)
    if u_camera_id == 0:
        return False, 0, f"Camera created but ID not found in response: {result}"

    print(f"Camera created successfully with ID: {u_camera_id}")
    return True, u_camera_id, "Camera created successfully"


# ------------------ API 函数：创建 Unit ------------------

def create_unit(api: StreamingEndpoint, u_sn: str, u_camera_id: int, u_url: str = '', timeout: int = DEFAULT_TIMEOUT):
    """创建 Unit

    Args:
        api: StreamingEndpoint API连接实例
        u_sn: Unit序列号
        u_camera_id: 关联的摄像头ID
        u_url: Unit URL（可选）
        timeout: 超时时间（毫秒）

    Returns:
        tuple: (success: bool, unit_id: int or 0, message: str)
            - success: 是否成功创建
            - unit_id: 创建的Unit ID，失败返回0
            - message: 错误消息或成功提示
    """
    print(f"Creating Unit with u_sn: {u_sn}, camera_id: {u_camera_id}")

    # 准备Unit数据
    unit_data = {
        'u_sn': u_sn,
        'u_camera': [u_camera_id],  # 关联摄像头ID（列表）
        'u_status': "NVCONNCTD"  # 状态：未连接
    }

    # 添加可选参数
    if u_url:
        unit_data['u_url'] = u_url

    print(f"Unit data: {unit_data}")

    # 调用API创建Unit
    ret, result = api.post_data_to_site(unit_data, API_UNIT, timeout, useJson=True)

    if not ret:
        return False, 0, f"Create Unit failed: {result}"

    u_unit_id = result.get('id', 0)
    if u_unit_id == 0:
        return False, 0, f"Unit created but ID not found in response: {result}"

    print(f"Unit created successfully with ID: {u_unit_id}")
    return True, u_unit_id, "Unit created successfully"


# ------------------ API 函数：创建账户 ------------------

def create_account(api: StreamingEndpoint, u_sn: str, timeout: int = DEFAULT_TIMEOUT):
    """创建账户

    Args:
        api: StreamingEndpoint API连接实例
        u_sn: Unit序列号（用作用户名）
        timeout: 超时时间（毫秒）

    Returns:
        tuple: (success: bool, account_id: int or 0, password: str, message: str)
            - success: 是否成功创建
            - account_id: 创建的账户ID，失败返回0
            - password: 生成的密码
            - message: 错误消息或成功提示
    """
    print(f"Creating account for username: {u_sn}")

    # 生成固定密码（基于u_sn）
    password = generate_password_from_sn(u_sn)

    # 准备账户数据
    a_user = {
        "username": u_sn,
        "password": password,
        "password_confirm": password
    }

    account_data = {
        'a_user': a_user,
        'a_type': "Device"
    }

    # 调用API创建账户
    ret, result = api.post_data_to_site(account_data, API_ACCOUNT, timeout, useJson=True)

    if not ret:
        return False, 0, password, f"Create account failed: {result}"

    # 获取账户ID
    u_account_id = result.get('id', 0)
    if u_account_id == 0:
        return False, 0, password, f"Account created but ID not found in response: {result}"

    print(f"Account created successfully with ID: {u_account_id}")
    return True, u_account_id, password, "Account created successfully"


# ------------------ API 函数：获取设备 Token ------------------

def get_device_token(api: StreamingEndpoint, u_sn: str, password: str, timeout: int = DEFAULT_TIMEOUT):
    """使用用户名/密码获取设备 token

    Args:
        api: StreamingEndpoint API连接实例
        u_sn: Unit序列号（用作用户名）
        password: 密码
        timeout: 超时时间（毫秒）

    Returns:
        tuple: (success: bool, token: str, message: str)
            - success: 是否成功获取
            - token: 设备token，失败返回空字符串
            - message: 错误消息或成功提示
    """
    print(f"Getting device token for username: {u_sn}")

    # 准备认证数据
    auth_payload = {"username": u_sn, "password": password}

    # 调用API获取设备token
    ret, result = api.post_data_to_site(auth_payload, API_TOKEN_AUTH, timeout, useJson=True)

    if not ret or not isinstance(result, dict):
        return False, '', f"Get device token failed: {result}"

    device_token = result.get("token", '')
    if not device_token:
        return False, '', f"Token not found in response: {result}"

    print(f"Device token retrieved successfully: {device_token[:20]}...")
    return True, device_token, "Device token retrieved successfully"
