##### 需求: 通过 SN 号向 DM 注册设备，获取注册参数，生成 nvc.bin 烧录 bin

1. 新建 as_dm_register 目录将 as_service_register.py 和 ms500.json 移动过去

2. ms500.json 改名成 as_request.json,主要存放请求的参数，

3. 新建 as_respond.json,存放请求的参数和响应的参数，

4. 将现在的 main.py 修改成，as_factory_info.py，优化里面的代码，需要的函数都封装在 as_nvs 和 as_dm_register 里面了,

- [✓] **需求1: 重构设备注册模块** (2025-12-19)
  - 创建 as_dm_register 目录
  - 移动 as_service_register.py 到 as_dm_register/
  - 将 ms500.json 重命名为 as_request.json（存放请求参数）
  - 创建 as_respond.json（存放请求参数和响应参数的完整结构）
  - 修改 as_service_register.py 以使用新的 JSON 文件结构
  - 将 main.py 重命名为 as_factory_info.py 并更新导入路径

#### 需求：烧录整个程序

1. 新建 as_flash_firmware 目录，将 as_firmware_tool.py 函数移动过去，将 ms500_build 移动进去

2. 在 as_flash_firmware 目录下新建 bin_type 目录，将 ms500_build 改名成 ped_alarm 移动到 bin_type 中，

3. ped_alarm 下有个 partitions.csv 文件，里面是需要烧录的地址，和需要烧录的文件。烧录地址和文件都从这里面获取，不需要写死

- [✓] **需求2: 重构固件烧录模块** (2025-12-19)
  - 创建 as_flash_firmware 目录
  - 移动 as_firmware_tool.py 到 as_flash_firmware/
  - 移动 ms500_build 到 as_flash_firmware/
  - 在 as_flash_firmware 下创建 bin_type 目录
  - 将 ms500_build 重命名为 ped_alarm 移动到 bin_type/
  - 创建 flash_config.csv 配置文件（包含文件名和烧录地址映射）
  - 修改 as_firmware_tool.py 实现从 CSV 文件动态读取烧录配置
  - 添加 load_flash_config() 函数解析 CSV 配置
  - 更新文件路径以支持模块化结构

- [✓] **代码格式化** (2025-12-19)
  - 执行 npx prettier --write . 修复所有格式问题

#### 需求：删除一级目录下的 as_nvs_tool.py，如果需要使用 as_nvs/as_nvs_tool.py

- [✓] **需求3: 清理重复文件** (2025-12-19)
  - 检查项目中是否有引用根目录 as_nvs_tool.py 的代码
  - 确认所有引用已使用 as_nvs 模块导入
  - 删除根目录下的 as_nvs_tool.py 文件
  - 统一使用 as_nvs/as_nvs_tool.py

#### 需求：直接使用 partitions.csv 文件，而不是 flash_config.csv

- [✓] **需求4: 使用 partitions.csv 替代 flash_config.csv** (2025-12-19)
  - 分析 partitions.csv 文件格式（ESP-IDF 标准分区表格式）
  - 创建 PARTITION_TO_BIN 映射表（分区名称到 bin 文件的对应关系）
  - 重写 load_flash_config() 函数解析 partitions.csv
  - 支持固定地址（bootloader、partition-table）和分区表地址
  - 删除 flash_config.csv 文件
  - 更新配置文件路径从 FLASH_CONFIG_FILE 改为 PARTITIONS_CSV

#### 需求：优化 load_flash_config()，传入目录就烧录该目录的 bin 文件

支持多个固件目录（ped_alarm 和 sdk_uvc），partitions.csv 可能分配了地址，但是没有 .bin 文件就不烧录

- [✓] **需求5: 优化 load_flash_config 支持动态目录和文件检测** (2025-12-19)
  - 修改 load_flash_config() 函数签名，添加 bin_dir 参数
  - 从传入的目录读取 partitions.csv 文件
  - 添加 bin 文件存在性检查逻辑（os.path.exists）
  - 只烧录实际存在的 bin 文件，不存在则跳过
  - 跳过空地址分区（自动分配的分区）
  - 添加清晰的日志输出（✓ 成功 / ⊗ 跳过）
  - 更新 main() 函数调用，传入 BUILD_DIR 参数
  - 支持通过修改 BIN_TYPE 变量切换不同固件目录

#### 需求：保留 NVS 原有参数（g_camera_id、wake_count 等）

在 as_nvs_update.py 生成 bin 烧录之前，使用 as_nvs_read.py 已经读取部分参数，比如 g_camera_id，wake_count。需要将之前的参数也保留下来，使用 as_nvs_update 烧录时恢复之前的参数

- [✓] **需求6: NVS 参数保留和恢复机制** (2025-12-19)
  - 修改 generate_nvs_data() 函数签名，添加 existing_nvs 可选参数
  - 实现参数合并逻辑：原有参数作为基础，新参数覆盖同名参数
  - 添加参数保留和更新的日志输出
  - 更新 as_factory_info.py 中的调用，传入 existing_info
  - 更新 as_model_flash.py 中的调用，传入 nvs_info
  - 保持向后兼容性：existing_nvs 为可选参数，不传则只写入新参数

#### 需求：创建相机时添加 c_sensor 参数

在 camera_data 中新增 c_sensor 参数，从 NVS 的 g_camera_id 读取并赋值给 c_sensor 进行上传

相机数据格式：

```json
{
  "c_sn": "string",
  "c_sensor": "string",
  "c_order": 1,
  "c_status": "NVCONNCTD"
}
```

- [✓] **需求7: 创建相机时添加 c_sensor 参数** (2025-12-19)
  - 修改 as_service_register.main() 函数签名，添加 g_camera_id 可选参数
  - 在创建相机时，如果提供了 g_camera_id，则添加到 camera_data 的 c_sensor 字段
  - 修改 as_factory_info.py 的 request_server() 函数，添加 existing_info 参数
  - 从 existing_info 中提取 g_camera_id 并传递给注册函数
  - 更新 main() 函数调用，传入 existing_info 参数
  - 添加日志输出显示 g_camera_id 的读取和使用情况

#### 需求：修改名称

将 NVS 相关的文件常量名称改为更语义化的名称

- [✓] **需求8: 重命名 NVS 文件常量** (2025-12-19)
  - 修改 as_nvs_read.py 中的常量：
    - NVS_RAW_BIN → READ_BIN = os.path.join(TEMP_DIR, "read.bin")
    - DECODED_CSV → READ_CSV = os.path.join(TEMP_DIR, "read.csv")
  - 修改 as_nvs_update.py 中的常量：
    - FACTORY_CSV → UPDATE_CSV = os.path.join(TEMP_DIR, "update.csv")
    - FACTORY_BIN → UPDATE_BIN = os.path.join(TEMP_DIR, "update.bin")
  - 使用 replace_all 功能替换所有引用
  - 执行代码格式化检查并修复

#### 需求：重命名目录和文件

将固件烧录相关的目录和文件重命名为更规范的名称

- [✓] **需求9: 重命名 as_factory 目录和文件** (2025-12-19)
  - 创建 as_flash_firmware 目录
  - 复制 as_factory 目录下所有文件到 as_flash_firmware/
  - 重命名 as_flash_tool.py 为 as_firmware_tool.py
  - 删除旧的 as_factory 目录
  - 更新 task.md 中的所有引用
  - 更新 CLAUDE.md 中的所有引用
