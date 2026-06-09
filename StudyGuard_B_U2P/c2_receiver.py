"""
C2 ZigBee 数据接收与解析模块 (U2P 侧).

职责:
  - 通过 UART 与 U2P 侧 C2 子板通信 (115200 8N1, HEX 命令模式)
  - 初始化 C2 为协调器 (COORDINATOR, PAN_ID=0x3F2C)
  - 后台线程持续接收 C2 转发的 ZigBee 广播数据
  - 解析 HEX 帧 (0xFC) 并提取文本负载
  - 将 HUMAN / RFID / ENV / HB 文本帧解析为结构化字典

协议约定 (来自成员 A):
  HUMAN,seat=A01,value=0        # 人体感应, 0=无人 1=有人
  RFID,seat=A01,card=64680264,event=scan   # 刷卡
  ENV,temp=27.5,humi=63.4       # 温湿度
  HB,u1p=ok                     # 心跳
"""

import serial
import threading
import time
from collections import deque

# ---- C2 HEX 命令 ----
_CMD_READ_DEVICE    = bytes([0xFE, 0x01, 0xFE, 0xFF])
_CMD_SET_COORDINATOR = bytes([0xFD, 0x02, 0x01, 0x00, 0xFF])
_CMD_SET_PAN_ID     = bytes([0xFD, 0x03, 0x03, 0x3F, 0x2C, 0xFF])
_CMD_SET_GROUP      = bytes([0xFD, 0x02, 0x09, 0x01, 0xFF])

_FRAME_HEADER = 0xFC
_TEXT_PREFIXES = (b'HUMAN', b'RFID', b'ENV', b'HB')


def parse_frame(text):
    """解析单行文本协议帧为结构化字典.

    >>> parse_frame("HUMAN,seat=A01,value=1")
    {'type': 'HUMAN', 'seat': 'A01', 'value': 1}
    >>> parse_frame("ENV,temp=27.5,humi=63.4")
    {'type': 'ENV', 'temp': 27.5, 'humi': 63.4}
    """
    if not text:
        return None
    parts = text.split(',')
    result = {'type': parts[0].strip()}
    for kv in parts[1:]:
        kv = kv.strip()
        if '=' not in kv:
            continue
        k, v = kv.split('=', 1)
        k, v = k.strip(), v.strip()
        if k == 'value':
            result[k] = int(v)
        elif k in ('temp', 'humi'):
            result[k] = float(v)
        else:
            result[k] = v
    return result


class C2Receiver:
    """U2P 侧 C2 子板数据接收器.

    使用方式::

        rcv = C2Receiver(port='/dev/ttyS1')
        rcv.open()
        if rcv.init_as_coordinator():
            rcv.start()
        while True:
            frame = rcv.get_frame()
            if frame:
                ...  # 送入状态机
    """

    def __init__(self, port='/dev/ttyS1', baudrate=115200, timeout=0.5):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self._running = False
        self._thread = None
        self._buf = b''
        self._lock = threading.Lock()
        self._queue = deque(maxlen=256)
        self._init_ok = False

    # -- 串口 --

    def open(self):
        self.ser = serial.Serial(
            port=self.port, baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE, timeout=self.timeout)

    def close(self):
        self.stop()
        if self.ser and self.ser.is_open:
            self.ser.close()

    # -- C2 初始化 --

    def init_as_coordinator(self):
        """按 HEX 命令协议初始化 C2 为协调器."""
        if not (self.ser and self.ser.is_open):
            return False
        ok = True
        # 查询设备
        if not self._cmd(_CMD_READ_DEVICE, b'\xFB', 3):
            ok = False
        # 协调器模式
        if not self._cmd(_CMD_SET_COORDINATOR, b'\xFA\x01', 3):
            ok = False
        # PAN_ID = 0x3F2C
        if not self._cmd(_CMD_SET_PAN_ID, b'\xFA\x03', 3):
            ok = False
        # 组播
        if not self._cmd(_CMD_SET_GROUP, b'\xFA\x09', 3):
            ok = False
        self._init_ok = ok
        return ok

    def _cmd(self, cmd, expected_prefix, attempts):
        for _ in range(attempts):
            try:
                self.ser.reset_input_buffer()
                self.ser.write(cmd)
                time.sleep(0.15)
                resp = self.ser.read(32)
                if resp.startswith(expected_prefix):
                    return True
            except (OSError, serial.SerialException):
                pass
        return False

    # -- 接收线程 --

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _loop(self):
        while self._running:
            try:
                if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                    chunk = self.ser.read(self.ser.in_waiting)
                    with self._lock:
                        self._buf += chunk
                    self._drain()
                else:
                    time.sleep(0.02)
            except (OSError, serial.SerialException):
                time.sleep(0.5)

    # -- 帧提取 --

    def _drain(self):
        """从缓冲区提取帧, 写入队列."""
        while True:
            progress = False

            # 方法1: 解析 0xFC HEX 帧
            idx = self._buf.find(bytes([_FRAME_HEADER]))
            if idx >= 0:
                if idx > 0:
                    self._buf = self._buf[idx:]
                    idx = 0
                if len(self._buf) < 2:
                    break
                total_len = self._buf[1]
                if total_len >= 2 and len(self._buf) < 2 + total_len:
                    break
                payload = self._try_fc(idx)
                if payload is not None:
                    self._extract_text(payload)
                    progress = True
                    continue
                # 解析失败, 跳过这个 FC 字节
                self._buf = self._buf[idx + 1:]
                progress = True
                continue

            # 方法2: 搜索文本前缀 (回退策略)
            for prefix in _TEXT_PREFIXES:
                idx = self._buf.find(prefix)
                if idx >= 0:
                    line = self._slice_line(idx)
                    if line:
                        parsed = parse_frame(line)
                        if parsed:
                            with self._lock:
                                self._queue.append(parsed)
                    self._buf = self._buf[idx + len(line):]
                    progress = True
                    break

            if not progress:
                break

    def _try_fc(self, idx):
        """尝试解析 0xFC 帧, 成功返回 payload bytes, 失败返回 None."""
        buf, n = self._buf, len(self._buf)
        if idx + 2 > n:
            return None

        total_len = buf[idx + 1]
        if total_len < 2 or idx + 2 + total_len > n:
            return None

        frame = buf[idx + 2 : idx + 2 + total_len]
        self._buf = buf[idx + 2 + total_len:]

        # 在帧数据中定位 payload: 跳过可能的源地址(2B)和接收选项(1B)
        # payload 为 0x01 mode text 或直接 text
        for offset in range(min(5, len(frame))):
            cand = frame[offset:]
            if len(cand) >= 2 and cand[0] == 0x01:
                return bytes(cand[2:])  # 跳过 01 mode
            if cand and 0x40 <= cand[0] <= 0x7A:
                return bytes(cand)
        return bytes(frame)

    def _extract_text(self, data):
        """从二进制负载中提取文本帧."""
        text = data.decode('ascii', errors='ignore')
        for prefix in _TEXT_PREFIXES:
            p = prefix.decode()
            pos = text.find(p)
            while pos >= 0:
                end = len(text)
                for other in ('HUMAN', 'RFID', 'ENV', 'HB'):
                    if other == p:
                        continue
                    o = text.find(other, pos + 1)
                    if 0 < o < end:
                        end = o
                line = text[pos:end].strip()
                parsed = parse_frame(line)
                if parsed:
                    with self._lock:
                        self._queue.append(parsed)
                text = text[end:]
                pos = text.find(p)

    def _slice_line(self, idx):
        """从 buffer[idx] 切出一行文本."""
        buf = self._buf
        end = len(buf)
        for i in range(idx, len(buf)):
            if buf[i] < 0x20 and buf[i] not in (0x0A, 0x0D):
                end = i
                break
        for prefix in _TEXT_PREFIXES:
            p = buf.find(prefix, idx + 1)
            if 0 < p < end:
                end = p
        return buf[idx:end].decode('ascii', errors='ignore').strip()

    # -- 对外接口 --

    def get_frame(self):
        """非阻塞取一帧, 无数据返回 None."""
        with self._lock:
            return self._queue.popleft() if self._queue else None

    def get_frame_wait(self, timeout=5.0):
        """阻塞等待一帧, 超时返回 None."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if self._queue:
                    return self._queue.popleft()
            time.sleep(0.05)
        return None

    @property
    def is_init_ok(self):
        return self._init_ok

    @property
    def queue_size(self):
        with self._lock:
            return len(self._queue)
