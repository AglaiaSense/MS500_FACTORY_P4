# CLAUDE.md

此文件为 Claude Code 在此仓库中工作时提供指导。

## 项目概述

MS500 工厂生产系统 - ESP32-P4 摄像头设备的工厂生产工具，处理设备注册、NVS 数据管理、固件烧录和 AI 模型部署。

## 项目规范

### 语言规范

- **响应语言**：中文（zh-CN）
- **代码注释**：中文
- **打印输出**：中文（zh-CN）

### 编码标准

- **最大文件行数**：500 行
- **注释风格**：
  - 函数：`# 中文注释`
  - 带参数函数：`/**/ 中文注释`
  - 段落分隔符：`#------------------  功能描述  ------------------`

### 工作流规范

- 开始前检查 `docs/task.md` 中的任务
- 完成时标记任务：`- [✓] **任务名称** (YYYY-MM-DD)`
- 每次需求都在 `docs/task.md` 中记录
- 代码修改后自动执行格式检查（prettier）

## 核心架构

### 模块设计

```
main.py                      # 主流程：参数注册 → 固件烧录 → 模型烧录
├─ as_factory_info.py        # 设备注册和 NVS 烧录
├─ as_factory_firmware.py    # 固件烧录
└─ as_factory_model.py       # AI 模型烧录

as_ms500_config.py           # 统一配置管理
as_ms500_config.json         # 配置文件（PORT、BIN_TYPE、MODEL_TYPE、序列号等）
as_ms500_config.json.template # 配置模板文件（提交到 Git，不包含敏感信息）
```

**配置文件说明：**
- `as_ms500_config.json.template` - 配置模板文件，提交到 Git 仓库，包含配置示例
- `as_ms500_config.json` - 实际配置文件，**不提交到 Git**（.gitignore），包含真实参数
- 首次使用需要从模板复制：`copy as_ms500_config.json.template as_ms500_config.json`

### ESP 组件系统

`esp_components/` - 自包含的 ESP-IDF 工具链：

```python
from esp_components import (
    get_esp_idf_python,    # .venv/Scripts/python.exe
    get_esptool,           # .venv/Scripts/esptool.exe
    get_nvs_tool_path,     # NVS 工具路径
    get_fatfs_gen_tool,    # FAT 生成器路径
    run_command            # 统一命令执行
)
```

**关键**：所有工具从 `.venv` 虚拟环境加载（Python 3.12.x）。

### NVS 分区架构

**位置**：Flash 偏移 `0x9000`，大小 `64KB`
**命名空间**：`factory`

**关键字段**：
- `c_sn`, `u_sn` - 相机/单元序列号（**必须全局唯一**）
- `device_token` - 服务器认证令牌
- `u_camera_id`, `u_unit_id`, `u_account_id` - 服务器分配的 ID
- `g_camera_id` - AI 模型认证 ID（32 字符十六进制，**不可更改**）
- `mac`, `password`, `server_url` - 设备配置

**工作流程**：读取 → 解析（nvs_tool.py）→ 转 CSV → 修改 → 生成 BIN（esp_idf_nvs_partition_gen）→ 烧录

### 服务器注册流程

1. 查询相机（GET /camera/c/）- 检查 `c_sn` 是否已注册
2. 创建相机（POST /camera/c/）
3. 创建单元（POST /camera/u/）- 链接到相机
4. 创建账户（POST /account/a/）- 密码：`MS` + MD5(u_sn)[:6] + `!`
5. 获取令牌（POST /api-token-auth/）

**管理员令牌**：`9b47d0133201679526cfc29825beff5f275574fa`

### AI 模型部署

1. 读取 NVS → 提取 `g_camera_id`
2. 生成模型 → `as_model_auth.py::generate_model_by_device_id()`
3. 创建 FAT 镜像 → 将模型打包到 `/dnn/` 目录
4. 烧录到 `storage_dl` 分区（偏移 `0x8A0000`，7MB）
5. 更新 NVS → 添加 `is_model_update=1`
6. 重启设备

## ESP32-P4 Flash 内存映射

| 分区            | 偏移     | 大小 | 用途           |
| --------------- | -------- | ---- | -------------- |
| bootloader      | 0x2000   | -    | 引导程序       |
| partition-table | 0x8000   | -    | 分区表         |
| **nvs**         | 0x9000   | 64KB | 非易失性存储   |
| ota_data        | 0x19000  | -    | OTA 数据       |
| firmware        | 0x20000  | -    | 主应用程序     |
| storage         | 0x720000 | -    | 存储分区       |
| **storage_dl**  | 0x8A0000 | 7MB  | AI 模型（FAT） |

## 关键架构决策

1. **配置管理**：所有参数通过 `as_ms500_config.py` 统一读取，避免硬编码
2. **序列号唯一性**：`c_sn` 和 `u_sn` 必须全局唯一，生产时需要序列号管理系统
3. **NVS 持久性**：固件更新时保留，完全擦除时丢失 - **擦除前备份**
4. **模型认证安全**：`g_camera_id` 用于模型加密，初始注册后不应更改
5. **虚拟环境**：`.venv` 包含完整 ESP-IDF 工具，通过 `esp_components` 访问
6. **设备下载模式**：烧录前确保设备处于下载模式（手动：按住 Boot → Reset → 释放 Boot）

## 常见操作

### 完整工厂流程
```bash
python main.py  # 参数注册 → 固件烧录 → 模型烧录
```

### 单独模块
```bash
python as_factory_info.py      # 仅设备注册和 NVS 烧录
python as_factory_firmware.py  # 仅固件烧录
python as_factory_model.py     # 仅模型烧录
```

### 配置验证
```bash
python as_ms500_config.py  # 验证配置文件
```

## 常见问题

### 连接错误
- 检查 COM 端口号（`as_ms500_config.json`）
- 确认设备处于下载模式
- 确保串口未被占用

### 注册错误
- "Camera SN already registered" → 修改 `c_sn` 为新序列号
- 网络超时 → 验证 `server_url` 可访问

### 模型烧录错误
- "g_camera_id not found" → 必须先执行设备注册

## 文档索引

- **操作手册**：`docs/OPERATION_MANUAL.md` - 完整操作指南
- **环境配置**：`docs/PYTHON_ENV_SETUP.md` - 虚拟环境配置
- **任务追踪**：`docs/task.md` - 当前任务清单
- **项目说明**：`README.md` - 项目概览和架构

---

**优化说明**：本文件已精简至核心内容，详细操作请参考 `docs/` 目录下的文档。
