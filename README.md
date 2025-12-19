# MS500 出厂生产程序

MS500 设备出厂注册与 NVS 数据管理工具集，用于将设备注册到服务器并烧录配置信息。

---

## 整体工厂生产流程

完整的工厂生产流程如下：

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MS500 工厂生产流程                              │
└─────────────────────────────────────────────────────────────────────┘

1. 连接设备
   └─> 使用 esptool 连接 ESP32 设备（COM4）
   └─> 初始化 temp/ 临时目录

2. 读取设备 Flash NVS 分区
   └─> 从偏移地址 0x9000 读取 64KB NVS 数据到 temp/ms500_nvs.bin
   └─> 自动读取设备 MAC 地址

3. 检查设备是否已注册
   └─> 使用官方 nvs_tool.py 解析 NVS 数据（由 as_nvs_tool 模块处理）
   └─> 如果已注册，询问是否重新注册

4. 向服务器注册设备
   └─> 调用 as_service_register.py 注册设备
   └─> 获取设备信息（SN、Token、Camera ID、Unit ID）

5. 生成并烧录 NVS 数据
   └─> 生成 NVS CSV 文件（temp/factory_data.csv）
   └─> 生成 NVS BIN 文件（temp/factory_nvs.bin）
   └─> 烧录到 Flash 偏移地址 0x9000

6. 完成
   └─> 显示设备注册信息（SN、MAC、Camera ID、Unit ID）
```

---

## 使用配置

在运行工厂生产程序之前，需要先进行以下配置：

### 1. 配置 ESP-IDF 环境路径

**修改 as_nvs_tool.py 文件中的路径配置：**

```python
# ESP-IDF Python 环境路径（根据你的电脑环境修改）
ESP_IDF_PYTHON = r"C:\Users\xiuxin\Desktop\esp-idf\python_env\idf5.4_py3.12_env\Scripts\python.exe"

# ESP-IDF 官方 NVS 工具路径（根据你的电脑环境修改）
NVS_TOOL_PATH = r"C:\Users\xiuxin\Desktop\esp-idf\frameworks\esp-idf-v5.4.1\components\nvs_flash\nvs_partition_tool\nvs_tool.py"
```

**修改 main.py 文件中的工具配置：**

```python
# 工具路径（根据你的电脑环境修改，通常在 PATH 中可直接使用）
ESPTOOL = "esptool"
```

### 2. 配置设备串口

**修改 main.py 文件中的串口配置：**

```python
def main():
    PORT = "COM4"  # 修改为实际端口，如 COM3、COM5 等
```

**如何查看设备串口：**

- Windows：设备管理器 → 端口(COM 和 LPT)
- Linux/Mac：`ls /dev/ttyUSB*` 或 `ls /dev/ttyACM*`

### 3. 设备进入烧录模式

**在运行程序前，确保设备已进入 DOWNLOAD 模式：**

连接设备后，在串口工具（如 Putty、SecureCRT）中查看输出，应看到类似信息：

```
rst:0x1 (POWERON),boot:0x107 (DOWNLOAD(USB/UART0/SPI))
waiting for download
```

**进入烧录模式的方法：**

1. **自动模式**：如果开发板支持 DTR/RTS 自动复位，esptool 会自动进入烧录模式
2. **手动模式**：
   - 按住 **Boot** 按钮
   - 按一下 **Reset** 按钮
   - 松开 **Boot** 按钮
   - 设备进入烧录模式

### 4. 配置服务器信息

**修改 ms500.json 文件：**

```json
{
  "server_url": "https://your-server.com",
  "c_sn": "MS500-H090-EP-2549-0001",
  "for_organization": "your-org-id",
  "u_url": "127.0.0.1"
}
```

**必填参数：**

- `server_url` - 服务器地址
- `c_sn` - 设备序列号（必须唯一，每台设备不同）
- `u_url` - 设备 URL 地址（默认 127.0.0.1）

---

## 使用方法

```bash
# 工厂生产程序（一键完成所有步骤）
cd pc_client/python_factory
python main.py
```

---

## 代码架构

### 模块化设计

```
python_factory/
├── main.py                    # 主程序：流程控制
├── as_nvs_tool.py            # NVS 工具模块：NVS 数据处理
├── as_service_register.py    # 设备注册模块：服务器注册
├── ms500.json                # 配置文件
└── temp/                     # 临时文件目录
    ├── ms500_nvs.bin
    ├── factory_decoded.csv
    ├── factory_data.csv
    └── factory_nvs.bin
```

---

## 1. main.py

**主程序：工厂生产流程控制**

一键完成设备注册和 NVS 数据烧录的完整流程。

### 1.1 功能说明

main.py 协调各模块完成生产流程：

1. **读取设备 Flash** - 连接设备并读取 NVS 分区数据
2. **检查已有数据** - 调用 as_nvs_tool 解析 NVS，检查是否已注册
3. **服务器注册** - 调用 as_service_register 向服务器注册设备
4. **生成并烧录** - 调用 as_nvs_tool 生成 NVS 数据并烧录到设备

### 1.2 使用方法

```bash
# 运行完整的生产流程
python main.py
```

### 1.3 配置说明

修改 main.py 中的配置：

```python
# 工具路径
ESPTOOL = "esptool"

# 临时文件目录
TEMP_DIR = "temp"

# 串口端口
PORT = "COM4"

# NVS 分区配置
NVS_OFFSET = "0x9000"
NVS_SIZE = "0x10000"  # 64KB
```

### 1.4 主要函数

```python
# 测试串口连接并读取 MAC 地址
test_read_mac(port)

# 步骤1：从设备读取 NVS 分区数据并获取 MAC 地址
read_flash_and_mac(port)

# 步骤3：调用 as_service_register 注册设备
request_server(mac)

# 步骤5：烧录 NVS 数据到设备
flash_nvs(port)

# 主流程函数
main()
```

### 1.5 调用的外部模块

```python
import as_nvs_tool         # NVS 工具模块
import as_service_register # 设备注册模块

# 调用 as_nvs_tool 的函数
as_nvs_tool.init_temp_dir()           # 初始化临时目录
as_nvs_tool.get_nvs_raw_bin_path()    # 获取原始 BIN 路径
as_nvs_tool.check_nvs_data()          # 检查并解码 NVS 数据
as_nvs_tool.generate_nvs_data(info)   # 生成 NVS CSV 和 BIN
as_nvs_tool.get_nvs_bin_path()        # 获取 NVS BIN 路径

# 调用 as_service_register 的函数
as_service_register.main()            # 注册设备
```

---

## 2. as_nvs_tool.py

**NVS 工具模块：NVS 数据管理**

封装所有 NVS 相关操作，包括解析、生成和格式转换。

### 2.1 功能说明

as_nvs_tool.py 提供完整的 NVS 数据管理功能：

- 初始化临时目录管理
- 使用官方 nvs_tool.py 解析 NVS 数据
- 将官方工具输出转换为 CSV 格式
- 生成 NVS CSV 和 BIN 文件
- 提供文件路径访问接口

### 2.2 配置说明

```python
# ESP-IDF Python 环境路径
ESP_IDF_PYTHON = r"C:\Users\xiuxin\Desktop\esp-idf\python_env\idf5.4_py3.12_env\Scripts\python.exe"

# ESP-IDF 官方 NVS 工具路径
NVS_TOOL_PATH = r"C:\Users\xiuxin\Desktop\esp-idf\frameworks\esp-idf-v5.4.1\components\nvs_flash\nvs_partition_tool\nvs_tool.py"

# 使用 ESP-IDF 的 NVS 分区生成模块
NVS_GEN_MODULE = "esp_idf_nvs_partition_gen"

# 临时文件目录
TEMP_DIR = "temp"

# 临时文件路径
NVS_RAW_BIN = os.path.join(TEMP_DIR, "ms500_nvs.bin")
DECODED_CSV = os.path.join(TEMP_DIR, "factory_decoded.csv")
FACTORY_CSV = os.path.join(TEMP_DIR, "factory_data.csv")
FACTORY_BIN = os.path.join(TEMP_DIR, "factory_nvs.bin")

# NVS 分区配置
NVS_OFFSET = "0x9000"
NVS_SIZE = "0x10000"  # 64KB
```

### 2.3 主要函数

```python
# 初始化临时文件目录
init_temp_dir()

# 将 nvs_tool.py 的输出转换为 CSV 格式
convert_to_csv(nvs_output, output_file)

# 检查并解码 NVS 数据，判断设备是否已有注册信息
check_nvs_data()

# 生成 NVS CSV 和 BIN 文件
generate_nvs_data(info)

# 获取生成的 NVS BIN 文件路径
get_nvs_bin_path()

# 获取 NVS 原始 BIN 文件路径
get_nvs_raw_bin_path()
```

### 2.4 核心特性

**使用官方工具解析 NVS 数据：**

```python
# 使用官方 nvs_tool.py 解析（minimal 格式）
cmd = [ESP_IDF_PYTHON, NVS_TOOL_PATH, NVS_RAW_BIN, "-d", "minimal"]
```

输出格式：`namespace:key = value`，然后通过 `convert_to_csv()` 函数转换为标准 CSV 格式。

函数 `generate_nvs_data()`，一次性完成 CSV 和 BIN 生成。

---

## 3. as_service_register.py

**设备注册模块：服务器注册**

独立的设备注册服务脚本，处理与服务器的所有交互。

### 3.1 功能说明

脚本执行以下步骤：

1. 重置配置文件 - 保留基础配置参数（server_url, c_sn, for_organization, u_url）
2. 查询摄像头是否已注册 - 如果设备已存在，则提示并退出，避免重复注册
3. 创建摄像头 - 在服务器上创建摄像头记录
4. 创建 Unit - 创建设备单元并关联摄像头
5. 创建账户 - 为设备创建账户，密码基于 SN 号自动生成
6. 获取设备 Token - 使用账户信息获取设备认证令牌

### 3.2 使用方法

```bash
# 独立运行
python as_service_register.py

# 或被 main.py 调用
import as_service_register
result = as_service_register.main()
```

### 3.3 代码结构

```python
# 常量定义
ADMIN_TOKEN = "..."       # 管理员Token
CAMERA = '/camera/c/'     # 摄像头API端点
TIME_OUT = 300            # 请求超时时间

# StreamingEndpoint 类 - 服务器API连接
class StreamingEndpoint:
    get_data_from_site()   # GET请求
    post_data_to_site()    # POST请求

# 配置管理函数
reset_config()             # 重置配置文件

# 密码生成函数
generate_password_from_sn() # 基于SN生成固定密码（MS + MD5前6位 + !）

# 主注册函数
main()                     # 执行完整的注册流程
```

### 3.4 返回值格式

```python
{
    'success': True/False,      # 注册是否成功
    'error': '',                # 错误信息（如果失败）
    'c_sn': '',                 # 设备序列号
    'device_token': '',         # 设备认证令牌
    'u_camera_id': 0,           # 摄像头ID
    'u_unit_id': 0,             # Unit ID
    'u_url': '',                # Unit URL
    'server_url': ''            # 服务器地址
}
```

### 3.5 错误处理

- 任何步骤失败都会立即停止，不执行后续步骤
- 如果摄像头已注册，提示修改 SN 号
- 所有错误信息都记录在返回值的 error 字段中

---

## 4. ms500.json

**配置文件**

设备注册所需的配置文件，包含服务器信息和设备信息。

### 4.1 配置项说明

```json
{
  "server_url": "https://your-server.com",
  "c_sn": "MS500-H090-EP-2549-0001",
  "for_organization": "your-org-id",
  "u_url": "127.0.0.1"
}
```

### 4.2 必填参数

| 参数       | 说明                 | 示例                    |
| ---------- | -------------------- | ----------------------- |
| server_url | 服务器地址           | https://server.com      |
| c_sn       | 设备序列号，必须唯一 | MS500-H090-EP-2549-0001 |
| u_url      | 设备 URL 地址        | 127.0.0.1               |

### 4.3 注册后新增字段

注册成功后，配置文件会自动添加以下字段：

```json
{
  "u_camera_id": 123,
  "u_unit_id": 456,
  "u_account_id": 789,
  "password": "MS79b2a1!",
  "device_token": "abc123..."
}
```

---

## 5. 工具对比

| 工具                       | 功能             | 使用场景         | 依赖                             |
| -------------------------- | ---------------- | ---------------- | -------------------------------- |
| **main.py**                | 完整生产流程控制 | 工厂批量生产     | as_nvs_tool, as_service_register |
| **as_nvs_tool.py**         | NVS 数据管理     | 被 main.py 调用  | nvs_tool.py, esptool             |
| **as_service_register.py** | 设备注册         | 独立注册或被调用 | requests, ms500.json             |

---

## 6. 临时文件管理

### 6.1 统一目录

所有临时文件统一存放在 `temp/` 目录下，便于管理和清理：

```
temp/
├── ms500_nvs.bin           # 从设备读取的原始 NVS 数据
├── factory_decoded.csv     # 解析后的已有 NVS 数据
├── factory_data.csv        # 新的注册数据 CSV
└── factory_nvs.bin         # 最终的 NVS BIN 文件
```

### 6.2 自动管理

- **自动创建** - main.py 运行时自动创建 temp/ 目录
- **便于清理** - 可通过删除 temp/ 目录清理所有临时文件
- **路径管理** - as_nvs_tool.py 提供路径访问接口

---

## 7. 密码生成规则

设备密码基于 SN 号自动生成，确保每个设备有唯一且可复现的密码：

- 格式：MS + MD5前6位 + !
- 示例：SN = MS500-001 生成密码 = MS79b2a1!
- 特点：
  - 相同的 SN 总是生成相同的密码
  - 包含大写字母、数字、特殊字符
  - 8位长度，安全性适中

---

## 8. 注意事项

1. **SN 号必须唯一** - 如果 SN 已存在，注册会失败，需要修改 c_sn
2. **ESP-IDF 环境** - 必须正确配置 ESP-IDF Python 环境路径
3. **NVS 工具路径** - 确保 nvs_tool.py 路径正确
4. **设备连接** - 设备需要处于下载模式（Bootloader）
5. **NVS 分区配置** - 偏移地址和大小必须与分区表一致
6. **网络要求** - 确保可以访问 server_url 指定的服务器
7. **临时文件** - 生产流程会在 temp/ 目录生成临时文件
8. **模块命名** - 注意 as\_ 前缀，表示这是应用级服务模块

---

## 9. 常见问题

**问题1: 如何修改 ESP-IDF Python 路径？**

编辑 as_nvs_tool.py，修改常量：

```python
ESP_IDF_PYTHON = r"C:\your-path\esp-idf\python_env\idf5.4_py3.12_env\Scripts\python.exe"
```

**问题2: 如何修改 NVS 分区配置？**

编辑 main.py 和 as_nvs_tool.py，根据分区表修改：

```python
NVS_OFFSET = "0x9000"
NVS_SIZE = "0x10000"  # 64KB
```

**问题3: 设备连接失败怎么办？**

检查：

1. 设备是否正确连接到指定 COM 端口
2. 设备是否处于下载模式（按住 Boot 按钮重启）
3. 串口是否被其他程序占用
4. 驱动是否正确安装

**问题4: NVS 解析失败怎么办？**

可能原因：

1. NVS 分区数据损坏 - 重新烧录固件
2. NVS 分区格式不兼容 - 检查固件版本
3. 分区配置错误 - 检查偏移地址和大小

**问题5: 如何处理重复注册？**

如果提示 "Camera SN is already registered"，有两个选择：

1. 修改 ms500.json 中的 c_sn 为新的序列号
2. 在服务器端删除旧的摄像头记录（如果确认需要重新注册）

**问题6: 临时文件存放在哪里？**

所有临时文件统一存放在 `temp/` 目录下，包括：

- temp/ms500_nvs.bin
- temp/factory_decoded.csv
- temp/factory_data.csv
- temp/factory_nvs.bin

---

## 10. 技术支持

- 开发环境：Python 3.7+
- 依赖库：requests、urllib3、esptool
- 服务器 API：基于 Django REST Framework
- 认证方式：Token Authentication
