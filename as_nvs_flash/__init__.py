"""
as_nvs_flash 模块 - NVS 数据管理统一接口

提供 NVS 读取、解析、生成和烧录的完整功能
"""

from .as_nvs_read import (
    init_temp_dir,
    read_flash_and_mac,
    check_nvs_data,
    get_nvs_raw_bin_path,
)

from .as_nvs_update import (
    generate_nvs_data,
    flash_nvs,
    get_nvs_bin_path,
)

__all__ = [
    # 读取模块
    "init_temp_dir",
    "read_flash_and_mac",
    "check_nvs_data",
    "get_nvs_raw_bin_path",
    # 更新模块
    "generate_nvs_data",
    "flash_nvs",
    "get_nvs_bin_path",
]
