# MS500 配置参数说明

`as_ms500_config.json` 配置文件参数速查表。

---

## BIN_TYPE（固件类型）

| 配置值           | 作用             |
| ---------------- | ---------------- |
| ped_alarm        | 行人检测固件     |
| sdk_uvc_tw_plate | 台湾车牌识别固件 |



---

## MODEL_TYPE（AI 模型类型）

| 配置值           |                  |
| ---------------- | ---------------- |
| ped_alarm        | 行人检测模型     |
| sdk_uvc_tw_plate | 台湾车牌识别模型 |



---

## server_url（服务器地址）

| 配置值     | 作用                          |
| ---------- | ---------------------------- |
| 局域网     | http://192.168.0.6:8000      |
| 测试服务器 | https://dm-be.leopardaws.com |
| 生产服务器 | https://gs-be.leopardaws.com |



---

## 配置示例

```json
{
  "server_url": "http://192.168.0.6:8000",
  "c_sn": "CA500-MIPI-zlxc-0059",
  "u_sn": "MS500-H120-EP-zlcu-0059",
  "PORT": "COM4",
  "BIN_TYPE": "ped_alarm",
  "MODEL_TYPE": "ped_alarm"
}
```
