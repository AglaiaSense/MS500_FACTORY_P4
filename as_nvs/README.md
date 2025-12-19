# as_nvs 模块使用说明

NVS（非易失性存储）数据管理模块，提供完整的读取、解析、生成和烧录功能。

## 模块结构

```
as_nvs/
├── __init__.py           # 统一导出接口
├── as_nvs_read.py       # NVS 读取和解析模块（可独立运行）
├── as_nvs_update.py     # NVS 生成和烧录模块
├── as_nvs_tool.py       # 兼容性包装器
└── temp/                # 临时文件目录
```

## 快速使用

### 1. 作为模块导入

```python
from as_nvs import (
    init_temp_dir,
    read_flash_and_mac,
    check_nvs_data,
    generate_nvs_data,
    flash_nvs,
)

# 初始化临时目录
init_temp_dir()

# 读取设备 NVS 和 MAC
mac = read_flash_and_mac("COM4")

# 检查 NVS 数据
nvs_info = check_nvs_data()

# 生成新的 NVS 数据
device_info = {
    "c_sn": "CA500-...",
    "u_sn": "MS500-...",
    "device_token": "...",
}
generate_nvs_data(device_info)

# 烧录到设备
flash_nvs("COM4")
```

### 2. 独立运行 as_nvs_read.py

直接读取和解析设备 NVS 数据：

```bash
# 使用默认串口 COM4
python as_nvs/as_nvs_read.py

# 指定串口号
python as_nvs/as_nvs_read.py COM5
```

输出示例：
```
============================================================
  NVS Read and Parse Tool
============================================================
Port: COM4
============================================================
============================================================
Step 1: Connect device and read Flash NVS partition
============================================================
Execute command: esptool --port COM4 read_flash 0x9000 0x10000 ...
  Detected chip: ESP32-P4
  Chip is ESP32-P4 (revision v0.1)
  MAC address: 12:34:56:78:9A:BC
✓ Successfully read NVS data to file: as_nvs/temp/ms500_nvs.bin

✓ MAC Address: 12:34:56:78:9A:BC

============================================================
Step 2: Check and decode NVS data
============================================================
  File size: 65536 bytes
  Detected: NVS partition has data

  Trying to decode NVS data...
  ✓ NVS data decoded successfully!

============================================================
  NVS Data Summary
============================================================
  c_sn: CA500-MIPI-zwcc-9999
  u_sn: MS500-H120-EP-zwcu-9999
  device_token: 43bfd95e1184a7afef00103d77ae8354fabc2810
  u_camera_id: 2612
  u_unit_id: 1766
  ...
============================================================

✓ Operation completed successfully!
```

## API 参考

### 读取模块 (as_nvs_read.py)

#### `init_temp_dir()`
初始化临时文件目录（as_nvs/temp/）

#### `read_flash_and_mac(port: str) -> str`
从设备读取 NVS 分区数据并获取 MAC 地址
- **参数**: port - 串口号（如 "COM4"）
- **返回**: MAC 地址字符串

#### `check_nvs_data() -> dict`
检查并解析 NVS 数据
- **返回**: NVS 信息字典，包含 has_data、decoded、info 等字段

#### `get_nvs_raw_bin_path() -> str`
获取原始 NVS bin 文件路径

### 更新模块 (as_nvs_update.py)

#### `generate_nvs_data(info: dict)`
生成 NVS CSV 和 BIN 文件
- **参数**: info - 设备信息字典，包含所有需要写入的键值对

#### `flash_nvs(port: str)`
烧录 NVS 数据到设备
- **参数**: port - 串口号（如 "COM4"）

#### `get_nvs_bin_path() -> str`
获取生成的 NVS bin 文件路径

## 临时文件

所有临时文件存储在 `as_nvs/temp/` 目录：

- `ms500_nvs.bin` - 从设备读取的原始 NVS 数据
- `factory_decoded.csv` - 解析后的 NVS 数据（CSV 格式）
- `factory_data.csv` - 新生成的 NVS 数据（CSV 格式）
- `factory_nvs.bin` - 生成的 NVS 二进制文件（用于烧录）

## 注意事项

1. **串口连接**: 确保设备处于下载模式（Bootloader）
2. **权限**: Windows 下可能需要管理员权限访问串口
3. **临时文件**: temp/ 目录会自动创建，无需手动创建
4. **NVS 分区**: 默认偏移 0x9000，大小 64KB，需与分区表一致
