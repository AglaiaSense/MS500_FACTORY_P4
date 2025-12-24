- [✓] **g_camera_id 前缀自动修正功能** (2025-12-24)
  - 在 as_nvs_flash/as_nvs_read.py 的 check_nvs_data() 函数中添加自动修正逻辑
  - 检测到 g_camera_id 前 4 位不是 "100B" 时自动替换为 "100B"
  - 所有调用 check_nvs_data() 的模块都会自动获得修正后的 g_camera_id

- [✓] **main.py 添加代码控制开关** (2025-12-24)
  - 添加 ENABLE_STEP1_REGISTER、ENABLE_STEP2_FIRMWARE、ENABLE_STEP3_MODEL 三个开关
  - 类似 C 语言的 #if 0 功能，可以方便地启用/禁用各个步骤
  - 自动显示启用的步骤和跳过的步骤
