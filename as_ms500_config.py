#!/usr/bin/env python3
"""
MS500 设备配置读取模块

功能说明:
统一管理 MS500 设备的配置参数读取，所有模块从这里获取配置

配置文件位置: as_ms500_config.json

配置参数说明:
- PORT: 串口号 (例如: "COM4")
- BIN_TYPE: 固件类型 (例如: "ped_alarm")
- MODEL_TYPE: 模型类型 (例如: "ped_alarm")
- server_url: 服务器地址 (例如: "http://192.168.0.6:8000")
- c_sn: 相机序列号 (例如: "CA500-MIPI-zlxc-0059")
- u_sn: 单元序列号 (例如: "MS500-H120-EP-zlcu-0059")
- u_url: 设备 URL (可选，默认: "127.0.0.1")
"""

import os
import json


#------------------  全局配置缓存  ------------------

_config_cache = None


#------------------  配置文件路径  ------------------

def get_config_path():
    """获取配置文件的绝对路径"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'as_ms500_config.json')


#------------------  读取配置文件  ------------------

def load_config(force_reload=False):
    """
    从 as_ms500_config.json 读取配置参数

    参数:
        force_reload: 是否强制重新加载配置（默认 False，使用缓存）

    返回:
        dict: 配置字典

    异常:
        RuntimeError: 配置文件不存在或读取失败
    """
    global _config_cache

    # 如果有缓存且不强制重载，直接返回缓存
    if _config_cache is not None and not force_reload:
        return _config_cache

    config_path = get_config_path()

    if not os.path.exists(config_path):
        raise RuntimeError(f"Configuration file does not exist: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 缓存配置
        _config_cache = config
        return config

    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse configuration file: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to read configuration file: {e}")


#------------------  获取单个配置参数  ------------------

def get_port():
    """获取串口号"""
    config = load_config()
    return config.get('PORT', 'COM4')


def get_bin_type():
    """获取固件类型"""
    config = load_config()
    return config.get('BIN_TYPE', 'ped_alarm')


def get_model_type():
    """获取模型类型"""
    config = load_config()
    return config.get('MODEL_TYPE', 'ped_alarm')


def get_server_url():
    """获取服务器地址"""
    config = load_config()
    server_url = config.get('server_url', '').strip()
    if not server_url:
        raise RuntimeError("Configuration parameter missing: server_url")
    return server_url


def get_c_sn():
    """获取相机序列号"""
    config = load_config()
    c_sn = config.get('c_sn', '').strip()
    if not c_sn:
        raise RuntimeError("Configuration parameter missing: c_sn")
    return c_sn


def get_u_sn():
    """获取单元序列号"""
    config = load_config()
    u_sn = config.get('u_sn', '').strip()
    if not u_sn:
        raise RuntimeError("Configuration parameter missing: u_sn")
    return u_sn


def get_u_url():
    """获取设备 URL（可选参数）"""
    config = load_config()
    return config.get('u_url', '127.0.0.1')


#------------------  获取所有配置参数  ------------------

def get_all_config():
    """
    获取所有配置参数

    返回:
        dict: 包含所有配置参数的字典
    """
    return load_config()


#------------------  打印配置信息  ------------------

def print_config():
    """打印当前配置信息（用于调试）"""
    config = load_config()

    print("-" * 60)
    print("  MS500 Configuration")
    print("-" * 60)
    print(f"PORT:        {config.get('PORT', 'COM4')}")
    print(f"BIN_TYPE:    {config.get('BIN_TYPE', 'ped_alarm')}")
    print(f"MODEL_TYPE:  {config.get('MODEL_TYPE', 'ped_alarm')}")
    print(f"server_url:  {config.get('server_url', '')}")
    print(f"c_sn:        {config.get('c_sn', '')}")
    print(f"u_sn:        {config.get('u_sn', '')}")
    print(f"u_url:       {config.get('u_url', '127.0.0.1')}")
    print("-" * 60)


#------------------  测试代码  ------------------

if __name__ == "__main__":
    # 测试配置读取
    try:
        print("\nTest individual parameter retrieval:")
        print(f"PORT = {get_port()}")
        print(f"BIN_TYPE = {get_bin_type()}")
        print(f"MODEL_TYPE = {get_model_type()}")
        print(f"server_url = {get_server_url()}")
        print(f"c_sn = {get_c_sn()}")
        print(f"u_sn = {get_u_sn()}")
        print(f"u_url = {get_u_url()}")

    except Exception as e:
        print(f"Error: {e}")
