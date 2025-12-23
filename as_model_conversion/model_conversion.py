import subprocess
import json
import base64
import requests
from urllib.parse import urlparse
from datetime import datetime
import time
import os

# 定义常量
TENANT_ID = "00g4kibanoaacZRcb697"
CLIENT_ID = "0oa4p8u9cl2sz1syf697"
SECRET = "7skkuCY3wMxQ4E9Nr73dk4-Aar9e1DI1DDcNk3Xs"
ORDINAL = 0
FORMAT = "RGB"
SYSTEM_DOMAIN = "https://conv-pack.aitrios.sony-semicon.com"
PORTAL_OKTA_DOMAIN = "https://auth.aitrios.sony-semicon.com"
PARENT_META_FIELD = "aitriosPortalConverterPackager"    
CHILD_META_FIELD_Conveter = "aitriosPortalConverter"    
CHILD_META_FIELD_Packager = "aitriosPortalPackager"

# 获取访问令牌
def get_access_token():
    print("### 获取访问令牌")
    credentials = f"{CLIENT_ID}:{SECRET}".encode("utf-8")
    authorization_code = base64.b64encode(credentials).decode("utf-8")

    command = [
        "curl", "--request", "POST",
        f"{PORTAL_OKTA_DOMAIN}/oauth2/default/v1/token",
        "--header", "accept: application/json",
        "--header", f"authorization: Basic {authorization_code}",
        "--header", "cache-control: no-cache",
        "--header", "content-type: application/x-www-form-urlencoded",
        "--data", "grant_type=client_credentials&scope=system"
    ]

    try:
        response = subprocess.run(command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        return json.loads(response.stdout)["access_token"]
    except subprocess.CalledProcessError as e:
        print(f"获取访问令牌时出错: {e.stderr}")
        return None

# 上传文件
def upload_file(access_token, model_path):
    print("### 上传文件")
    command = [
        "curl", "--location", "--request", "POST", f"{SYSTEM_DOMAIN}/api/v1/files",
        "--header", "Content-Type: multipart/form-data",
        "--header", f"Authorization: Bearer {access_token}",
        "--header", f"tenant_id: {TENANT_ID}",
        "--form", f"file=@{model_path}",
        "--form", "type_code=productAiModelConverted"
    ]

    try:
        response = subprocess.run(command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        return json.loads(response.stdout)["file_info"]["id"]
    except subprocess.CalledProcessError as e:
        print(f"上传文件时出错: {e.stderr}")
        return None

# 导入模型
def import_model(access_token, model_id,file_id):
    print("### 导入模型")
    command = [
        "curl", "--location", "--request", "POST", f"{SYSTEM_DOMAIN}/api/v1/models",
        "--header", "Content-Type: application/json",
        "--header", "source-service: marketplace",
        "--header", f"tenant_id: {TENANT_ID}",
        "--header", f"Authorization: Bearer {access_token}",
        "--header", f"parent_meta_field: {PARENT_META_FIELD}",
        "--header", f"child_meta_field: {CHILD_META_FIELD_Conveter}",
        "--data-raw", json.dumps({
            "model_id": model_id,
            "file_id": file_id,
            "network_type": "1",
            "input_format_param": [{"ordinal": ORDINAL, "format": FORMAT}]
        })
    ]

    try:
        response = subprocess.run(command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        result = json.loads(response.stdout)["result"]
        if result != "SUCCESS":
            print(f"导入模型失败:", response.stdout)
            return False
        print(f"导入模型成功!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"导入模型时出错: {e.stderr}")
        return False

# 发布模型
def publish_model(access_token, device_id, model_id):
    print(f"### 发布模型")
    command = [
        "curl", "--location", "--request", "POST", f"{SYSTEM_DOMAIN}/api/v1/models/{model_id}/model_publish",
        "--header", "Content-Type: application/json",
        "--header", "source-service: marketplace",
        "--header", f"tenant_id: {TENANT_ID}",
        "--header", f"Authorization: Bearer {access_token}",
        "--header", f"parent_meta_field: {PARENT_META_FIELD}",
        "--header", f"child_meta_field: {CHILD_META_FIELD_Packager}",
        "--data-raw", json.dumps({
            "device_id": device_id,
            "key_generation": "0001",
            "packager_version": "4.00.00"
        })
    ]

    try:
        response = subprocess.run(command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        result = json.loads(response.stdout)["result"]
        transaction_id = json.loads(response.stdout)["transaction_id"]
        if result != "SUCCESS":
            print(f"发布模型失败:", response.stdout)
            return None
        print(f"模型发布成功，事务 ID = {transaction_id}")
        return transaction_id
    except subprocess.CalledProcessError as e:
        print(f"发布模型时出错: {e.stderr}")
        return None

# 获取发布状态
def get_publish_status(access_token, transaction_id):
    print(f"### 获取发布状态")
    print(f"请稍候...")

    while True:
        time.sleep(10)  # 使用 time.sleep
        command = [
            "curl", "--location", "--request", "GET", f"{SYSTEM_DOMAIN}/api/v1/model_publish/{transaction_id}/status?include_publish_url=true",
            "--header", "Content-Type: application/json",
            "--header", "source-service: marketplace",
            "--header", f"tenant_id: {TENANT_ID}",
            "--header", f"Authorization: Bearer {access_token}"
        ]

        try:
            response = subprocess.run(command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            status = json.loads(response.stdout)["status"]
            publish_url = json.loads(response.stdout)["publish_url"]
            if status == "Publish complete":
                print(f"发布 URL = {publish_url}")
                print(f"完成!")
                return publish_url
            else:
                print(f"未完成! 重试中...")
        except subprocess.CalledProcessError as e:
            print(f"获取发布状态时出错: {e.stderr}")
            return None

def download_model(publish_url, output_dir=None):
    """
    下载模型文件

    Args:
        publish_url: 下载URL
        output_dir: 输出目录，如果为None则保存到当前目录

    Returns:
        下载的文件路径，失败返回None
    """
    # 解析 URL
    parsed_url = urlparse(publish_url)
    file_name = parsed_url.path.split('/')[-1]

    # 确定输出路径
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, file_name)
    else:
        output_path = file_name

    print(f"文件名 = {file_name}")
    print(f"输出路径 = {output_path}")

    try:
        # 发送 GET 请求下载文件
        response = requests.get(publish_url, allow_redirects=True)

        # 检查响应状态
        if response.status_code == 200:
            with open(output_path, 'wb') as file:
                file.write(response.content)
            print(f"文件 {file_name} 下载成功")
            return output_path
        else:
            print(f"下载文件失败。状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"下载文件时发生错误: {e}")
        return None

# 模型转换主函数
def model_convert(device_id, model_path, output_dir=None):
    """
    模型转换主函数
Args:
        device_id: 设备ID
        model_path: 模型文件路径
        output_dir: 输出目录，如果为None则保存到当前目录

    Returns:
        转换后的文件路径，失败返回None
    """
    # 获取当前时间
    current_time = datetime.now()
    model_id= current_time.strftime("%Y%m%d_%H%M%S%f")
    print(f"model_id:{model_id}")
    access_token = get_access_token()
    if not access_token:
        return None

    file_id = upload_file(access_token, model_path)
    if not file_id:
        return None

    if not import_model(access_token, model_id, file_id):
        return None

    transaction_id = publish_model(access_token, device_id, model_id)
    if not transaction_id:
        return None

    publish_url = get_publish_status(access_token, transaction_id)
    if publish_url:
        return download_model(publish_url, output_dir)
    return None


