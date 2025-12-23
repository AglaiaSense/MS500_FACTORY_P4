# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目概述

MS500 工厂生产系统 - 用于 MS500 ESP32-P4 摄像头设备的综合性工厂生产工具。该系统处理设备注册、NVS（非易失性存储）数据管理、固件烧录和 AI 模型部署。

## 项目规范（来自 .claude/settings.json）

### 语言规范

- **响应语言**：中文（zh-CN）
- **代码注释**：中文
- **日志消息**：英文（ESP_LOGI、printf 等所有打印输出必须使用英文）

### 编码标准

- **最大文件行数**：500 行
- **注释风格**：
  - 函数注释：`// 中文注释`
  - 变量注释：`// 中文注释`
  - 带参数函数：`/**/ 中文注释`
  - 段落分隔符：`#------------------  功能描述  ------------------`

### 工作流规范

- 开始前检查 task.md 中的任务
- 完成时标记任务（格式：`- [✓] **任务名称** (日期)`）
- 每次提问和提交都是一次需求，都在 task.md 里记录
- 代码修改后执行格式检查

### Python 环境

- ESP-IDF Python 环境已内置在 `esp_components/python_env/`
- Python 版本：3.12.6
- 包含所有必需的 ESP-IDF 工具和依赖

## 核心架构

### 模块化设计理念

代码库遵循模块化服务模式，每个 Python 脚本都有特定职责：

1. **main.py** - 编排完整的工厂生产工作流
2. **as_service_register.py** - 处理服务器端设备注册
3. **as_nvs_tool.py** - 管理 NVS 分区操作（读取/写入/解析）
4. **as_firmware_tool.py** - 将固件二进制文件烧录到 ESP32-P4
5. **as_model_flash.py** - 自动化 AI 模型部署到设备

所有模块使用 `as_` 前缀表示应用级服务模块。

### ESP 组件系统

`esp_components/` 目录包含一个自包含的 ESP-IDF 工具链：

```
esp_components/
├── python_env/              # 本地 Python 3.12.6 虚拟环境
│   └── Scripts/
│       ├── python.exe       # Python 解释器
│       └── esptool.exe      # ESP32 烧录工具（v4.10.0）
├── nvs_tools/              # NVS 分区工具
│   ├── nvs_tool.py         # ESP-IDF 官方 NVS 解析器
│   ├── nvs_parser.py
│   ├── nvs_check.py
│   └── nvs_logger.py
├── fatfs_tools/            # FAT 文件系统生成
│   ├── wl_fatfsgen.py
│   ├── fatfsgen.py
│   └── fatfs_utils/        # 11 个工具文件
└── esp_tools.py            # 统一工具路径配置
```

**关键架构决策**：所有 ESP-IDF 依赖都在本地打包，消除外部 ESP-IDF 安装要求。通过 `esp_components` 模块访问工具：

```python
from esp_components import (
    get_esp_idf_python,    # 返回本地 Python 路径
    get_nvs_tool_path,     # 返回 NVS 工具路径
    get_esptool,           # 返回 esptool 路径
    get_fatfs_gen_tool,    # 返回 FAT 生成器路径
    get_nvs_gen_module     # 返回模块名称
)
```

### NVS 分区架构

NVS（非易失性存储）对于设备身份和配置至关重要：

- **位置**：Flash 偏移 `0x9000`，大小 `64KB (0x10000)`
- **格式**：ESP-IDF NVS 二进制格式，带键值对
- **命名空间**：`factory` 包含所有生产数据
- **关键字段**：
  - `c_sn` - 相机序列号（字符串）
  - `u_sn` - 单元序列号（字符串）
  - `device_token` - 服务器认证令牌（字符串）
  - `u_camera_id` - 服务器分配的相机 ID（u32 或字符串）
  - `u_unit_id` - 服务器分配的单元 ID（u32）
  - `u_account_id` - 账户 ID（u32）
  - `password` - 设备密码（字符串）
  - `server_url` - 服务器地址（字符串）
  - `u_url` - 设备 URL（字符串）
  - `mac` - 设备 MAC 地址（字符串）
  - `g_camera_id` - 用于 AI 模型认证的全局相机 ID（字符串，32 字符十六进制）

**NVS 工作流程**：

1. 使用 esptool 从设备读取原始二进制
2. 使用官方 `nvs_tool.py` 的 "minimal" 格式解析
3. 将解析的输出转换为 CSV 格式
4. 在 CSV 中修改/添加键值对
5. 使用 `esp_idf_nvs_partition_gen` 模块生成新的二进制
6. 烧录回设备偏移 `0x9000`

### 工厂生产工作流程

由 `main.py` 编排的完整生产流程：

```
1. 连接设备 → 读取 MAC + NVS 分区 (0x9000, 64KB)
2. 检查 NVS → 解析现有数据，如果已注册则提示
3. 服务器注册 → 调用 as_service_register.py
   └─> 重置配置 → 查询相机 → 创建相机 → 创建单元 → 创建账户 → 获取令牌
4. 生成 NVS → 使用注册数据创建 CSV → 生成 BIN
5. 烧录 NVS → 将 NVS 分区写回设备
6. 完成 → 显示注册摘要
```

### 服务器注册流程

`as_service_register.py` 实现多步骤 REST API 工作流：

1. **重置配置** - 仅保留基础参数（server_url, c_sn, u_sn, for_organization, u_url）
2. **查询相机** - 检查 c_sn 是否已注册（GET /camera/c/）
3. **创建相机** - 使用 c_sn 注册新相机（POST /camera/c/）
4. **创建单元** - 注册 u_sn 单元并链接到相机（POST /camera/u/）
5. **创建账户** - 生成基于 MD5 的密码账户（POST /account/a/）
6. **获取令牌** - 认证并检索设备令牌（POST /api-token-auth/）

**密码生成规则**：`MS` + MD5(u_sn)[:6] + `!`（例如："MS79b2a1!"）

**关键**：使用固定的管理员令牌 `9b47d0133201679526cfc29825beff5f275574fa`。所有步骤必须成功，否则注册中止。

### AI 模型部署系统

`as_model_flash.py` 实现自动化 AI 模型部署：

**工作流程**：

1. 读取 NVS → 提取 `g_camera_id`（32 字符十六进制设备 ID）
2. 生成模型 → 调用 `model/as_model_auth.py::generate_model_by_device_id()`
3. 创建 FAT 镜像 → 将模型文件打包到 `storage_dl.bin`（FAT 文件系统）
   - 模型放置在 `/dnn/` 目录中
   - 使用长文件名支持（LFN）
4. 烧录模型 → 写入 storage_dl 分区（偏移 `0x8A0000`，7MB）
5. 更新 NVS → 添加 `is_model_update=1` 标志
6. 烧录 NVS → 写入更新的 NVS 分区
7. 重启设备 → 触发 ESP32 重启

**存储分区**：`storage_dl` 位于偏移 `0x8A0000`，大小 `0x700000`（7MB），格式化为 FAT 文件系统。

**模型配置**：`model/model_config.json` 指定模型目录和 device_id（从 NVS 覆盖）。

### 配置文件

**ms500.json** - 主设备配置：

```json
{
  "server_url": "http://...",
  "c_sn": "CA500-MIPI-...", // 相机序列号（唯一）
  "u_sn": "MS500-H120-EP-...", // 单元序列号（唯一）
  "for_organization": "",
  "u_url": "127.0.0.1",
  // 注册后自动填充：
  "u_camera_id": 2612,
  "u_unit_id": 1766,
  "u_account_id": 157,
  "password": "MS05e8f1!",
  "device_token": "..."
}
```

**model/model_config.json** - AI 模型配置：

```json
{
  "model_dir": "ped_alerm", // as_model_conversion/ 下的模型目录
  "device_id": "..." // 从 NVS g_camera_id 自动读取
}
```

## 常用开发命令

### 工厂生产

```bash
# 完整的工厂生产流程（注册 + NVS 烧录）
python main.py

# 仅测试串口连接
# 编辑 main.py，取消底部第 304-305 行的注释
```

### 设备注册

```bash
# 独立的设备注册（不烧录 NVS）
python as_service_register.py

# 前提条件：配置 ms500.json 中的 server_url、c_sn、u_sn
```

### 固件烧录

```bash
# 将完整固件烧录到 ESP32-P4
python as_flash_firmware/as_firmware_tool.py

# 前提条件：as_flash_firmware/bin_type/ 目录中的固件文件：
#   - bootloader.bin (0x2000)
#   - ms500_p4.bin (0x20000)
#   - partition-table.bin (0x8000)
#   - ota_data_initial.bin (0x19000)
#   - storage.bin (0x720000)
```

### AI 模型部署

```bash
# 自动化 AI 模型烧录
python as_factory_model.py

# 前提条件：
#   1. 模型文件位于 as_model_conversion/{model_dir}/packerOut.zip
#   2. 配置 as_model_conversion/model_config.json
#   3. 设备 NVS 必须包含 g_camera_id
```

### NVS 操作

```python
# 从设备读取并解析 NVS
import as_nvs_tool
as_nvs_tool.init_temp_dir()
nvs_info = as_nvs_tool.check_nvs_data()

# 生成新的 NVS 二进制
device_info = {
    "c_sn": "CA500-...",
    "u_sn": "MS500-...",
    "device_token": "...",
    # ... 其他字段
}
as_nvs_tool.generate_nvs_data(device_info)
```

## ESP32-P4 Flash 内存映射

ESP32-P4 的关键分区偏移：

| 分区            | 偏移     | 大小 | 用途                   |
| --------------- | -------- | ---- | ---------------------- |
| bootloader      | 0x2000   | -    | 引导加载程序二进制文件 |
| partition-table | 0x8000   | -    | 分区表                 |
| nvs             | 0x9000   | 64KB | 非易失性存储           |
| ota_data        | 0x19000  | -    | OTA 更新数据           |
| firmware        | 0x20000  | -    | 主应用程序             |
| storage         | 0x720000 | -    | 存储分区               |
| storage_dl      | 0x8A0000 | 7MB  | AI 模型存储（FAT）     |

## 串口配置

默认值：`COM4`（Windows）

**修改方法**：编辑相应 Python 文件中的 `PORT` 变量：

- `main.py:15`
- `as_flash_firmware/as_firmware_tool.py:18`
- `as_model_flash.py:57`

**查找端口**：

- Windows：设备管理器 → 端口（COM 和 LPT）
- Linux/Mac：`ls /dev/ttyUSB*` 或 `ls /dev/ttyACM*`

## 设备连接要求

**下载模式（引导加载程序）**：

- ESP32 必须处于下载模式才能进行烧录操作
- 自动模式：如果硬件支持 DTR/RTS，esptool 会自动处理
- 手动模式：
  1. 按住 **Boot** 按钮
  2. 短按 **Reset** 按钮
  3. 释放 **Boot** 按钮
  4. 通过串口监视器验证：`boot:0x107 (DOWNLOAD(USB/UART0/SPI))`

## 错误处理模式

### 连接错误

- 检查 COM 端口号和可用性
- 验证设备是否处于下载模式
- 确保没有其他程序使用串口
- 确认驱动程序安装

### NVS 解析错误

- NVS 分区可能为空（全部 0xFF）- 新设备正常
- 分区数据损坏 - 重新烧录固件
- 格式不兼容 - 检查 ESP-IDF 版本

### 注册错误

- "Camera SN already registered" - 在 ms500.json 中更改 c_sn
- 网络超时 - 验证 server_url 可访问性
- 令牌认证失败 - 检查管理员令牌有效性

### 模型烧录错误

- g_camera_id 未找到 - 必须先注册设备
- 模型生成失败 - 检查模型目录和 packerOut.zip
- FAT 生成失败 - 验证文件数量和大小限制

## 临时文件

所有临时文件存储在 `temp/` 目录中：

```
temp/
├── ms500_nvs.bin          # 从设备读取的原始 NVS
├── factory_decoded.csv    # 解析的现有 NVS 数据
├── factory_data.csv       # 新的注册数据 CSV
├── factory_nvs.bin        # 用于烧录的生成 NVS 二进制
└── storage_dl_content/    # AI 模型 FAT 文件系统暂存
    └── dnn/               # 模型文件（打包到 storage_dl.bin）
```

首次运行时自动创建。可以删除以清理工作空间。

## 关键架构说明

1. **序列号唯一性**：`c_sn` 和 `u_sn` 都必须全局唯一。生产系统必须实现序列号分配逻辑。

2. **NVS 数据持久性**：NVS 数据在固件更新中保留，但在完全芯片擦除中不保留。完全擦除操作前务必备份 NVS。

3. **模型认证安全**：NVS 中的 `g_camera_id` 用于认证和加密 AI 模型。必须在初始注册时设置，不应更改。

4. **嵌入式 ESP-IDF 工具**：`esp_components/` 目录是自包含的。除非有意为之，不要修改路径指向外部 ESP-IDF 安装。

5. **FAT 文件系统限制**：storage_dl 分区使用带长文件名支持的 FAT12/16。目录深度和文件名长度有实际限制。

6. **Python 虚拟环境**：捆绑的 Python 环境（`esp_components/python_env/`）依赖于系统 Python（C:\Python312）。这是一个虚拟环境，而非独立的 Python。

7. **设备 ID 格式**：`g_camera_id` 是 32 字符十六进制字符串（例如："100B50501A2101026964011000000000"）。此格式对模型认证系统至关重要。

8. **波特率调优**：默认波特率为 115200 以确保兼容性。如果硬件支持，可以增加到 460800/921600 以加快烧录速度（参见 `as_model_flash.py:62`）。

## 测试和验证

工厂生产后，验证：

1. 设备成功启动
2. 通过 `as_nvs_tool.check_nvs_data()` 可读取 NVS 数据
3. 设备可以使用 device_token 与服务器认证
4. AI 模型从 storage_dl 分区正确加载
5. 序列号和 ID 与服务器记录匹配

使用串口监视器观察启动期间的设备日志以进行诊断。

## 代码格式规范

根据 `.claude/settings.local.json` 中的钩子配置，每次代码修改后会自动运行格式检查：

```bash
npx prettier --check .
```

如需手动格式化，运行：

```bash
npx prettier --write .
```

## 任务管理

参考 `task.md` 文件进行任务追踪：

- 每个需求都要记录完成情况
- 格式：`- [✓] **需求名称** (YYYY-MM-DD)`
- 每次提问和提交都是一次需求，都需要在 task.md 中记录
