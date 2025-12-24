
需求: 使用as_factory_firmware.py的main烧录函数烧录固件，指定端口为COM4，bin_type为sdk_uvc_tw_plate，输出日志内容。请给出完整的日志输出内容。
应该是有 storage.bin和 storage_dl.bin两个文件进行烧录
步骤0: 读取分区表配置
============================================================
固件目录: E:\03-MS500-P4\01.code\MS500_Factory_P4\as_flash_firmware\bin_type\sdk_uvc_tw_plate
分区表文件: E:\03-MS500-P4\01.code\MS500_Factory_P4\as_flash_firmware\bin_type\sdk_uvc_tw_plate\partitions.csv

  ✓ 0x2000 <- bootloader.bin
  ✓ 0x8000 <- partition-table.bin
  ✓ 0xd000 <- ota_data_initial.bin
  ⊗ 跳过: ms500_p4.bin (分区 'ota_0' 未在 partitions.csv 中定义)
  ✓ 0x10000 <- ms500_p4.bin
  ⊗ 跳过: storage.bin (分区 'storage' 未在 partitions.csv 中定义)
  ⊗ 跳过: storage_dl.bin (分区 'storage_dl' 未在 partitions.csv 中定义)

✓ 成功加载 4 个烧录文件配置
============================================================
步骤1: 检查固件文件
============================================================
  ✓ bootloader.bin (14496 bytes)
  ✓ partition-table.bin (3072 bytes)
  ✓ ota_data_initial.bin (8192 bytes)
  ✓ ms500_p4.bin (1831968 bytes)