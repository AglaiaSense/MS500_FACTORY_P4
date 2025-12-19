# esptool 说明文档

## 什么是 esptool？

`esptool` 是一个基于 Python 的命令行工具，用于与 ESP32/ESP8266 芯片的 ROM 引导加载程序（bootloader）进行通信。

### 主要功能

- **烧录固件**：将编译好的固件烧录到 ESP32 Flash
- **读取 Flash**：从 ESP32 Flash 读取数据
- **写入 Flash**：向 ESP32 Flash 写入数据
- **擦除 Flash**：擦除 ESP32 Flash 中的数据
- **读取芯片信息**：读取芯片 MAC 地址、芯片类型等信息
- **合并二进制文件**：将多个二进制文件合并为一个
- **生成图像文件**：生成可引导的固件映像

### 版本信息

- **工具版本**：esptool.py v4.10.0
- **位置**：`esp_components/python_env/Scripts/esptool.exe`
- **大小**：约 106KB

## 常用命令示例

### 1. 读取芯片信息

```bash
esptool --port COM4 chip_id
esptool --port COM4 read_mac
```

### 2. 读取 Flash 数据

```bash
# 读取 NVS 分区（从 0x9000 开始，读取 64KB）
esptool --port COM4 read_flash 0x9000 0x10000 temp\ms500_nvs.bin
```

**命令参数说明**：

- `--port COM4`：指定串口号
- `read_flash`：读取 Flash 命令
- `0x9000`：起始地址（NVS 分区偏移）
- `0x10000`：长度（64KB = 0x10000 字节）
- `temp\ms500_nvs.bin`：输出文件路径

### 3. 烧录固件

```bash
# 烧录单个文件
esptool --port COM4 write_flash 0x9000 nvs.bin

# 烧录多个文件
esptool -p COM4 -b 460800 write_flash \
  --flash_mode dio \
  --flash_freq 80m \
  --flash_size 16MB \
  0x2000 bootloader.bin \
  0x8000 partition-table.bin \
  0x20000 app.bin
```

**常用参数**：

- `-p` / `--port`：串口号
- `-b` / `--baud`：波特率（默认 115200，可用 460800, 921600）
- `--before`：烧录前操作（default_reset, no_reset）
- `--after`：烧录后操作（hard_reset, soft_reset, no_reset）
- `--chip`：芯片类型（esp32, esp32s2, esp32s3, esp32c3, esp32p4）
- `--flash_mode`：Flash 模式（qio, qout, dio, dout）
- `--flash_freq`：Flash 频率（80m, 40m, 26m, 20m）
- `--flash_size`：Flash 大小（2MB, 4MB, 8MB, 16MB）

### 4. 擦除 Flash

```bash
# 擦除整个 Flash
esptool --port COM4 erase_flash

# 擦除指定区域
esptool --port COM4 erase_region 0x9000 0x10000
```

### 5. 重启设备

```bash
esptool --port COM4 run
```

## 本地化配置

在 `esp_components` 中，esptool 已经本地化：

```python
# 在 esp_tools.py 中
ESPTOOL = str(ESP_COMPONENTS_DIR / "python_env" / "Scripts" / "esptool.exe")
```

### 使用方法

所有 Python 脚本都通过 `esp_components` 导入：

```python
from esp_components import get_esptool

ESPTOOL = get_esptool()
```

这样可以确保使用本地的 esptool，减少外部依赖。

## 注意事项

1. **串口连接**：确保设备正确连接到指定串口
2. **驱动程序**：确保已安装 USB 转串口驱动（CP210x, CH340 等）
3. **下载模式**：某些操作需要设备处于下载模式（Bootloader）
4. **波特率**：更高的波特率可加快烧录速度，但需要硬件支持
5. **地址对齐**：Flash 地址通常需要 4KB 对齐
6. **分区表**：烧录前确认分区表配置正确

## 错误排查

### 1. 串口连接失败

- 检查串口号是否正确
- 检查设备是否连接
- 检查串口是否被其他程序占用

### 2. 烧录失败

- 尝试降低波特率
- 确保设备处于下载模式
- 检查 Flash 地址和大小是否正确

### 3. 读取 Flash 失败

- 确保设备处于运行状态
- 检查地址和长度是否有效
- 确认 Flash 分区配置正确

## 更多信息

- **官方文档**：https://docs.espressif.com/projects/esptool/
- **GitHub 仓库**：https://github.com/espressif/esptool
- **ESP-IDF 文档**：https://docs.espressif.com/projects/esp-idf/
