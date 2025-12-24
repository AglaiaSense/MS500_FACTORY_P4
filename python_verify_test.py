#!/usr/bin/env python3
"""
Python 环境验证测试脚本

功能说明:
测试项目的 Python 虚拟环境是否正确配置，包括：
1. .venv 虚拟环境目录是否存在
2. Python 解释器是否存在
3. esptool 工具是否存在
4. NVS 工具是否存在
5. FAT 文件系统工具是否存在

使用方法:
    python python_verify_test.py

如果环境配置正确，会显示成功信息。
如果环境配置有问题，会显示详细的错误信息和解决方案。
"""

import sys
import os

# 导入环境验证工具
from esp_components import (
    verify_all_tools,
    verify_python_environment,
    verify_nvs_tools,
    verify_fatfs_tools,
    get_esp_idf_python,
    get_esptool,
    get_nvs_tool_path,
    get_fatfs_gen_tool,
)


def main():
    """主函数 - 执行环境验证测试"""
    print("-" * 60)
    print("  Python 环境验证测试")
    print("-" * 60)
    print()

    try:
        # 显示配置的工具路径
        print("配置的工具路径:")
        print(f"  Python 解释器: {get_esp_idf_python()}")
        print(f"  esptool 工具: {get_esptool()}")
        print(f"  NVS 工具: {get_nvs_tool_path()}")
        print(f"  FAT 生成工具: {get_fatfs_gen_tool()}")
        print()

        # 执行环境验证
        print("-" * 60)
        print("  开始验证环境...")
        print("-" * 60)
        print()

        # 分步验证
        print("步骤 1: 验证 Python 虚拟环境...")
        verify_python_environment()
        print("  ✓ Python 虚拟环境验证成功")
        print()

        print("步骤 2: 验证 NVS 工具...")
        verify_nvs_tools()
        print("  ✓ NVS 工具验证成功")
        print()

        print("步骤 3: 验证 FAT 文件系统工具...")
        verify_fatfs_tools()
        print("  ✓ FAT 文件系统工具验证成功")
        print()

        # 综合验证
        print("-" * 60)
        print("  综合验证")
        print("-" * 60)
        verify_all_tools()
        print()

        # 显示成功信息
        print("-" * 60)
        print("  验证结果")
        print("-" * 60)
        print()
        print("✓✓✓ 所有环境检查通过！")
        print()
        print("您的环境配置正确，可以正常使用以下功能：")
        print("  - 设备注册和 NVS 烧录")
        print("  - 固件烧录")
        print("  - AI 模型部署")
        print()
        print("下一步:")
        print("  - 运行 main.py 开始工厂生产流程")
        print("  - 运行 as_factory_model.py 单独部署 AI 模型")
        print("  - 运行 as_flash_firmware/as_firmware_tool.py 单独烧录固件")
        print()
        print("-" * 60)

        return 0

    except RuntimeError as e:
        # 环境验证失败
        print()
        print("-" * 60)
        print("  验证失败")
        print("-" * 60)
        print()
        print("✗✗✗ 环境配置有问题！")
        print()
        print("错误详情:")
        print("-" * 60)
        print(str(e))
        print("-" * 60)
        print()
        print("请按照上面的解决方法修复环境配置后重试。")
        print()
        print("更多帮助请查看: PYTHON_ENV_SETUP.md")
        print("-" * 60)

        return 1

    except Exception as e:
        # 其他未预期的错误
        print()
        print("-" * 60)
        print("  发生未预期的错误")
        print("-" * 60)
        print()
        print(f"错误信息: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("-" * 60)

        return 1


if __name__ == "__main__":
    sys.exit(main())
