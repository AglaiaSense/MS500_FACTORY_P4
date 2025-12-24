# Python 虚拟环境配置指南

## 概述

本项目使用位于项目根目录的 `.venv` 虚拟环境，包含所有必需的 ESP32-P4 开发工具和依赖库。

**虚拟环境路径**: `.venv` (项目根目录)

**Python 版本要求**: 3.12.x

---

## 快速开始

### 1. 激活现有虚拟环境

项目中已包含配置好的 `.venv` 虚拟环境，直接激活即可使用：

#### Windows CMD
```cmd
.venv\Scripts\activate
```

#### Windows PowerShell
```powershell
.venv\Scripts\Activate.ps1
```

#### Linux/Mac
```bash
source .venv/bin/activate
```

### 2. 验证环境

激活后，验证工具是否正常：

```bash
# 检查 Python 版本
python --version

# 检查 esptool 版本
esptool version

# 查看已安装的包
pip list
```

---

## 从零创建虚拟环境

如果 `.venv` 目录不存在或需要重新创建，按以下步骤操作：

### 前提条件

- 安装 Python 3.12.x
- 下载地址：https://www.python.org/downloads/

### 步骤

#### 1. 创建虚拟环境

```bash
# 在项目根目录执行
python -m venv .venv
```

#### 2. 激活虚拟环境

```bash
# Windows CMD
.venv\Scripts\activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux/Mac
source .venv/bin/activate
```

#### 3. 升级 pip

```bash
python -m pip install --upgrade pip
```

#### 4. 安装项目依赖

```bash
pip install -r requirements.txt
```

#### 5. 验证安装

```bash
# 检查 esptool 版本
esptool version

# 检查已安装的包
pip list
```

---

## 虚拟环境中的核心工具

安装完成后，你将拥有以下 ESP-IDF 工具：

| 工具 | 版本 | 用途 |
|------|------|------|
| esptool | 4.10.0 | ESP32 固件烧录工具 |
| esp-idf-monitor | 1.8.0 | 串口监视器 |
| esp_idf_nvs_partition_gen | 0.1.9 | NVS 分区生成器 |
| esp-idf-kconfig | 2.5.0 | 配置管理 |
| esp-idf-size | 1.7.1 | 固件大小分析 |
| esp-coredump | 1.14.0 | 核心转储分析 |
| idf-component-manager | 2.4.2 | 组件管理器 |

---

## 项目使用示例

### 运行工厂生产流程

```bash
# 1. 激活虚拟环境
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 2. 运行完整工厂生产流程（注册 + 烧录）
python main.py

# 3. 单独烧录固件
python as_flash_firmware/as_firmware_tool.py

# 4. 单独部署 AI 模型
python as_factory_model.py

# 5. 设备注册（不烧录）
python as_service_register.py
```

---

## 项目架构说明

### ESP 组件系统

项目在 `esp_components/` 目录中统一管理 ESP-IDF 工具路径：

```
esp_components/
├── nvs_tools/              # NVS 分区工具
├── fatfs_tools/            # FAT 文件系统生成器
├── esp_tools.py            # 工具路径配置（指向 .venv）
└── __init__.py             # 导出统一接口
```

### 代码中使用虚拟环境

项目代码通过 `esp_components` 模块自动使用 `.venv` 环境：

```python
from esp_components import (
    get_esp_idf_python,    # 返回 .venv/Scripts/python.exe
    get_esptool,           # 返回 .venv/Scripts/esptool.exe
    get_nvs_tool_path,     # 返回 NVS 工具路径
    get_fatfs_gen_tool,    # 返回 FAT 生成器路径
)

# 示例：使用 Python 解释器路径
python_path = get_esp_idf_python()
# 结果：E:\03-MS500-P4\01.code\MS500_Factory_P4\.venv\Scripts\python.exe
```

**关键设计**：`esp_tools.py` 中配置了虚拟环境路径为 `.venv`，所有工具自动从该环境加载。

---

## 故障排查

### 问题 1: 激活脚本执行策略错误（PowerShell）

**错误信息**：
```
无法加载文件 .venv\Scripts\Activate.ps1，因为在此系统上禁止运行脚本。
```

**解决方法**：
```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题 2: pip 安装超时或失败

**解决方法**：使用国内镜像源
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 3: cryptography 安装失败

**原因**：缺少 C++ 编译器

**解决方法**：
1. 安装 Visual Studio Build Tools
2. 下载地址：https://visualstudio.microsoft.com/downloads/
3. 选择 "Desktop development with C++"

### 问题 4: 找不到 esptool 命令

**解决方法**：
1. 确认虚拟环境已激活（命令行前缀显示 `(.venv)`）
2. 重新安装依赖：`pip install -r requirements.txt`
3. 验证安装：`pip show esptool`

### 问题 5: Python 版本不匹配

**解决方法**：
1. 检查系统 Python 版本：`python --version`
2. 确保是 3.12.x 版本
3. 如果版本不对，安装 Python 3.12 后重新创建虚拟环境

---

## 退出虚拟环境

完成工作后，退出虚拟环境：

```bash
deactivate
```

---

## 注意事项

1. **虚拟环境位置**：`.venv` 位于项目根目录，所有项目代码自动引用此环境。

2. **版本要求**：必须使用 Python 3.12.x，其他版本可能导致依赖冲突。

3. **自包含工具链**：虚拟环境包含完整的 ESP-IDF 工具，无需单独安装 ESP-IDF。

4. **跨平台兼容**：虚拟环境在 Windows/Linux/Mac 上使用相同的 requirements.txt。

5. **Git 忽略**：`.venv` 目录应添加到 `.gitignore`，不提交到仓库。

6. **更新依赖**：如需更新依赖包，运行：
   ```bash
   pip install --upgrade -r requirements.txt
   ```

7. **重建环境**：如果环境损坏，删除 `.venv` 目录后重新创建：
   ```bash
   # Windows
   rmdir /s .venv
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt

   # Linux/Mac
   rm -rf .venv
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

---

## 依赖包说明

完整依赖列表见 `requirements.txt`，主要分类：

- **ESP-IDF 工具** (8 个包)：esptool、nvs_partition_gen、idf-monitor 等
- **ESP32 库** (6 个包)：pyelftools、bitstring、construct 等
- **串口通信** (1 个包)：pyserial
- **加密安全** (2 个包)：cryptography、ecdsa
- **HTTP 网络** (5 个包)：requests、urllib3 等
- **配置解析** (4 个包)：PyYAML、jsonref 等
- **Pydantic** (6 个包)：数据验证框架
- **CLI 工具** (7 个包)：click、rich、tqdm 等
- **开发调试** (3 个包)：pygdbmi、freertos-gdb 等
- **系统工具** (4 个包)：psutil、python-dotenv 等
- **构建工具** (7 个包)：cffi、packaging 等

总共 **53 个依赖包**，确保完整的 ESP32-P4 开发环境。

---

## 联系与支持

如遇到问题，请参考：
- 项目文档：`CLAUDE.md`
- 任务记录：`task.md`
- ESP-IDF 官方文档：https://docs.espressif.com/projects/esp-idf/
- Python venv 文档：https://docs.python.org/3/library/venv.html
