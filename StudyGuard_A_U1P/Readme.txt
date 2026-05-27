StudyGuard_A_U1P

成员 A 端固件：U1P 读取 S7/S5/S8，并通过本地 C2 ZigBee 节点发送给 U2P 侧 C2。

硬件建议：
0#: U2P + C2，用于后续 B/C 成员接收与管理端开发
1#: U1P + C2，本工程烧录到此 U1P
2#: S2/8 温湿度板，兼容 S8 读取逻辑
3#: S5 NFC/RFID
4#: S7 人体感应

C2 拨码要求：
U1P 侧 C2 与 U2P 侧 C2 均置为通信模式/HEX 命令模式。
U1P 固件会将本地 C2 初始化为 TERMINAL，并设置 PAN_ID=0x3F2C。

发送协议：
每一条业务数据都是一行文本帧，字段用英文逗号分隔，键值用等号分隔。
U1P 调用 c2_broadcast_data() 将文本帧封装为 C2 HEX 广播帧后发送。

1. 人体感应帧
格式：
HUMAN,seat=A01,value=0
HUMAN,seat=A01,value=1

字段：
seat: 座位编号，当前固定为 A01
value: 0 表示无人，1 表示有人
发送时机：S7 检测状态变化时发送；串口日志每秒打印原始值 raw/d0/human

2. NFC/RFID 刷卡帧
格式：
RFID,seat=A01,card=64680264,event=scan

字段：
seat: 座位编号，当前固定为 A01
card: S5 读取到的 4 字节 UID，按十六进制大写/数字字符串输出
event: 固定为 scan，表示检测到一次刷卡
发送时机：检测到新卡或卡号变化时发送

3. 温湿度环境帧
格式：
ENV,temp=27.5,humi=63.4

字段：
temp: 摄氏温度，保留 1 位小数
humi: 相对湿度百分比，保留 1 位小数
发送时机：每 3 秒发送一次

4. 心跳帧
格式：
HB,u1p=ok

字段：
u1p: 固定为 ok，表示 U1P 端主循环正常运行
发送时机：启动后发送一次，之后每 10 秒发送一次

串口验证示例：
[I2C] S7=1 S5=1 S8=1
[C2] init ok, mode=TERMINAL
[TX] HUMAN,seat=A01,value=1
[TX] RFID,seat=A01,card=64680264,event=scan
[TX] ENV,temp=27.5,humi=63.4
[TX] HB,u1p=ok

构建烧录：
进入 demo/Project/CMAKE_Project，双击 build_and_flash.bat。
生成文件位于 build_sg/STUDYGUARD_A_U1P.hex。
