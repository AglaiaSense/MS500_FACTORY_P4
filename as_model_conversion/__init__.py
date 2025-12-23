#!/usr/bin/env python3
"""
as_model_conversion 模块
导出模型认证和转换函数，便于外部导入
"""

# 导出模型认证函数
from .as_model_auth import generate_model_by_device_id

__all__ = ["generate_model_by_device_id"]
