#!/usr/bin/env python3
"""
分区信息工具模块
功能：从 partitions.csv 文件中读取分区偏移地址和大小
"""

import os
import csv


#------------------  分区信息解析  ------------------


def parse_partitions_csv(csv_path):
    """
    解析 ESP-IDF 格式的分区表文件

    参数:
        csv_path: partitions.csv 文件路径

    返回:
        分区信息字典 {分区名: {"offset": "0x...", "size": "0x..."}}
        如果文件不存在或解析失败，返回空字典
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Partition table file not found: {csv_path}")

    partitions = {}
    current_offset = 0

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
                # 跳过空行和注释行
                if not row or row[0].strip().startswith("#"):
                    continue

                # 解析分区信息: Name, Type, SubType, Offset, Size
                if len(row) >= 5:
                    name = row[0].strip()
                    offset_str = row[3].strip().rstrip(",")
                    size_str = row[4].strip().rstrip(",")

                    # 处理偏移地址（如果为空，使用当前偏移）
                    if offset_str:
                        offset = int(offset_str, 16) if offset_str.startswith("0x") else int(offset_str)
                    else:
                        # 偏移地址为空，使用当前累计偏移
                        offset = current_offset

                    # 处理大小
                    if size_str:
                        size = int(size_str, 16) if size_str.startswith("0x") else int(size_str)
                    else:
                        size = 0

                    # 存储分区信息
                    partitions[name] = {
                        "offset": f"0x{offset:X}",
                        "size": f"0x{size:X}",
                    }

                    # 更新当前偏移（用于下一个没有明确偏移的分区）
                    current_offset = offset + size

    except Exception as e:
        raise RuntimeError(f"Failed to parse partition table: {e}")

    return partitions


def get_partition_info(bin_type, partition_name):
    """
    获取指定固件类型和分区的信息

    参数:
        bin_type: 固件类型（例如：sdk_uvc_tw_plate, ped_alarm, ms500_uvc）
        partition_name: 分区名称（例如：nvs, storage_dl）

    返回:
        包含 offset 和 size 的字典 {"offset": "0x...", "size": "0x..."}
        如果分区不存在，返回 None
    """
    # 构建 partitions.csv 路径
    bin_dir = os.path.join(os.path.dirname(__file__), "bin_type", bin_type)
    csv_path = os.path.join(bin_dir, "partitions.csv")

    # 解析分区表
    partitions = parse_partitions_csv(csv_path)

    # 返回指定分区的信息
    return partitions.get(partition_name)


def get_nvs_info(bin_type):
    """
    获取 NVS 分区信息

    参数:
        bin_type: 固件类型

    返回:
        包含 offset 和 size 的字典 {"offset": "0x...", "size": "0x..."}
    """
    return get_partition_info(bin_type, "nvs")


def get_storage_dl_info(bin_type):
    """
    获取 storage_dl 分区信息

    参数:
        bin_type: 固件类型

    返回:
        包含 offset 和 size 的字典 {"offset": "0x...", "size": "0x..."}
    """
    return get_partition_info(bin_type, "storage_dl")


#------------------  测试代码  ------------------


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("Partition Information Tool - Test")
    print("=" * 60)

    bin_types = ["sdk_uvc_tw_plate", "ped_alarm", "ms500_uvc"]

    for bin_type in bin_types:
        print(f"\nFirmware type: {bin_type}")
        print("-" * 60)

        try:
            # 测试 NVS 分区
            nvs_info = get_nvs_info(bin_type)
            if nvs_info:
                print(f"  NVS partition:")
                print(f"    Offset: {nvs_info['offset']}")
                print(f"    Size:   {nvs_info['size']}")

            # 测试 storage_dl 分区
            storage_dl_info = get_storage_dl_info(bin_type)
            if storage_dl_info:
                print(f"  storage_dl partition:")
                print(f"    Offset: {storage_dl_info['offset']}")
                print(f"    Size:   {storage_dl_info['size']}")

        except Exception as e:
            print(f"  Error: {e}")

    print("\n" + "=" * 60)
