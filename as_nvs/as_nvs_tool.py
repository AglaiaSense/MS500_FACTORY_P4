"""
as_nvs_tool.py - 兼容性包装器

为了保持向后兼容，此文件重新导出所有 as_nvs 模块的功能
新代码应该直接使用 as_nvs_read 和 as_nvs_update 模块
"""

# 从读取模块导入
from .as_nvs_read import (
    init_temp_dir,
    check_nvs_data,
    get_nvs_raw_bin_path,
    convert_to_csv,
)

# 从更新模块导入
from .as_nvs_update import (
    generate_nvs_data,
    get_nvs_bin_path,
)

# 导出所有函数以保持向后兼容
__all__ = [
    "init_temp_dir",
    "check_nvs_data",
    "get_nvs_raw_bin_path",
    "convert_to_csv",
    "generate_nvs_data",
    "get_nvs_bin_path",
]
