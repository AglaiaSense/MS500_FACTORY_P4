"""
ESP 组件工具包
提供 ESP-IDF 相关工具的统一接口
"""

import os
import sys

# 自动设置项目根目录到 sys.path
# 这样所有导入 esp_components 的模块都能直接使用，无需手动添加路径
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from .esp_tools import (
    get_esp_idf_python,
    get_nvs_tool_path,
    get_fatfs_gen_tool,
    get_esptool,
    get_nvs_gen_module,
    get_baud_rate,
    test_port_connection,
    run_command,
    run_command_with_error_check,
    verify_python_environment,
    verify_nvs_tools,
    verify_fatfs_tools,
    verify_all_tools,
)

__all__ = [
    "get_esp_idf_python",
    "get_nvs_tool_path",
    "get_fatfs_gen_tool",
    "get_esptool",
    "get_nvs_gen_module",
    "get_baud_rate",
    "test_port_connection",
    "run_command",
    "run_command_with_error_check",
    "verify_python_environment",
    "verify_nvs_tools",
    "verify_fatfs_tools",
    "verify_all_tools",
]
