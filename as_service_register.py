#!/usr/bin/env python3
"""
MS500 Service Register Script

专门用于注册设备的独立服务脚本
包含完整的设备注册流程，所有代码都在此文件中，无外部依赖

注册步骤:
1. 重置配置文件
2. 查询摄像头是否已注册（如果已注册则提示并退出）
3. 创建摄像头
4. 创建 Unit
5. 创建账户
6. 使用用户名/密码获取设备 token

Usage:
    python service_register.py
"""

import json
import os
import sys
import re
import hashlib
import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

disable_warnings(InsecureRequestWarning)

# ------------------ 常量定义 ------------------

# 固定的管理员Token
ADMIN_TOKEN = "9b47d0133201679526cfc29825beff5f275574fa"

# API endpoints
CAMERA = '/camera/c/'
TIME_OUT = 300  # milliseconds

# 配置文件路径（当前目录下的 ms500.json）
UNIT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ms500.json')


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


# ------------------ 配置管理函数 ------------------

def reset_config(config_path):
    """
    重置配置文件，保留 server_url, c_sn, for_organization, u_url
    """

    # 读取配置
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return False

    # 保留的参数
    server_url = config.get('server_url', '')
    c_sn = config.get('c_sn', '')
    u_sn = config.get('u_sn', '')
    for_organization = config.get('for_organization', '')
    u_url = config.get('u_url', '')

    # 创建新的配置，只保留指定参数
    new_config = {
        'server_url': server_url,
        'c_sn': c_sn,
        'u_sn': u_sn,
        'for_organization': for_organization,
        'u_url': u_url
    }

    # 保存配置
    try:
        with open(config_path, 'w', encoding='utf-8') as file:
            json.dump(new_config, file, indent=4, ensure_ascii=False)
        print(f"配置文件重置成功")
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False


# ------------------ 密码生成函数 ------------------

def generate_password_from_sn(u_sn: str) -> str:
    """基于u_sn生成固定密码

    密码格式：MS + MD5前6位 + !
    例如：MS79b2a1!
    """
    # 使用MD5哈希
    hash_obj = hashlib.md5(u_sn.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()

    # 生成密码：MS前缀 + MD5前6位 + ! 后缀
    password = 'MS' + hash_hex[:6] + '!'

    print(f"为 {u_sn} 生成密码: {password}")
    return password


# ------------------ 主注册函数 ------------------

def main():
    """主函数，执行完整的设备注册流程"""

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
            'u_url': '',
            'server_url': ''
        }

    # 检查配置文件是否存在
    config_path = UNIT_CONFIG_PATH
    if not os.path.exists(config_path):
        print(f"未找到配置文件: {config_path}")
        print("请在 python_factory 目录下创建 ms500.json")
        return create_error_result("未找到配置文件")

    # 每次运行前重置配置文件
    if not reset_config(config_path):
        return create_error_result("配置文件重置失败")

    # 读取重置后的配置
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            unit_config = json.load(file)
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return create_error_result(f"读取配置文件失败: {e}")

    # 获取配置信息
    server_url = unit_config.get('server_url', '').strip()
    if not server_url:
        print("配置文件中缺少 server_url")
        return create_error_result("配置文件中缺少 server_url")

    c_sn = unit_config.get('c_sn', '').strip()
    if not c_sn:
        print("配置文件中缺少 c_sn")
        return create_error_result("配置文件中缺少 c_sn")

    # 获取u_sn配置（新增）
    u_sn = unit_config.get('u_sn', '').strip()
    if not u_sn:
        print("配置文件中缺少 u_sn")
        return create_error_result("配置文件中缺少 u_sn")

    for_organization = unit_config.get('for_organization', '')
    u_url = unit_config.get('u_url', '').strip()

    print("\n配置信息:")
    print(f"  服务器地址: {server_url}")
    print(f"  相机序列号: {c_sn}")
    print(f"  Unit序列号(u_sn): {u_sn}")
    print(f"  组织ID: {for_organization}")
    print(f"  Unit URL: {u_url}")

    # 使用固定的管理员token创建API连接
    api = StreamingEndpoint(server_url, ADMIN_TOKEN)

    # ------------------ 步骤1: 查询摄像头是否已注册 ------------------
    print("\n步骤 1: 检查相机是否已注册...")
    print("-" * 70)

    ret, result = api.get_data_from_site({'c_sn': c_sn}, path=CAMERA, timeout=TIME_OUT)

    if not ret:
        print(f"查询相机失败: {result}")
        return create_error_result(f"查询相机失败: {result}")

    # 检查摄像头是否已存在
    if isinstance(result, dict) and len(result.get('results', [])) > 0:
        # 摄像头已注册
        camera_data = result.get('results', [])[0]
        existing_camera_id = camera_data.get('id', 0)
        print(f"相机已注册，ID: {existing_camera_id}")
        print("注册已终止")
        print(f"相机序列号 '{c_sn}' 已在系统中注册！")
        print("请修改配置文件中的序列号。")
        return create_error_result(f"相机序列号 '{c_sn}' 已注册，请修改序列号")

    print("数据库中未找到相机，继续注册...")

    # ------------------ 步骤2: 创建摄像头 ------------------
    print("\n步骤 2: 创建相机...")
    print("-" * 70)

    # 准备摄像头数据
    camera_data = {'c_sn': str(c_sn), 'c_order': 1, 'c_status': "NVCONNCTD"}

    # 调用API创建摄像头
    ret, result = api.post_data_to_site(camera_data, CAMERA, TIME_OUT, useJson=True)

    if not ret or not isinstance(result, dict):
        print(f"创建相机失败: {result}")
        return create_error_result(f"创建相机失败: {result}")

    u_camera_id = result.get('id', 0)
    if u_camera_id == 0:
        print(f"相机已创建但响应中未找到 ID: {result}")
        return create_error_result("相机已创建但响应中未找到 ID")

    print(f"相机创建成功，ID: {u_camera_id}")

    # ------------------ 步骤3: 创建Unit ------------------
    print("\n步骤 3: 创建 Unit...")
    print("-" * 70)

    # 准备Unit数据
    unit_data = {
        'u_sn': u_sn,  # 使用u_sn作为Unit序列号
        'u_camera': [u_camera_id],  # 关联摄像头ID（列表）
        'u_status': "NVCONNCTD"  # 状态：未连接
    }

    # 添加可选参数
    # if for_organization:
    #     unit_data['for_organization'] = for_organization

    if u_url:
        unit_data['u_url'] = u_url

    print(f"Unit 数据: {unit_data}")

    # 调用API创建Unit
    ret, result = api.post_data_to_site(unit_data, '/camera/u/', TIME_OUT, useJson=True)

    if not ret:
        print(f"创建 Unit 失败: {result}")
        return create_error_result(f"创建 Unit 失败: {result}")

    u_unit_id = result.get('id', 0)
    if u_unit_id == 0:
        print(f"Unit 已创建但响应中未找到 ID: {result}")
        return create_error_result("Unit 已创建但响应中未找到 ID")

    print(f"Unit 创建成功，ID: {u_unit_id}")

    # ------------------ 步骤4: 创建账户 ------------------
    print("\n步骤 4: 创建账户...")
    print("-" * 70)

    # 生成固定密码（u_sn）
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

    # 添加可选参数
    # if for_organization:
    #     account_data['for_organization'] = for_organization

    print(f"为用户名创建账户: {u_sn}")

    # 调用API创建账户
    ret, result = api.post_data_to_site(account_data, '/account/a/', TIME_OUT, useJson=True)

    if not ret:
        print(f"创建账户失败: {result}")
        return create_error_result(f"创建账户失败: {result}")

    # 获取账户ID
    u_account_id = result.get('id', '')
    if not u_account_id:
        print(f"账户已创建但响应中未找到 ID: {result}")
        return create_error_result("账户已创建但响应中未找到 ID")

    print(f"账户创建成功，ID: {u_account_id}")

    # ------------------ 步骤5: 使用用户名/密码获取设备 token ------------------
    print("\n步骤 5: 获取设备 token...")
    print("-" * 70)

    # 准备认证数据
    auth_payload = {"username": u_sn, "password": password}

    # 调用API获取设备token
    ret, result = api.post_data_to_site(auth_payload, '/api-token-auth/', TIME_OUT, useJson=True)

    if not ret or not isinstance(result, dict):
        print(f"获取设备 token 失败: {result}")
        return create_error_result(f"获取设备 token 失败: {result}")

    device_token = result.get("token")
    if not device_token:
        print(f"响应中未找到 token: {result}")
        return create_error_result("响应中未找到 token")

    print(f"设备 token 获取成功: {device_token[:20]}...")

    # ------------------ 保存结果到配置文件 ------------------

    # 更新配置
    unit_config['u_camera_id'] = u_camera_id
    unit_config['u_unit_id'] = u_unit_id
    unit_config['u_account_id'] = u_account_id
    unit_config['password'] = password
    unit_config['device_token'] = device_token

    # 写回配置文件
    try:
        with open(config_path, 'w', encoding='utf-8') as file:
            json.dump(unit_config, file, indent=4, ensure_ascii=False)
        print(f"配置文件更新成功: {config_path}")
    except Exception as e:
        print(f"更新配置文件失败: {e}")
        return create_error_result(f"更新配置文件失败: {e}")

    # ------------------ 完成 ------------------
    print("\n" +"MS500 设备注册完成！")
    print(f"SN : {c_sn}")
    print(f"Unit SN : {u_sn}")
    print(f"相机 ID: {u_camera_id}")
    print(f"Unit ID: {u_unit_id}")
    print(f"账户 ID: {u_account_id}")
    print(f"密码: {password}")
    print(f"设备 Token: {device_token}")
    print("注册数据已保存到 ms500.json")

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

    return result


if __name__ == "__main__":
    try:
        result = main()
        exit_code = 0 if result.get('success', False) else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n注册被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n意外错误: {str(e)}")
        sys.exit(1)
