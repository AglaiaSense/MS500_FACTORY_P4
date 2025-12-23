- [✓] **优化as_model_conversion** (2025-12-23)
  - 删除 model_config.json，不再使用配置文件
  - 重构 as_model_auth.py：
    - type_model 目录仅存放模型文件（packerOut.zip 和 network_info.txt）
    - 外部接口改为 device_id 和 model_type 两个参数
    - packerOut.zip 路径自动拼接：as_model_conversion/type_model/{model_type}/packerOut.zip
    - 工作目录改为：as_model_conversion/temp/{device_id}/
    - output 目录：temp/{device_id}/output
    - spiffs_dl 目录：temp/{device_id}/spiffs_dl
  - 实现 5 步分层处理：
    1. 创建工作目录
    2. 模型转换（调用 model_convert）
    3. ZIP 解压缩
    4. 复制烧录文件（network.fpk + network_info.txt）
    5. 组装并验证 spiffs_dl 目录
