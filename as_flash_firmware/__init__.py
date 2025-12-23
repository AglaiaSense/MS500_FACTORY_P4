#!/usr/bin/env python3
"""
as_flash_firmware 模块
导出固件烧录和分区工具函数，便于外部导入
"""

# 导出分区信息工具函数
from .as_spifs_partition import (
    parse_partitions_csv,
    get_partition_info,
    get_nvs_info,
    get_storage_dl_info,
)

__all__ = [
    "parse_partitions_csv",
    "get_partition_info",
    "get_nvs_info",
    "get_storage_dl_info",
]
