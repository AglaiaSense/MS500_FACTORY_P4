# MS500 工厂生产脚本

本手册提供 MS500-EP 摄像头设备生产出货的完整操作指南，适用于工厂操作人员和技术人员。

---

## 项目下载

**GitHub 仓库地址：**

```
https://github.com/AglaiaSense/MS500_FACTORY_P4.git
```

**克隆项目：**

```bash
git clone https://github.com/AglaiaSense/MS500_FACTORY_P4.git
cd MS500_FACTORY_P4
```

---

## 目录

1. [从零创建虚拟环境](#1-从零创建虚拟环境)
2. [运行工厂生产流程](#2-运行工厂生产流程)
3. [修改配置文件](#3-修改配置文件)

---

## 1. 从零创建虚拟环境

如果项目中不存在 `.venv` 虚拟环境，或需要重新创建环境，请按照以下步骤操作。

### 1.1 前提条件

#### 安装 Python 3.12.x

1. 访问 Python 官网：https://www.python.org/downloads/
2. 下载 Python 3.12.x 版本（例如：3.12.6）
3. 运行安装程序
4. **重要**：勾选 "Add Python to PATH"
5. 点击 "Install Now" 完成安装

#### 验证 Python 安装

打开命令行（CMD 或 PowerShell），运行：

```bash
python --version
```

应该显示类似：`Python 3.12.6`

### 1.2 创建虚拟环境步骤

#### 步骤 1: 进入项目目录

```bash
# 使用 cd 命令进入项目根目录
cd MS500_Factory_P4
```

#### 步骤 2: 创建虚拟环境

```bash
python -m venv .venv
```

执行后，会在项目根目录创建 `.venv` 文件夹。

#### 步骤 3: 激活虚拟环境

**Windows CMD:**
```cmd
.venv\Scripts\activate
```

**Windows PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

激活成功后，命令行前缀会显示 `(.venv)`：

```
(.venv) MS500_Factory_P4>
```

#### 步骤 4: 升级 pip

```bash
python -m pip install --upgrade pip
```

#### 步骤 5: 安装项目依赖

```bash
pip install -r requirements.txt
```

安装过程可能需要 5-10 分钟，请耐心等待。

**如果网络较慢，可以使用国内镜像源：**

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 步骤 6: 验证安装

```bash
# 检查 esptool 版本
esptool version

# 检查已安装的包
pip list
```

如果看到 `esptool 4.10.0` 等输出，说明安装成功。

### 1.3 常见问题处理

#### 问题 1: PowerShell 执行策略错误

**错误信息：**
```
无法加载文件 .venv\Scripts\Activate.ps1，因为在此系统上禁止运行脚本。
```

**解决方法：**

以管理员身份运行 PowerShell，执行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

然后重新激活虚拟环境。

#### 问题 2: pip 安装超时

**解决方法：**

使用国内镜像源（如清华镜像）：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 问题 3: cryptography 安装失败

**错误信息：**
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**解决方法：**

1. 访问：https://visualstudio.microsoft.com/downloads/
2. 下载 "Visual Studio Build Tools"
3. 安装时选择 "Desktop development with C++"
4. 安装完成后重新运行 `pip install -r requirements.txt`

#### 问题 4: 找不到 esptool 命令

**解决方法：**

1. 确认虚拟环境已激活（命令行显示 `(.venv)`）
2. 重新安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 验证：
   ```bash
   pip show esptool
   ```

### 1.4 退出虚拟环境

完成工作后，退出虚拟环境：

```bash
deactivate
```

---

## 2. 运行工厂生产流程

本节介绍如何运行完整的工厂生产流程和各个独立模块。

### 2.1 准备工作

#### 2.1.1 连接设备

1. 将MS500-EP设备通过串口线接到电脑
2. 确认设备电源正常
3. 查看设备管理器，确认串口号（例如：COM4）

**Windows 查看串口号：**
- 打开"设备管理器"
- 展开"端口（COM 和 LPT）"
  - 找到对应的串口号（例如：USB-SERIAL CH340 (COM4)）


**Linux/Mac 查看串口号：**
```bash
ls /dev/ttyUSB*
# 或
ls /dev/ttyACM*
```

#### 2.1.2 准备固件文件

将固件文件放入对应目录：

```
as_flash_firmware/bin_type/{BIN_TYPE}/
├── bootloader.bin
├── ms500_p4.bin
├── partition-table.bin
├── partitions.csv
├── ota_data_initial.bin
└── storage.bin
```

例如，如果 `BIN_TYPE` 为 `ped_alarm`，则文件路径为：
```
as_flash_firmware/bin_type/ped_alarm/
```

#### 2.1.3 准备模型文件

将 AI 模型文件放入对应目录：

```
as_model_conversion/type_model/{MODEL_TYPE}/
├── packerOut.zip
└── network_info.txt
```

例如，如果 `MODEL_TYPE` 为 `ped_alarm`，则文件路径为：
```
as_model_conversion/type_model/ped_alarm/
```

#### 2.1.4 配置参数

编辑 `as_ms500_config.json` 文件（详见[第 3 节](#3-修改配置文件)）。

### 2.2 激活虚拟环境

在运行任何程序之前，必须先激活虚拟环境：

**Windows CMD:**
```cmd
.venv\Scripts\activate
```

**Windows PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 2.3 运行完整工厂生产流程（推荐）

完整流程包括：参数注册、固件烧录、模型烧录。

```bash
python main.py
```

**执行步骤：**

```
步骤 1/3: 参数注册（NVS 烧录）
  ├─ 读取设备 MAC 地址
  ├─ 检查现有 NVS 数据
  ├─ 向服务器注册设备
  ├─ 生成 NVS 数据
  └─ 烧录 NVS 到设备

步骤 2/3: 固件烧录
  ├─ 读取固件文件
  ├─ 解析分区表
  └─ 烧录固件到设备

步骤 3/3: 模型烧录
  ├─ 读取 device_id
  ├─ 生成加密模型
  ├─ 创建 FAT 镜像
  ├─ 烧录模型到设备
  └─ 更新 NVS 标志并重启
```

**预期输出：**

```
MS500 Factory Production Program
Port: COM4
Firmware Type: ped_alarm
Model Type: ped_alarm

Enabled Steps: 参数注册 -> 固件烧录 -> 模型烧录

================================================================================
【步骤 1/3】 参数注册（NVS 烧录）
================================================================================
...
✓ 步骤 1 完成: 参数注册成功

================================================================================
【步骤 2/3】 固件烧录
================================================================================
...
✓ 步骤 2 完成: 固件烧录成功

================================================================================
【步骤 3/3】 模型烧录
================================================================================
...
✓ 步骤 3 完成: 模型烧录成功

================================================================================
  ✓ 工厂生产流程完成
================================================================================
```

### 2.4 单独运行各模块

如果只需要执行某个特定步骤，可以单独运行对应模块。

#### 2.4.1 仅固件烧录

```bash
python as_factory_firmware.py
```

**用途：**
- 更新设备固件
- 不修改 NVS 数据
- 不烧录模型

#### 2.4.2 仅设备注册和 NVS 烧录

```bash
python as_factory_info.py
```

**用途：**
- 向服务器注册新设备
- 生成并烧录 NVS 数据
- 不烧录固件和模型

#### 2.4.3 仅模型烧录

```bash
python as_factory_model.py
```

**用途：**
- 更新 AI 模型
- 不修改固件和 NVS（除模型标志外）

**前提条件：**
- 设备必须已注册（NVS 中包含 `g_camera_id`）

### 2.5 控制执行步骤

如果需要跳过某些步骤，可以编辑 `main.py` 中的控制开关：

```python
# 在 main.py 第 40-42 行
ENABLE_STEP1_REGISTER = True   # 步骤1: 参数注册（NVS 烧录）
ENABLE_STEP2_FIRMWARE = True   # 步骤2: 固件烧录
ENABLE_STEP3_MODEL = True      # 步骤3: 模型烧录
```

**示例：只烧录固件，跳过注册和模型**

```python
ENABLE_STEP1_REGISTER = False  # 跳过注册
ENABLE_STEP2_FIRMWARE = True   # 执行固件烧录
ENABLE_STEP3_MODEL = False     # 跳过模型烧录
```

然后运行：

```bash
python main.py
```

### 2.6 常见问题处理

#### 问题 1: 串口连接失败

**错误信息：**
```
Error: Cannot connect to device
```

**检查清单：**
- [ ] 设备是否正确连接
- [ ] 串口号是否正确（检查设备管理器）
- [ ] 设备是否处于下载模式
- [ ] 是否有其他程序占用串口（如串口监视器、IDE）
- [ ] USB 驱动是否安装

**手动进入下载模式：**
1. 按住 **Boot** 按钮不放
2. 短按 **Reset** 按钮
3. 释放 **Boot** 按钮
4. 重新运行程序

#### 问题 2: 服务器注册失败

**错误信息：**
```
Camera SN already registered
```

**解决方法：**

在 `as_ms500_config.json` 中修改 `c_sn` 为新的唯一序列号：

```json
{
  "c_sn": "CA500-MIPI-zlxc-0060",  // 修改为新序列号
  "u_sn": "MS500-H120-EP-zlcu-0060"
}
```

#### 问题 3: 模型烧录失败

**错误信息：**
```
g_camera_id not found
```

**解决方法：**

设备必须先上电启动运行过程序，才能将camera_id保存到flash中，执行：

```bash
python as_factory_firmware.py
```

上电启动，会有camera_id打印。然后再运行模型烧录。

#### 问题 4: NVS 数据为空

**错误信息：**
```
Warning: NVS partition is empty (all 0xFF)
```

**说明：**

这是正常的，表示设备是新设备或 NVS 未烧录过。继续执行注册流程即可。

#### 问题 5: 固件文件不存在

**错误信息：**
```
Error: Firmware file not found: as_flash_firmware/bin_type/ped_alarm/bootloader.bin
```

**解决方法：**

1. 检查固件文件是否存在于对应目录
2. 确认 `BIN_TYPE` 配置与目录名称一致
3. 确保所有必需的固件文件都已准备好

---

## 3. 修改配置文件

所有配置参数集中在 `as_ms500_config.json` 文件中管理。

### 3.1 配置文件准备（首次使用必读）

**首次使用本系统时，需要从模板文件创建配置文件：**

#### Windows CMD:
```cmd
copy as_ms500_config.json.template as_ms500_config.json
```

#### Windows PowerShell:
```powershell
Copy-Item as_ms500_config.json.template as_ms500_config.json
```

#### Linux/Mac:
```bash
cp as_ms500_config.json.template as_ms500_config.json
```

**文件说明：**

| 文件名 | 用途 | Git 管理 |
|--------|------|----------|
| `as_ms500_config.json.template` | 配置模板文件，包含配置示例 | ✅ 提交到 Git |
| `as_ms500_config.json` | 实际使用的配置文件，包含真实参数 | ❌ 不提交（.gitignore） |

**设计原因：**
- 模板文件提供配置参数示例，方便新用户快速上手
- 实际配置文件不提交到 Git，避免敏感信息（服务器地址、序列号等）泄露
- 每个环境（开发、测试、生产）可以使用不同的配置，互不干扰

### 3.2 配置文件位置

```
MS500_Factory_P4/
├── as_ms500_config.json.template  # 配置模板（提交到 Git）
└── as_ms500_config.json          # 实际配置（不提交到 Git）
```

### 3.3 配置文件格式

```json
{
  "server_url": "http://192.168.0.6:8000",
  "c_sn": "CA500-MIPI-zlxc-0059",
  "u_sn": "MS500-H120-EP-zlcu-0059",
  "PORT": "COM4",
  "BIN_TYPE": "ped_alarm",
  "MODEL_TYPE": "ped_alarm"
}
```

### 3.4 配置参数说明

#### 3.4.1 server_url（服务器地址）

**说明：** 设备管理服务器的 URL 地址

**格式：** `http://IP:端口`

**示例：**
```json
"server_url": "http://192.168.0.6:8000"
```

**注意：**
- 根据服务器出厂进行修改，出厂要使用正式服务器
- 端口号通常为 `8000`
- 确保服务器可访问

#### 3.4.2 c_sn（相机序列号）

**说明：** 相机的唯一序列号，用于服务器注册

**格式：** `CA500-MIPI-{标识}-{编号}`

**示例：**
```json
"c_sn": "CA500-MIPI-zlxc-0059"
```

**注意：**
- **必须全局唯一**，不能重复
- 每台设备烧录前需要修改此参数
- 建议使用流水号管理（如：0001、0002、0003...）

#### 3.4.3 u_sn（单元序列号）

**说明：** 单元的唯一序列号，用于服务器注册

**格式：** `MS500-H120-EP-{标识}-{编号}`

**示例：**
```json
"u_sn": "MS500-H120-EP-zlcu-0059"
```

**注意：**
- **必须全局唯一**，不能重复
- 通常与 `c_sn` 的编号保持一致
- 用于生成设备密码（`MS` + MD5(u_sn)[:6] + `!`）

#### 3.4.4 PORT（串口号）

**说明：** 设备连接的串口号

**Windows 格式：** `COM{数字}`

**Linux/Mac 格式：** `/dev/ttyUSB{数字}` 或 `/dev/ttyACM{数字}`

**示例：**
```json
// Windows
"PORT": "COM4"

// Linux
"PORT": "/dev/ttyUSB0"

// Mac
"PORT": "/dev/ttyACM0"
```

**如何查找串口号：**

**Windows：**
1. 打开"设备管理器"
2. 展开"端口（COM 和 LPT）"
3. 查看串口号（例如：USB Serial Port (COM4)）

**Linux/Mac：**
```bash
ls /dev/ttyUSB*
# 或
ls /dev/ttyACM*
```

#### 3.4.5 BIN_TYPE（固件类型）

**说明：** 指定要烧录的固件类型，对应 `as_flash_firmware/bin_type/` 目录下的子目录名

**可选值：**
- `ped_alarm` - 行人检测固件
- `sdk_uvc_tw_plate` - 台湾车牌识别固件
- 其他自定义固件类型

**示例：**
```json
"BIN_TYPE": "ped_alarm"
```

**对应目录结构：**
```
as_flash_firmware/bin_type/
├── ped_alarm/           <-- BIN_TYPE = "ped_alarm"
│   ├── bootloader.bin
│   ├── ms500_p4.bin
│   └── ...
└── sdk_uvc_tw_plate/    <-- BIN_TYPE = "sdk_uvc_tw_plate"
    ├── bootloader.bin
    └── ...
```

#### 3.4.6 MODEL_TYPE（模型类型）

**说明：** 指定要烧录的 AI 模型类型，对应 `as_model_conversion/type_model/` 目录下的子目录名

**可选值：**
- `ped_alarm` - 行人检测模型
- `sdk_uvc_tw_plate` - 台湾车牌识别模型
- 其他自定义模型类型

**示例：**
```json
"MODEL_TYPE": "ped_alarm"
```

**对应目录结构：**
```
as_model_conversion/type_model/
├── ped_alarm/              <-- MODEL_TYPE = "ped_alarm"
│   ├── packerOut.zip
│   └── network_info.txt
└── sdk_uvc_tw_plate/       <-- MODEL_TYPE = "sdk_uvc_tw_plate"
    ├── packerOut.zip
    └── network_info.txt
```

### 3.5 配置修改示例

#### 示例 1: 修改串口号

**场景：** 设备连接到 COM5

**修改前：**
```json
{
  "PORT": "COM4"
}
```

**修改后：**
```json
{
  "PORT": "COM5"
}
```

#### 示例 2: 更换固件和模型类型

**场景：** 从行人检测切换到车牌识别

**修改前：**
```json
{
  "BIN_TYPE": "ped_alarm",
  "MODEL_TYPE": "ped_alarm"
}
```

**修改后：**
```json
{
  "BIN_TYPE": "sdk_uvc_tw_plate",
  "MODEL_TYPE": "sdk_uvc_tw_plate"
}
```

#### 示例 3: 批量生产设备序列号管理

**场景：** 生产第 60、61、62 台设备

**设备 1：**
```json
{
  "c_sn": "CA500-MIPI-zlxc-0060",
  "u_sn": "MS500-H120-EP-zlcu-0060"
}
```

**设备 2：**
```json
{
  "c_sn": "CA500-MIPI-zlxc-0061",
  "u_sn": "MS500-H120-EP-zlcu-0061"
}
```

**设备 3：**
```json
{
  "c_sn": "CA500-MIPI-zlxc-0062",
  "u_sn": "MS500-H120-EP-zlcu-0062"
}
```

### 3.6 配置验证

修改配置后，可以运行以下命令验证配置是否正确：

```bash
python as_ms500_config.py
```

**预期输出：**
```
------------------------------------------------------------
  MS500 Configuration
------------------------------------------------------------
PORT:        COM4
BIN_TYPE:    ped_alarm
MODEL_TYPE:  ped_alarm
server_url:  http://192.168.0.6:8000
c_sn:        CA500-MIPI-zlxc-0059
u_sn:        MS500-H120-EP-zlcu-0059
u_url:       127.0.0.1
------------------------------------------------------------
```

### 3.7 配置文件最佳实践

#### 1. 序列号管理

建议使用 Excel 或数据库管理序列号分配，避免重复：

| 设备编号 | c_sn | u_sn | 烧录日期 | 操作员 |
|---------|------|------|----------|--------|
| 0059 | CA500-MIPI-zlxc-0059 | MS500-H120-EP-zlcu-0059 | 2025-12-25 | 张三 |
| 0060 | CA500-MIPI-zlxc-0060 | MS500-H120-EP-zlcu-0060 | 2025-12-25 | 张三 |

#### 2. 配置备份

每次修改配置前，建议备份：

```bash
# Windows
copy as_ms500_config.json as_ms500_config.json.backup

# Linux/Mac
cp as_ms500_config.json as_ms500_config.json.backup
```

---

## 附录

### A. 完整命令参考

#### 虚拟环境命令
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 激活虚拟环境 (Linux/Mac)
source .venv/bin/activate

# 退出虚拟环境
deactivate

# 安装依赖
pip install -r requirements.txt

# 升级 pip
python -m pip install --upgrade pip
```

#### 工厂生产命令
```bash
# 完整流程
python main.py

# 单独烧录固件
python as_factory_firmware.py

# 单独注册设备
python as_factory_info.py

# 单独烧录模型
python as_factory_model.py

# 验证配置
python as_ms500_config.py

# 环境验证测试
python python_verify_test.py.py
```

### B. 目录结构速查

```
MS500_Factory_P4/
├── .venv/                           # 虚拟环境
├── as_ms500_config.json             # 配置文件 ⭐
├── as_ms500_config.py               # 配置读取模块
├── main.py                          # 主程序 ⭐
├── as_factory_firmware.py           # 固件烧录 ⭐
├── as_factory_info.py               # 设备注册 ⭐
├── as_factory_model.py              # 模型烧录 ⭐
├── README.md                        # 项目说明
├── CLAUDE.md                        # 项目架构文档
├── docs/                            # 文档目录 📚
│   ├── task.md                      # 任务清单
│   ├── OPERATION_MANUAL.md          # 本操作手册
│   └── PYTHON_ENV_SETUP.md          # 虚拟环境配置指南
├── as_flash_firmware/bin_type/      # 固件文件目录 📁
└── as_model_conversion/type_model/  # 模型文件目录 📁
```

### C. 故障排查清单

遇到问题时，按以下顺序检查：

- [ ] 虚拟环境是否激活（命令行显示 `(.venv)`）
- [ ] Python 版本是否为 3.12.x
- [ ] 依赖是否完整安装（`pip list` 检查）
- [ ] 配置文件是否正确（`python as_ms500_config.py`）
- [ ] 设备是否正确连接（设备管理器或 `ls /dev/ttyUSB*`）
- [ ] 串口号是否正确
- [ ] 固件文件是否存在
- [ ] 模型文件是否存在
- [ ] 服务器是否可访问
- [ ] 序列号是否唯一

### D. 联系支持

如遇到本手册未涵盖的问题，请联系技术支持团队。

**相关文档：**
- 项目架构：`CLAUDE.md`
- 虚拟环境：`PYTHON_ENV_SETUP.md`
- 项目说明：`README.md`

---

**文档版本：** 1.0
**更新日期：** 2025-12-25
**适用系统：** MS500 Factory Production System
