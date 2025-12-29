"""
ESP-IDF 工具路径配置模块
统一管理所有 ESP-IDF 相关工具的路径和配置，以及统一的命令执行函数
"""

import os
from pathlib import Path

# 获取esp_components目录的绝对路径
ESP_COMPONENTS_DIR = Path(__file__).parent.absolute()

# 获取项目根目录
PROJECT_ROOT = ESP_COMPONENTS_DIR.parent

# ========== ESP-IDF 工具路径配置 ==========

# ESP-IDF Python 环境路径（使用项目根目录的.venv虚拟环境）
ESP_IDF_PYTHON = str(PROJECT_ROOT / ".venv" / "Scripts" / "python.exe")

# ESP-IDF NVS 工具路径（使用本地工具）
NVS_TOOL_PATH = str(ESP_COMPONENTS_DIR / "nvs_tools" / "nvs_tool.py")

# FAT 文件系统镜像生成工具路径（使用本地工具）
FATFS_GEN_TOOL = str(ESP_COMPONENTS_DIR / "fatfs_tools" / "wl_fatfsgen.py")

# ESP32 烧录工具（使用 Python 模块方式调用，避免 Windows WinError 2）
# 注意：返回列表格式 [python.exe, -m, esptool]
ESPTOOL = [str(PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"), "-m", "esptool"]

# 使用 ESP-IDF 的 NVS 分区生成模块（仅用于生成 BIN）
NVS_GEN_MODULE = "esp_idf_nvs_partition_gen"

# 默认串口波特率配置
# BAUD_RATE = "460800"
BAUD_RATE = "115200"


# ========== 工具获取函数 ==========

def get_esp_idf_python():
    """获取 ESP-IDF Python 环境路径"""
    return ESP_IDF_PYTHON


def get_nvs_tool_path():
    """获取 NVS 工具路径（本地esp_components版本）"""
    return NVS_TOOL_PATH


def get_fatfs_gen_tool():
    """获取 FATFS 生成工具路径（本地esp_components版本）"""
    return FATFS_GEN_TOOL


def get_esptool():
    """
    获取 esptool 命令（返回列表格式）

    返回:
        list: [python.exe, -m, esptool] 格式的命令列表

    注意:
        返回的是列表，使用时需要扩展：
        cmd = get_esptool() + ["--port", "COM4", ...]
        或
        cmd = [*get_esptool(), "--port", "COM4", ...]
    """
    return ESPTOOL


def get_nvs_gen_module():
    """获取 NVS 分区生成模块名称"""
    return NVS_GEN_MODULE


def get_baud_rate():
    """获取默认串口波特率"""
    return BAUD_RATE


# ========== 串口测试函数 ==========

def test_port_connection(port):
    """
    测试串口连接并读取芯片信息

    参数:
        port: 串口号（例如：COM4, /dev/ttyUSB0）

    返回:
        连接成功返回 True，失败返回 False

    异常:
        连接失败时抛出 RuntimeError
    """
    print("\n" + "=" * 60)
    print("步骤2: 测试串口连接")
    print("-" * 60)

    cmd = [*ESPTOOL, "--port", port, "chip_id"]
    result = run_command(cmd)

    if result.returncode != 0:
        print("\n" + "!" * 60)
        print("错误: 无法连接到设备")
        print("!" * 60)
        print("\n请检查:")
        print(f"  1. 设备是否正确连接到 {port}")
        print("   2. COM 端口号是否正确")
        print("   3. 设备是否处于下载模式（Bootloader）")
        print("   4. 串口是否被其他程序占用")

        # 打印详细错误信息
        print("\n" + "-" * 60)
        print("详细错误信息:")
        print("-" * 60)
        if result.stdout.strip():
            print(result.stdout)
        if result.stderr.strip():
            print(result.stderr)
        else:
            print("(无错误详情)")
        print("-" * 60)

        raise RuntimeError("串口连接失败")

    # 打印连接成功信息
    for line in result.stdout.splitlines():
        if "Detecting chip type" in line or "Chip is" in line or "MAC:" in line:
            print(f"  {line.strip()}")

    print("\n✓ 串口连接测试成功")

    return True


# ========== 命令执行函数 ==========

def run_command(cmd, capture_output=True, text=True, print_cmd=True, timeout=None, realtime_output=False, **kwargs):
    """
    统一的命令执行函数

    参数:
        cmd: 命令列表 (例如: [ESPTOOL, "--port", "COM4", "read_mac"])
        capture_output: 是否捕获输出 (默认 True，当 realtime_output=True 时自动设置为 False)
        text: 是否以文本模式输出 (默认 True)
        print_cmd: 是否打印命令 (默认 True)
        timeout: 超时时间（秒）
        realtime_output: 是否实时输出命令执行过程 (默认 False)
        **kwargs: 其他传递给 subprocess.run 的参数

    返回:
        subprocess.CompletedProcess 对象
        注意: 当 realtime_output=True 时，stdout 和 stderr 将为空字符串
    """
    import subprocess
    import sys

    if print_cmd:
        print(f"执行命令: {' '.join(cmd)}")

    # 实时输出模式
    if realtime_output:
        # 实时模式下，stdout/stderr 重定向到控制台，不捕获输出
        process = subprocess.Popen(
            cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=text,
            **kwargs
        )

        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise

        # 返回与 subprocess.run 兼容的结果对象
        # 注意: 实时模式下 stdout 和 stderr 为空
        class CompletedProcess:
            def __init__(self, args, returncode):
                self.args = args
                self.returncode = returncode
                self.stdout = ""
                self.stderr = ""

        return CompletedProcess(cmd, returncode)

    # 传统捕获模式
    return subprocess.run(
        cmd,
        capture_output=capture_output,
        text=text,
        timeout=timeout,
        **kwargs
    )


def run_command_with_error_check(cmd, error_message="命令执行失败", print_cmd=True, **kwargs):
    """
    执行命令并检查返回码，失败时抛出异常

    参数:
        cmd: 命令列表
        error_message: 错误消息
        print_cmd: 是否打印命令
        **kwargs: 其他传递给 run_command 的参数

    返回:
        subprocess.CompletedProcess 对象

    异常:
        RuntimeError: 命令执行失败时抛出
    """
    result = run_command(cmd, print_cmd=print_cmd, **kwargs)

    if result.returncode != 0:
        error_details = []
        if result.stdout and result.stdout.strip():
            error_details.append(f"STDOUT: {result.stdout}")
        if result.stderr and result.stderr.strip():
            error_details.append(f"STDERR: {result.stderr}")

        full_error = f"{error_message}\n" + "\n".join(error_details) if error_details else error_message
        raise RuntimeError(full_error)

    return result


# ========== 工具验证函数 ==========

def verify_python_environment():
    """
    验证 Python 虚拟环境是否正确配置

    检查项:
        1. .venv 目录是否存在
        2. python.exe 是否存在
        3. esptool.exe 是否存在

    Returns:
        bool: 环境验证成功返回 True

    Raises:
        RuntimeError: 环境验证失败时抛出，包含详细错误信息
    """
    errors = []

    # 检查 .venv 目录
    venv_dir = PROJECT_ROOT / ".venv"
    if not venv_dir.exists():
        errors.append(f"虚拟环境目录不存在: {venv_dir}")
        errors.append("\n解决方法:")
        errors.append("  1. 在项目根目录创建虚拟环境:")
        errors.append("     python -m venv .venv")
        errors.append("  2. 安装项目依赖:")
        errors.append("     .venv\\Scripts\\activate")
        errors.append("     pip install -r requirements.txt")
        errors.append("\n详细说明请查看: PYTHON_ENV_SETUP.md")
        raise RuntimeError("\n".join(errors))

    # 检查 Python 解释器
    if not os.path.exists(ESP_IDF_PYTHON):
        errors.append(f"Python 解释器不存在: {ESP_IDF_PYTHON}")
        errors.append("\n解决方法:")
        errors.append("  虚拟环境可能损坏，请重新创建:")
        errors.append("  1. 删除 .venv 目录")
        errors.append("  2. python -m venv .venv")
        errors.append("  3. .venv\\Scripts\\activate")
        errors.append("  4. pip install -r requirements.txt")
        raise RuntimeError("\n".join(errors))

    # 检查 esptool（验证 Python 模块是否已安装）
    # ESPTOOL 现在是列表格式 [python.exe, -m, esptool]
    import subprocess
    try:
        result = subprocess.run(
            [*ESPTOOL, "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            raise RuntimeError("esptool 模块未正确安装")
    except (FileNotFoundError, subprocess.TimeoutExpired, RuntimeError):
        errors.append(f"esptool 工具未安装或无法运行")
        errors.append("\n解决方法:")
        errors.append("  1. 激活虚拟环境: .venv\\Scripts\\activate")
        errors.append("  2. 安装依赖: pip install -r requirements.txt")
        errors.append("  3. 验证安装: python -m esptool version")
        raise RuntimeError("\n".join(errors))

    return True


def verify_nvs_tools():
    """
    验证 NVS 工具是否存在

    Returns:
        bool: 工具验证成功返回 True

    Raises:
        RuntimeError: 工具验证失败时抛出
    """
    if not os.path.exists(NVS_TOOL_PATH):
        raise RuntimeError(
            f"NVS 工具不存在: {NVS_TOOL_PATH}\n"
            f"请检查 esp_components/nvs_tools/ 目录是否完整"
        )
    return True


def verify_fatfs_tools():
    """
    验证 FAT 文件系统工具是否存在

    Returns:
        bool: 工具验证成功返回 True

    Raises:
        RuntimeError: 工具验证失败时抛出
    """
    if not os.path.exists(FATFS_GEN_TOOL):
        raise RuntimeError(
            f"FAT 生成工具不存在: {FATFS_GEN_TOOL}\n"
            f"请检查 esp_components/fatfs_tools/ 目录是否完整"
        )
    return True


def verify_all_tools():
    """
    验证所有必需工具

    在程序开始时调用此函数，确保所有工具都已正确配置

    Returns:
        bool: 所有工具验证成功返回 True

    Raises:
        RuntimeError: 任何工具验证失败时抛出
    """
    verify_python_environment()
    verify_nvs_tools()
    verify_fatfs_tools()
    print("✓ 环境验证成功: 所有工具已正确配置")
    return True

