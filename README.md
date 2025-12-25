# MS500 工厂生产系统

MS500 ESP32-P4 摄像头设备的综合性工厂生产工具，用于设备注册、固件烧录和 AI 模型部署。

# 激活虚拟环境

```
.venv\Scripts\activate
```

## 项目概述

本系统提供完整的工厂生产流程，包括：
- 设备注册和 NVS 数据管理
- 固件烧录
- AI 模型转换和烧录

所有配置参数集中在 `as_ms500_config.json` 中管理，支持灵活配置。

## 快速开始

### 0. 配置文件准备

**首次使用时，需要从模板文件创建配置文件：**

```bash
# Windows CMD
copy as_ms500_config.json.template as_ms500_config.json

# Windows PowerShell
Copy-Item as_ms500_config.json.template as_ms500_config.json

# Linux/Mac
cp as_ms500_config.json.template as_ms500_config.json
```

**说明：**
- `as_ms500_config.json.template` 是配置模板文件，包含所有必需的配置参数示例
- `as_ms500_config.json` 是实际使用的配置文件，**不会提交到 Git 仓库**（已在 .gitignore 中配置）
- 这样设计可以避免敏感信息（如服务器地址、序列号等）被误提交到代码库

### 1. 配置参数

编辑 `as_ms500_config.json` 文件，设置必要的参数：

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

**参数说明：**
- `server_url`: 服务器地址
- `c_sn`: 相机序列号（全局唯一）
- `u_sn`: 单元序列号（全局唯一）
- `PORT`: 串口号（Windows: COM4, Linux: /dev/ttyUSB0）
- `BIN_TYPE`: 固件类型（对应 as_flash_firmware/bin_type/ 下的目录名）
- `MODEL_TYPE`: 模型类型（对应 as_model_conversion/type_model/ 下的目录名）

### 2. 准备固件和模型

**固件文件：**
将固件文件放在 `as_flash_firmware/bin_type/{BIN_TYPE}/` 目录下：
- `bootloader.bin`
- `ms500_p4.bin`
- `partition-table.bin`
- `partitions.csv`
- `ota_data_initial.bin`
- `storage.bin`

**模型文件：**
将模型文件放在 `as_model_conversion/type_model/{MODEL_TYPE}/` 目录下：
- `packerOut.zip`
- `network_info.txt`

### 3. 运行程序

#### 方式 1: 一键完整流程（推荐）

运行 `main.py` 执行完整的工厂生产流程：

```bash
python main.py
```

完整流程包括：
1. 参数注册（NVS 烧录）
2. 固件烧录
3. 模型烧录

#### 方式 2: 单独运行各模块

**固件烧录：**
```bash
python as_factory_firmware.py
```

**设备注册和 NVS 烧录：**
```bash
python as_factory_info.py
```

**模型转换和烧录：**
```bash
python as_factory_model.py
```

## 核心模块说明

### 1. as_factory_firmware.py - 固件烧录

**功能：**
- 从 `as_flash_firmware/bin_type/{BIN_TYPE}/` 目录读取固件文件
- 根据 `partitions.csv` 自动解析分区地址
- 烧录固件到 ESP32-P4

**使用方法：**
```python
# 单独运行
python as_factory_firmware.py

# 或作为模块调用
from as_factory_firmware import main
result = main(port="COM4", bin_type="ped_alarm")
```

**烧录内容：**
- Bootloader (0x2000)
- Partition Table (0x8000)
- OTA Data (动态地址)
- 主应用程序 (动态地址)
- Storage 分区 (动态地址)

### 2. as_factory_info.py - 服务器注册设备并写入 Flash

**功能：**
- 连接设备并读取 MAC 地址
- 读取并解析现有 NVS 数据
- 向服务器注册设备（创建相机、单元、账户）
- 生成 NVS 数据（CSV → BIN）
- 烧录 NVS 分区到设备

**使用方法：**
```python
# 单独运行
python as_factory_info.py

# 或作为模块调用
from as_factory_info import main
main(port="COM4", bin_type="ped_alarm")
```

**服务器注册流程：**
1. 重置配置（保留基础参数）
2. 查询相机（检查 c_sn 是否已注册）
3. 创建相机（POST /camera/c/）
4. 创建单元（POST /camera/u/）
5. 创建账户（POST /account/a/）
6. 获取设备令牌（POST /api-token-auth/）

**NVS 数据字段：**
- `c_sn`: 相机序列号
- `u_sn`: 单元序列号
- `device_token`: 服务器认证令牌
- `u_camera_id`: 相机 ID
- `u_unit_id`: 单元 ID
- `u_account_id`: 账户 ID
- `password`: 设备密码（格式：MS + MD5(u_sn)[:6] + !）
- `server_url`: 服务器地址
- `mac`: 设备 MAC 地址
- `g_camera_id`: 全局相机 ID（用于模型认证）

### 3. as_factory_model.py - 模型转换和烧录

**功能：**
- 从 NVS 读取 `g_camera_id`
- 调用模型转换模块生成加密模型
- 创建 FAT 文件系统镜像
- 烧录模型到 storage_dl 分区
- 更新 NVS 标志（is_model_update=1）
- 重启设备

**使用方法：**
```python
# 单独运行
python as_factory_model.py

# 或作为模块调用
from as_factory_model import main
result = main(port="COM4", model_type="ped_alarm", bin_type="ped_alarm")
```

**烧录流程：**
1. 读取 device_id（从 NVS 的 g_camera_id）
2. 生成加密模型（调用 as_model_conversion/as_model_auth.py）
3. 创建 storage_dl.bin（FAT 文件系统）
4. 烧录到 storage_dl 分区（偏移 0x8A0000，大小 7MB）
5. 更新 NVS（添加 is_model_update=1）
6. 烧录更新后的 NVS
7. 重启设备

### 4. main.py - 一键完整流程

**功能：**
- 从 `as_ms500_config.json` 读取配置参数
- 依次执行参数注册、固件烧录、模型烧录
- 提供完整的工厂生产流程

**使用方法：**
```bash
python main.py
```

**执行流程：**
```
1. 读取配置 (as_ms500_config.json)
   ↓
2. 参数注册 (as_factory_info.py)
   ↓
3. 固件烧录 (as_factory_firmware.py)
   ↓
4. 模型烧录 (as_factory_model.py)
   ↓
5. 完成
```

## 目录结构说明

```
MS500_Factory_P4/
├── main.py                          # 一键完整流程主程序
├── as_factory_firmware.py           # 固件烧录模块
├── as_factory_info.py               # 设备注册和 NVS 烧录模块
├── as_factory_model.py              # 模型转换和烧录模块
├── as_ms500_config.json             # 配置文件（PORT、BIN_TYPE、MODEL_TYPE 等）
├── as_ms500_config.py               # 配置读取模块
├── CLAUDE.md                        # Claude Code 项目说明文档
├── README.md                        # 本文件
│
├── docs/                            # 文档目录
│   ├── task.md                      # 任务清单
│   ├── OPERATION_MANUAL.md          # 操作手册
│   └── PYTHON_ENV_SETUP.md          # Python 虚拟环境配置指南
│
├── esp_components/                  # ESP-IDF 工具组件（自包含）
│   ├── __init__.py                  # 组件包初始化
│   ├── esp_tools.py                 # 统一工具路径配置和命令执行函数
│   ├── python_env/                  # 本地 Python 3.12.6 虚拟环境
│   │   ├── Scripts/
│   │   │   ├── python.exe           # Python 解释器
│   │   │   └── esptool.exe          # ESP32 烧录工具（v4.10.0）
│   │   └── Lib/site-packages/       # Python 依赖包
│   ├── nvs_tools/                   # NVS 分区工具
│   │   ├── nvs_tool.py              # ESP-IDF 官方 NVS 解析器
│   │   ├── nvs_parser.py
│   │   ├── nvs_check.py
│   │   └── nvs_logger.py
│   └── fatfs_tools/                 # FAT 文件系统生成工具
│       ├── wl_fatfsgen.py           # FAT 镜像生成器
│       ├── fatfsgen.py
│       └── fatfs_utils/             # FAT 工具库（11 个工具文件）
│
├── as_flash_firmware/               # 固件烧录模块
│   ├── __init__.py                  # 模块初始化，导出分区信息函数
│   ├── as_firmware_tool.py          # 固件烧录工具（解析分区表、烧录固件）
│   └── bin_type/                    # 固件类型目录
│       ├── ped_alarm/               # 行人检测固件
│       │   ├── bootloader.bin
│       │   ├── ms500_p4.bin
│       │   ├── partition-table.bin
│       │   ├── partitions.csv       # 分区表配置
│       │   ├── ota_data_initial.bin
│       │   └── storage.bin
│       └── sdk_uvc_tw_plate/        # 台湾车牌识别固件
│           └── ...
│
├── as_nvs_flash/                    # NVS 数据管理模块
│   ├── __init__.py                  # 模块初始化，导出主要函数
│   ├── as_nvs_read.py               # NVS 读取和解析
│   ├── as_nvs_update.py             # NVS 生成和烧录
│   └── temp/                        # 临时文件目录（自动创建）
│       ├── ms500_nvs.bin            # 从设备读取的原始 NVS
│       ├── factory_decoded.csv      # 解析的现有 NVS 数据
│       ├── factory_data.csv         # 新的注册数据 CSV
│       └── factory_nvs.bin          # 用于烧录的生成 NVS 二进制
│
├── as_model_flash/                  # AI 模型烧录模块
│   ├── as_model_down.py             # 从 NVS 读取 device_id 并生成模型
│   ├── as_model_flash.py            # 创建 FAT 镜像并烧录 storage_dl.bin
│   └── as_model_flag.py             # 更新 NVS 标志（is_model_update=1）
│
├── as_model_conversion/             # AI 模型转换模块
│   ├── __init__.py                  # 模块初始化，导出模型生成函数
│   ├── as_model_auth.py             # 模型认证和生成
│   ├── model_conversion.py          # 模型转换工具
│   ├── model_config.json            # 模型配置文件
│   ├── temp/                        # 临时文件目录
│   │   └── {device_id}/
│   │       └── spiffs_dl/           # 生成的模型文件
│   └── type_model/                  # 模型类型目录
│       ├── ped_alarm/               # 行人检测模型
│       │   ├── packerOut.zip
│       │   └── network_info.txt
│       └── sdk_uvc_tw_plate/        # 台湾车牌识别模型
│           └── ...
│
├── as_dm_register/                  # 设备管理注册模块
│   ├── __init__.py                  # 模块初始化
│   └── register.py                  # 服务器注册逻辑
│
└── temp/                            # 全局临时文件目录（自动创建）
    ├── ms500_nvs.bin                # 从设备读取的 NVS
    ├── factory_decoded.csv          # 解析的 NVS 数据
    ├── factory_data.csv             # 新的注册数据
    ├── factory_nvs.bin              # 生成的 NVS 二进制
    └── storage_dl_content/          # AI 模型 FAT 文件系统暂存
        └── dnn/                     # 模型文件（打包到 storage_dl.bin）
```

### 目录功能说明

#### 核心模块
- **esp_components/**: ESP-IDF 工具链（自包含，无需外部 ESP-IDF 安装）
- **as_flash_firmware/**: 固件烧录功能
- **as_nvs_flash/**: NVS 数据读写和管理
- **as_model_flash/**: AI 模型烧录功能
- **as_model_conversion/**: AI 模型转换和加密
- **as_dm_register/**: 设备服务器注册

#### 数据目录
- **temp/**: 临时文件存储（NVS、模型等）
- **bin_type/**: 固件文件存储（按类型分类）
- **type_model/**: AI 模型文件存储（按类型分类）

## ESP32-P4 Flash 内存映射

| 分区            | 偏移     | 大小 | 用途                   |
| --------------- | -------- | ---- | ---------------------- |
| bootloader      | 0x2000   | -    | 引导加载程序           |
| partition-table | 0x8000   | -    | 分区表                 |
| nvs             | 0x9000   | 64KB | 非易失性存储           |
| ota_data        | 0x19000  | -    | OTA 更新数据           |
| firmware        | 0x20000  | -    | 主应用程序             |
| storage         | 0x720000 | -    | 存储分区               |
| storage_dl      | 0x8A0000 | 7MB  | AI 模型存储（FAT）     |

## 串口配置

### Windows
- 查看串口：设备管理器 → 端口（COM 和 LPT）
- 示例：COM4

### Linux/Mac
- 查看串口：`ls /dev/ttyUSB*` 或 `ls /dev/ttyACM*`
- 示例：/dev/ttyUSB0

### 修改串口
编辑 `as_ms500_config.json` 中的 `PORT` 参数。

## 设备连接要求

### 下载模式（烧录模式）

ESP32 必须处于下载模式才能进行烧录操作：

**自动模式**（推荐）：
- 如果硬件支持 DTR/RTS，esptool 会自动处理
- 无需手动操作

**手动模式**：
1. 按住 **Boot** 按钮
2. 短按 **Reset** 按钮
3. 释放 **Boot** 按钮
4. 通过串口监视器验证：`boot:0x107 (DOWNLOAD(USB/UART0/SPI))`

## 常见问题

### 1. 串口连接失败
**错误信息**：`Error: Cannot connect to device`

**解决方法**：
- 检查 COM 端口号是否正确
- 确认设备是否处于下载模式
- 确保没有其他程序占用串口
- 检查驱动程序是否安装

### 2. NVS 解析错误
**错误信息**：`Error: Cannot decode NVS data`

**可能原因**：
- NVS 分区为空（新设备正常）
- 分区数据损坏
- 格式不兼容

**解决方法**：
- 新设备：正常，继续注册流程
- 已烧录设备：重新烧录固件

### 3. 服务器注册错误
**错误信息**：`Camera SN already registered`

**解决方法**：
- 在 `as_ms500_config.json` 中更改 `c_sn` 为唯一序列号

### 4. 模型烧录错误
**错误信息**：`g_camera_id not found`

**解决方法**：
- 必须先执行设备注册（as_factory_info.py）
- 确保 NVS 中包含 `g_camera_id` 字段

## 技术架构说明

### 1. 参数管理集中化
所有配置参数都在 `as_ms500_config.json` 中统一管理，支持灵活配置。

### 2. 命令执行统一化
所有 `subprocess.run` 操作都统一使用 `esp_tools.run_command()`，提供：
- 自动命令打印
- 统一错误处理
- 灵活的参数配置

### 3. 模块化设计
每个 Python 脚本都有特定职责：
- `main.py`: 编排完整流程
- `as_factory_*.py`: 独立功能模块
- `as_*_flash/`: 数据读写模块
- `esp_components/`: 工具库

### 4. 自包含工具链
`esp_components/` 目录包含所有 ESP-IDF 依赖，无需外部 ESP-IDF 安装。

## 开发说明

### 添加新的固件类型

1. 在 `as_flash_firmware/bin_type/` 下创建新目录
2. 放入固件文件和 `partitions.csv`
3. 在 `as_ms500_config.json` 中设置 `BIN_TYPE`

### 添加新的模型类型

1. 在 `as_model_conversion/type_model/` 下创建新目录
2. 放入 `packerOut.zip` 和 `network_info.txt`
3. 在 `as_ms500_config.json` 中设置 `MODEL_TYPE`

## 许可证

本项目为内部工厂生产工具，版权归公司所有。

## 联系方式

如有问题，请联系技术支持团队。
