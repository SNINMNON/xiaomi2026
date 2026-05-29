# StudyGuard B 成员交付报告

## 交付范围

本工程为 StudyGuard 项目的 U2P 端状态管理与数据接收模块，严格按 README §15.1 成员 B 分工完成：

- U2P 侧 C2 ZigBee 数据接收 (c2_receiver.py)
- 文本协议解析 (HUMAN / RFID / ENV / HB)
- 座位状态机 (EMPTY / RESERVED / USING / AWAY / OCCUPY)
- 环境数据融合与 BAD_ENV 判断
- 人体感应、刷卡信息与计时器融合

## 文件清单

```text
StudyGuard_B_U2P/
  c2_receiver.py      # C2 串口通信与数据解析模块
  seat_state.py       # 座位状态机模块
  main.py             # 最小演示入口 (供成员 C 集成)
  B成员交付报告.md     # 本文件
```

## 模块说明

### c2_receiver.py

- 通过 UART (115200 8N1) 与 U2P 侧 C2 子板通信
- 按 HEX 命令协议初始化 C2 为 COORDINATOR (PAN_ID=0x3F2C)
- 后台线程持续接收, 双策略解析:
  1. HEX 帧解析 (0xFC 帧头, 兼容多版本 E18 固件格式)
  2. 文本前缀搜索回退 (HUMAN/RFID/ENV/HB)
- 输出结构化字典: `{'type': 'HUMAN', 'seat': 'A01', 'value': 1}` 等

**关键接口:**

| 方法 | 说明 |
|---|---|
| `C2Receiver(port, baudrate)` | 构造, 默认 /dev/ttyS1, 115200 |
| `open()` / `close()` | 串口开关 |
| `init_as_coordinator()` | C2 初始化, 返回 bool |
| `start()` / `stop()` | 后台接收线程 |
| `get_frame()` | 非阻塞取帧 |
| `get_frame_wait(timeout)` | 阻塞取帧 |

### seat_state.py

- `SeatState` 枚举: EMPTY, RESERVED, USING, AWAY, OCCUPY
- `Seat` 类: 单座位状态跟踪, 含 `on_human()`, `on_rfid()`, `on_tick()`, `admin_clear()`, `admin_release()`
- `SeatStateMachine` 类: 多座位管理, 帧分发, 环境阈值判断, 查询接口

**人体感应防抖 (README §7.3):**

| 条件 | 防抖延迟 | 说明 |
|---|---|---|
| human 0→1 | **3 秒** | 持续有人 3 秒后才确认入座, 避免误触发 |
| human 1→0 | **5 秒** | 持续无人 5 秒后才确认离开, 避免短暂离席误判 |

防抖期间若感应值变回原值, 计时自动取消, 不触发状态转换。

**状态转换 (README §10):**

```text
EMPTY --刷卡--> RESERVED --人入座--> USING --人离开--> AWAY --超时--> OCCUPY
  ↑               ↑                    │   ↑          │         │
  └──取消/超时────┘                    │   └──人返回──┘         │
  ←──────────刷卡签退──────────────────┘                        │
  ←──────────管理员清除─────────────────────────────────────────┘
  ←──────────用户刷卡确认 (OCCUPY → USING)──────────────────────┘
```

**环境阈值 (README §7.5):** temp<18 / temp>30 / humi<30% / humi>75% → BAD_ENV

**超时默认值:**

| 超时类型 | 默认值 | 说明 |
|---|---|---|
| 人体感应防抖 (有人) | 3s | human=1 持续 3s 确认入座 |
| 人体感应防抖 (离开) | 5s | human=0 持续 5s 确认离开 |
| 离开超时 (AWAY→OCCUPY) | 30s | `--away-timeout` 可配置 |
| 预约超时 (RESERVED→EMPTY) | 60s | `--reserve-timeout` 可配置 |

### main.py

最小演示入口, 启动 C2 接收线程 + 状态机循环, 终端实时打印状态。
成员 C 将在此基础上添加 E5 UI 和 HTTP 服务。

```bash
sudo python3 main.py --port /dev/ttyS2 --seat A01 --away-timeout 30
```

## 与成员 A 的协议约定

接收并解析 A 端通过 C2 广播以下文本帧:

```text
HUMAN,seat=A01,value=0        # 人体感应 (0=无人, 1=有人)
HUMAN,seat=A01,value=1
RFID,seat=A01,card=64680264,event=scan   # NFC/RFID 刷卡
ENV,temp=27.5,humi=63.4       # 温湿度 (1位小数)
HB,u1p=ok                     # 心跳
```

## C2 配置

```text
两块 C2: HEX 命令模式
PAN_ID: 0x3F2C
U1P 侧: TERMINAL (成员 A 代码配置)
U2P 侧: COORDINATOR (本工程 c2_receiver.py 配置)
UART: 115200 8N1
```

## U2P 运行指南

### 前置条件

1. U2P 已通过 SSH 或串口登录
2. Python3 和 pyserial 已安装：`pip3 install pyserial`
3. 代码已上传到 U2P 的 `/home/sunrise/StudyGuard_B_U2P/`

### 确定 C2 串口

C2 子板插在 U2P 上后，通过 PogoPin UART2 通信，Linux 设备为 `/dev/ttyS2`：

```bash
ls /dev/ttyS*
# 输出: /dev/ttyS0  /dev/ttyS1  /dev/ttyS2
```

### 运行

```bash
cd ~/StudyGuard_B_U2P
sudo python3 main.py --port /dev/ttyS2 --seat A01 --away-timeout 30 --reserve-timeout 60
```

> **注意**：串口设备需要 root 权限，所以必须加 `sudo`。不想每次 `sudo` 的话，执行一次 `sudo usermod -a -G dialout sunrise` 后重新 SSH 即可。

### 停止

在运行窗口按 `Ctrl+C`。
