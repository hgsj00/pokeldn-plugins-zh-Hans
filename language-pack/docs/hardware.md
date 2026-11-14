---
title: 硬件与设置
nav_order: 9
has_children: true
---

# 硬件与设置

射频部分是一块通过 USB 串口连接、运行 `firmware/esp32` 的 ESP32 开发板；LDN、Pia 与游戏则以 Python 运行在主机上，无需 root 权限，也无需 Wi-Fi 驱动。所有游戏都通过它进行交换。Linux 主机也可以直接驱动一块支持 AP 模式的 Wi-Fi 网卡；该方案属于旧式做法。

## 页面

- [ESP32 射频](hardware_esp32.md)：开发板、其固件、串口协议与测量数据。
- [Switch 密钥](hardware_switch_keys.md)：安全地安装 `prod.keys`。
- [适配器](hardware_adapters.md)：Linux Wi-Fi 网卡、其配置与故障模式。
- [控制器开发板](hardware_pad.md)：一块 ESP32-S3，主机将其识别为有线控制器，并通过蓝牙 LE 驱动；或一块经典 ESP32，主机将其配对为 Pro 控制器，并通过 USB 串口驱动。
- [树莓派主机](hardware_raspberry_pi.md)：Linux 部署方式，以及受监管的神秘礼物运行器。
