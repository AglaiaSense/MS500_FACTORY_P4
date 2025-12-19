"""
AI 模型认证和打包工具
将模型文件上传到 AITRIOS 平台并完成打包发布流程

【重要更新】
- 使用 model_conversion.py 进行模型转换，避免了 SSL 错误
- model_conversion.py 使用 curl 命令而不是 requests 库，更加稳定
- 支持自定义输出目录（config.output_dir）
- model_id 自动基于时间戳生成，不再需要 model_id_counter

使用方法:
1. 配置 model_config.json 文件:
   {
     "model_dir": "模型目录名",
     "device_id": "设备ID"
   }
2. 运行: python as_model_auth.py
3. 转换后的文件保存到: as_model_conversion/{model_dir}/output/
4. 解压文件保存到: as_model_conversion/{model_dir}/temp/{文件名}/
"""

import os
import sys
import json
import zipfile
import shutil
from pathlib import Path
from typing import Dict, Optional


class ModelConfig:
    """模型配置管理类"""

    def __init__(self, config_file: str = "model_config.json"):
        self.config_file = config_file
        self.base_dir = Path(__file__).parent
        self.config = self._load_config()

        # 初始化路径
        self.model_dir = self.base_dir / self.config["model_dir"]
        self.packerOut_path = self.model_dir / "packerOut.zip"
        self.network_info_path = self.model_dir / "network_info.txt"
        self.output_dir = self.model_dir / "output"
        self.temp_dir = self.model_dir / "temp"

        # 确保目录存在
        self._ensure_directories()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_file}\n"
                f"Please create model_config.json with required fields:\n"
                f"  - model_dir: 模型目录名称\n"
                f"  - device_id: 设备ID"
            )

        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 验证必需字段（不再需要 model_id_counter）
        required_keys = ["model_dir", "device_id"]
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise KeyError(f"Missing required keys in config: {missing_keys}")

        return config

    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def get_device_id(self) -> str:
        """获取设备ID"""
        return self.config["device_id"]

    def get_model_dir_name(self) -> str:
        """获取模型目录名称"""
        return self.config["model_dir"]


# ------------------  工具函数  ------------------

def process_downloaded_model(zip_path: str, network_info_path: str, temp_dir: str) -> bool:
    """
    处理下载的模型文件
    1. 解压到临时目录下的文件名子目录（temp/文件名）
    2. 替换 network_info.txt
    """
    print("### Process Downloaded Model")

    # 从 zip 文件路径中提取文件名（不含扩展名）
    zip_filename = os.path.basename(zip_path)
    folder_name = os.path.splitext(zip_filename)[0]  # 去掉 .zip 扩展名

    # 创建解压目标目录：temp/文件名
    extract_dir = os.path.join(temp_dir, folder_name)
    os.makedirs(extract_dir, exist_ok=True)

    # 解压文件
    print(f"Extracting {zip_path}")
    print(f"Target directory: {extract_dir}")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    # 查找并替换 network_info.txt
    for root, dirs, files in os.walk(extract_dir):
        if 'network_info.txt' in files:
            target_path = os.path.join(root, 'network_info.txt')
            print(f"Replacing {target_path} with {network_info_path}")
            shutil.copy2(network_info_path, target_path)
            print(f"network_info.txt replaced successfully")
            return True

    print("Warning: network_info.txt not found in extracted files")
    return False


# ------------------  主流程  ------------------

def generate_model_by_device_id(device_id: str, config_file: str = "model_config.json") -> Optional[str]:
    """
    根据传入的 device_id 生成模型文件

    Args:
        device_id: 设备ID
        config_file: 配置文件路径

    Returns:
        生成的模型文件解压后的 temp 目录路径，失败返回 None
    """
    print(f"\n### Generate Model by Device ID")
    print(f"Device ID: {device_id}")

    # 初始化配置
    config = ModelConfig(config_file)

    try:
        # 步骤 1: 更新配置文件中的 device_id
        config.config["device_id"] = device_id
        with open(config.config_file, 'w', encoding='utf-8') as f:
            json.dump(config.config, f, indent=4, ensure_ascii=False)
        print(f"✓ Updated device_id in {config.config_file}")

        # 步骤 2: 获取配置参数和路径
        packerOut_path = config.packerOut_path
        output_dir = config.output_dir

        print(f"Using as_model_conversion directory: {config.model_dir}")
        print(f"Using DEVICE_ID: {device_id}")
        print(f"Using packerOut path: {packerOut_path}")
        print(f"Using output directory: {output_dir}")

        # 步骤 3: 使用 model_conversion.py 进行模型转换
        print("\n### Using model_conversion.py for as_model_conversion conversion")
        print("Note: model_conversion.py uses curl command to avoid SSL errors")

        from model_conversion import model_convert

        # 调用 model_convert 函数
        downloaded_file = model_convert(device_id, str(packerOut_path), str(output_dir))

        if not downloaded_file:
            print("Error: Model conversion failed")
            return None

        print(f"\n✓ Model conversion successful!")
        print(f"Output file: {downloaded_file}")

        # 步骤 4: 处理下载的模型文件（如果需要替换 network_info.txt）
        # 解压文件并返回解压后的目录路径
        zip_filename = os.path.basename(downloaded_file)
        folder_name = os.path.splitext(zip_filename)[0]
        extract_dir = os.path.join(str(config.temp_dir), folder_name)
        os.makedirs(extract_dir, exist_ok=True)

        print(f"\nExtracting {downloaded_file}")
        print(f"Target directory: {extract_dir}")

        with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        print(f"✓ Extracted to {extract_dir}")

        # 如果存在 network_info.txt，进行替换
        if config.network_info_path.exists():
            print("\n### Processing downloaded as_model_conversion")
            # 查找并替换 network_info.txt
            for root, dirs, files in os.walk(extract_dir):
                if 'network_info.txt' in files:
                    target_path = os.path.join(root, 'network_info.txt')
                    print(f"Replacing {target_path} with {config.network_info_path}")
                    shutil.copy2(str(config.network_info_path), target_path)
                    print(f"network_info.txt replaced successfully")
                    break

        # 返回解压后的具体目录路径（包含 network.fpk, network_info.txt, readme.json）
        print(f"\n✓ Model directory: {extract_dir}")
        return str(extract_dir)

    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数 - 完整的模型打包流程（使用 model_conversion.py）"""

    # 初始化配置
    config = ModelConfig("model_config.json")

    try:
        # 步骤 1: 获取配置参数和路径
        device_id = config.get_device_id()
        packerOut_path = config.packerOut_path
        output_dir = config.output_dir

        print(f"Using as_model_conversion directory: {config.model_dir}")
        print(f"Using DEVICE_ID: {device_id}")
        print(f"Using packerOut path: {packerOut_path}")
        print(f"Using output directory: {output_dir}")

        # 步骤 2: 使用 model_conversion.py 进行模型转换
        print("\n### 使用 model_conversion.py 进行模型转换")
        print("注意: model_conversion.py 使用 curl 命令，避免了 SSL 错误")

        from model_conversion import model_convert

        # 调用 model_convert 函数
        downloaded_file = model_convert(device_id, str(packerOut_path), str(output_dir))

        if not downloaded_file:
            print("Error: Model conversion failed")
            return 1

        print(f"\n模型转换成功!")
        print(f"输出文件: {downloaded_file}")

        # 步骤 3: 处理下载的模型文件（如果需要替换 network_info.txt）
        if config.network_info_path.exists():
            print("\n### Processing downloaded as_model_conversion")
            process_downloaded_model(downloaded_file, str(config.network_info_path), str(config.temp_dir))
        else:
            print("\n### network_info.txt not found, skipping processing")

        print("\n=== All steps completed successfully ===")
        print(f"Device ID: {device_id}")
        print(f"Output: {downloaded_file}")
        return 0

    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
