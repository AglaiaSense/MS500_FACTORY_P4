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
    print("### Get Access Token")
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
        print(f"Error getting access token: {e.stderr}")
        return None

# 上传文件
def upload_file(access_token, model_path):
    print("### Upload File")
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
        print(f"Error uploading file: {e.stderr}")
        return None

# 导入模型
def import_model(access_token, model_id,file_id):
    print("### Import Model")
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
            print(f"Import Model failed:", response.stdout)
            return False
        print(f"Import Model succeeded!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error importing model: {e.stderr}")
        return False

# 发布模型
def publish_model(access_token, device_id, model_id):
    print(f"### Publish Model")
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
            print(f"Publish Model failed:", response.stdout)
            return None
        print(f"Model published successfully with TRANSACTION_ID = {transaction_id}")
        return transaction_id
    except subprocess.CalledProcessError as e:
        print(f"Error publishing model: {e.stderr}")
        return None

# 获取发布状态
def get_publish_status(access_token, transaction_id):
    print(f"### Get Publish Status")
    print(f"Wait a moment...")
    
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
                print(f"PUBLISH_URL = {publish_url}")
                print(f"Complete!")
                return publish_url
            else:
                print(f"Incomplete! Retrying...")
        except subprocess.CalledProcessError as e:
            print(f"Error getting publish status: {e.stderr}")
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

    print(f"FILE_NAME = {file_name}")
    print(f"OUTPUT_PATH = {output_path}")

    try:
        # 发送 GET 请求下载文件
        response = requests.get(publish_url, allow_redirects=True)

        # 检查响应状态
        if response.status_code == 200:
            with open(output_path, 'wb') as file:
                file.write(response.content)
            print(f"File {file_name} downloaded successfully.")
            return output_path
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error occurred while downloading the file: {e}")
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


# 加载转换器配置
def load_converter_config():
    """从 converter_config.json 加载转换器配置"""
    config_file = "resource/converter_config.json"
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载转换器配置失败: {e}")
        return None


# 模型转换器工厂函数
def get_model_converter(converter_type: str, config: dict):
    """
    根据配置创建模型转换器实例

    Args:
        converter_type: 转换器类型 ("Sony" | "Irida")
        config: 配置字典，包含客户配置（如 IridaModelId）和进度回调

    Returns:
        转换器实例 (SonyModelConverter 或 IridaModelConverter)
    """
    if converter_type == "Irida":
        from update.irida_converter import IridaModelConverter

        # 从转换器配置文件读取 API Key 和 Base URL
        converter_config = load_converter_config()
        if not converter_config:
            raise ValueError("无法加载转换器配置文件 (converter_config.json)")

        irida_config = converter_config.get("converters", {}).get("Irida", {})
        api_key = irida_config.get("apiKey", "")
        base_url = irida_config.get("baseUrl", "")

        if not api_key or not base_url:
            raise ValueError("转换器配置文件中缺少 Irida API Key 或 Base URL")

        # 从客户配置读取模型 ID
        model_id = config.get("IridaModelId", "parking-mm")
        progress_callback = config.get("progress_callback", None)

        print(f"创建 Irida 转换器: API Key={'***' + api_key[-4:]}, 模型={model_id}")
        return IridaModelConverter(api_key, base_url, model_id, progress_callback)
    else:  # 默认 Sony
        from update.sony_converter import SonyModelConverter
        print("创建 Sony 转换器")
        return SonyModelConverter()


# if __name__ == "__main__":
#     # 可以在这里替换 DEVICE_ID, MODEL_PATH, MODEL_ID
#     DEVICE_ID = "100B50501A2101059064011000000000"
#     MODEL_PATH = "SSDMOBILENET/300x300/v3.5-ssd_mobilenet_v1_0.75_depth_quantized_qat_MLIR-packerOut.zip"
#
#     filename = model_convert(DEVICE_ID, MODEL_PATH)
#     if filename:
#         print(f"Successfully converted model. Filename: {filename}")
#     else:
#         print(f"Model conversion failed.")
