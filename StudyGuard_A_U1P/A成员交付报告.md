# StudyGuard A 成员交付报告

## 交付范围

本工程为 StudyGuard 项目的 U1P 座位端固件，负责成员 A 的工作：

- 读取 S7 人体感应状态。
- 读取 S5 NFC/RFID 卡号。
- 读取 S8/S2-8 温湿度数据。
- 初始化 U1P 侧本地 C2。
- 将采集结果打包为文本协议帧。
- 通过 U1P 与 C2 之间的 UART 调用 C2 广播发送。

主程序：

```text
demo/Project/Application/src/c2_demo.c
```

## 已验证功能

串口日志已验证以下功能正常：

![串口日志截图](.\image.png)

说明：

- `S7=1` 表示人体感应板被 I2C 识别。
- `S5=1` 表示 NFC/RFID 板被 I2C 识别。
- `S8=1` 表示温湿度板被 I2C 识别。
- `C2 init ok` 表示 U1P 已通过 UART 将本地 C2 初始化为终端节点。
- `[TX]` 表示 U1P 已生成业务帧并调用 C2 广播发送函数。

完整无线接收效果需要 B 成员在 U2P 侧 C2 接收程序中进一步联调确认。

## 硬件连接

当前建议摆放：

```text
0#: U2P + C2，后续 B/C 成员使用
1#: U1P + C2，本工程运行节点
2#: S2/8 温湿度板，按 S8 驱动读取
3#: S5 NFC/RFID
4#: S7 人体感应
```

C2 要求：

```text
两块 C2 均为通信模式 / HEX 命令模式
PAN_ID: 0x3F2C
U1P 侧 C2: TERMINAL
U2P 侧 C2: COORDINATOR 或接收节点
```

## 接口发送协议

业务层使用一行一帧的文本协议。字段用英文逗号分隔，键和值用等号分隔。

### 1. 人体感应帧

格式：

```text
HUMAN,seat=A01,value=0
HUMAN,seat=A01,value=1
```

字段说明：

```text
seat  : 座位编号，当前固定 A01
value : 0=无人，1=有人
```

发送时机：

```text
S7 检测状态发生变化时发送。
```

### 2. NFC/RFID 刷卡帧

格式：

```text
RFID,seat=A01,card=64680264,event=scan
```

字段说明：

```text
seat  : 座位编号，当前固定 A01
card  : S5 读取到的 4 字节 UID，按十六进制字符串输出
event : 固定 scan，表示检测到一次刷卡
```

发送时机：

```text
检测到新卡或卡号变化时发送。
```

### 3. 温湿度环境帧

格式：

```text
ENV,temp=27.5,humi=63.4
```

字段说明：

```text
temp : 摄氏温度，保留 1 位小数
humi : 相对湿度百分比，保留 1 位小数
```

发送时机：

```text
每 3 秒发送一次。
```

### 4. 心跳帧

格式：

```text
HB,u1p=ok
```

字段说明：

```text
u1p : 固定 ok，表示 U1P 主循环正常运行
```

发送时机：

```text
启动后发送一次，之后每 10 秒发送一次。
```

## B 成员接收建议

U2P 侧接收到 C2 串口数据后，建议按以下逻辑解析：

```text
1. 找到 ASCII 文本内容。
2. 按帧类型前缀判断：
   HUMAN
   RFID
   ENV
   HB
3. 对逗号分隔字段做 key=value 解析。
4. 将 seat=A01 的数据送入 seat_state.py 状态机。
```

建议状态机输入结构：

```json
{
  "type": "HUMAN",
  "seat": "A01",
  "value": 1
}
```

```json
{
  "type": "RFID",
  "seat": "A01",
  "card": "64680264",
  "event": "scan"
}
```

```json
{
  "type": "ENV",
  "temp": 27.5,
  "humi": 63.4
}
```

## 后续联调事项

- B 成员需要在 U2P 侧 C2 接收程序中确认能收到上述文本帧。
- 如果 U2P 收不到，优先检查两块 C2 的拨码模式、PAN_ID、节点类型和 U2P 侧 UART 参数。
- A 端已通过调试串口确认业务帧生成和 C2 发送函数调用正常。

## 构建烧录

运行：

```text
StudyGuard_A_U1P\demo\Project\CMAKE_Project\build_and_flash.bat
```

生成固件：

```text
demo/Project/CMAKE_Project/build_sg/STUDYGUARD_A_U1P.hex
```
