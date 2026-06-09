"""
座位状态机模块 (U2P 侧).

职责:
  - 维护每个座位的状态: EMPTY / RESERVED / USING / AWAY / OCCUPY
  - 根据人体感应、刷卡信息和计时器驱动状态转换
  - 监测温湿度, 判断 BAD_ENV 环境异常
  - 对外提供查询和管理接口 (供成员 C 的 UI / HTTP 模块调用)

状态转换规则 (README 第10节):
  EMPTY    --刷卡--> RESERVED
  RESERVED --人入座--> USING        | 超时/再次刷卡 --> EMPTY
  USING    --人离开--> AWAY         | 刷卡 --> EMPTY
  AWAY     --人返回--> USING        | 超时 --> OCCUPY  | 刷卡 --> EMPTY
  OCCUPY   --管理员清除--> EMPTY    | 用户刷卡 --> USING

环境阈值 (README 第7.5节):
  temp < 18 / temp > 30 / humi < 30% / humi > 75%  -> BAD_ENV
"""

import time
from enum import Enum


class SeatState(Enum):
    EMPTY = "EMPTY"
    RESERVED = "RESERVED"
    USING = "USING"
    AWAY = "AWAY"
    OCCUPY = "OCCUPY"


class Seat:
    """单个座位的状态跟踪.

    防抖逻辑 (README 第7.3节):
      human 从 0→1 需持续 3 秒以上 → 确认有人
      human 从 1→0 需持续 5 秒以上 → 确认离开
    """

    DEBOUNCE_PRESENCE = 3.0   # 有人确认延迟 (秒)
    DEBOUNCE_ABSENCE  = 5.0   # 离开确认延迟 (秒)

    def __init__(self, seat_id, away_timeout=30.0, reserve_timeout=60.0):
        self.seat_id = seat_id
        self.state = SeatState.EMPTY
        self.card = None
        self.human = 0                  # 当前确认后的 human 值
        self.raw_human = 0              # 最新的原始 human 值
        self.debounce_start = None      # 防抖计时起点
        self.debounce_target = None     # 防抖目标值 (0 或 1)
        self.away_start = None          # 离开时刻
        self.reserve_start = None       # 预约时刻
        self.away_timeout = away_timeout
        self.reserve_timeout = reserve_timeout

    # -- 事件处理 --

    def on_human(self, value):
        """人体感应原始值变化. 返回 (old_state, new_state) 或 None.

        不直接触发状态转换, 而是启动防抖计时,
        在 on_tick() 中确认稳定后才执行转换.
        """
        old_raw = self.raw_human
        self.raw_human = value

        if value == self.human:
            # 信号回到当前已确认状态, 取消未完成的防抖.
            self.debounce_start = None
            self.debounce_target = None
            return None

        if value == old_raw:
            # 周期性上报同一原始值时保持已有防抖计时.
            return None

        # 值发生了变化, 启动防抖
        self.debounce_start = time.time()
        self.debounce_target = value
        return None

    def _apply_human(self, value):
        """防抖确认后执行状态转换."""
        old = self.state
        self.human = value

        if self.state == SeatState.RESERVED and value == 1:
            self.state = SeatState.USING
            self.reserve_start = None

        elif self.state == SeatState.USING and value == 0:
            self.state = SeatState.AWAY
            self.away_start = time.time()

        elif self.state == SeatState.AWAY and value == 1:
            self.state = SeatState.USING
            self.away_start = None

        if self.state != old:
            return (old, self.state)
        return None

    def on_rfid(self, card):
        """刷卡事件. 返回 (old_state, new_state) 或 None."""
        old = self.state

        if self.state == SeatState.EMPTY:
            # 空闲刷卡 → 预约
            self.state = SeatState.RESERVED
            self.card = card
            self.reserve_start = time.time()

        elif self.state == SeatState.RESERVED:
            if self.card == card:
                self._release()
            else:
                self.card = card
                self.reserve_start = time.time()

        elif self.state == SeatState.USING:
            if self.card == card:
                self._release()

        elif self.state == SeatState.AWAY:
            if self.card == card:
                self._release()

        elif self.state == SeatState.OCCUPY:
            if self.card == card:
                self.state = SeatState.USING
                self.away_start = None

        if self.state != old:
            return (old, self.state)
        return None

    def on_tick(self):
        """定时器检查. 返回 (old_state, new_state) 或 None.

        处理两类超时:
          1) 防抖确认: raw_human 稳定足够时间后生效
          2) 状态超时: 预约超时 / 离开超时
        """
        now = time.time()
        old = self.state

        # 防抖检查: raw_human 值已稳定足够时间则确认
        if self.debounce_start is not None and self.debounce_target is not None:
            elapsed = now - self.debounce_start
            threshold = self.DEBOUNCE_PRESENCE if self.debounce_target == 1 else self.DEBOUNCE_ABSENCE
            if elapsed >= threshold:
                result = self._apply_human(self.debounce_target)
                self.debounce_start = None
                self.debounce_target = None
                if result:
                    return result

        # 状态超时检查
        if self.state == SeatState.RESERVED and self.reserve_start is not None:
            if now - self.reserve_start > self.reserve_timeout:
                self._release()

        elif self.state == SeatState.AWAY and self.away_start is not None:
            if now - self.away_start > self.away_timeout:
                self.state = SeatState.OCCUPY

        if self.state != old:
            return (old, self.state)
        return None

    # -- 管理操作 --

    def admin_clear(self):
        """管理员清除 OCCUPY."""
        if self.state == SeatState.OCCUPY:
            self._release()
            return True
        return False

    def admin_release(self):
        """管理员强制释放."""
        self._release()
        return True

    def _release(self):
        self.state = SeatState.EMPTY
        self.card = None
        self.away_start = None
        self.reserve_start = None

    @property
    def away_seconds(self):
        if self.away_start is not None:
            return time.time() - self.away_start
        return 0.0

    def to_dict(self):
        return {
            'seat': self.seat_id,
            'state': self.state.value,
            'card': self.card,
            'human': self.human,
            'away_seconds': round(self.away_seconds, 1),
        }


class SeatStateMachine:
    """多座位状态机.

    使用方式::

        sm = SeatStateMachine(['A01', 'A02'])
        sm.handle_frame({'type': 'HUMAN', 'seat': 'A01', 'value': 1})
        sm.handle_frame({'type': 'RFID', 'seat': 'A01', 'card': '64680264', 'event': 'scan'})
        sm.handle_frame({'type': 'ENV', 'temp': 27.5, 'humi': 63.4})
        sm.tick()  # 每秒调用, 检查超时
    """

    TEMP_LOW = 18.0
    TEMP_HIGH = 30.0
    HUMI_LOW = 30.0
    HUMI_HIGH = 75.0

    def __init__(self, seat_ids=None, away_timeout=30.0, reserve_timeout=60.0):
        self.seats = {}
        self.temp = 25.0
        self.humi = 50.0
        self.bad_env = False
        self.away_timeout = away_timeout
        self.reserve_timeout = reserve_timeout
        if seat_ids:
            for sid in seat_ids:
                self.add_seat(sid)

    def add_seat(self, seat_id):
        self.seats[seat_id] = Seat(seat_id, self.away_timeout, self.reserve_timeout)

    def set_away_timeout(self, seconds):
        self.away_timeout = float(seconds)
        for s in self.seats.values():
            s.away_timeout = self.away_timeout

    # -- 帧分发 --

    def handle_frame(self, frame):
        """处理来自 c2_receiver 的解析帧.

        Returns:
            list[(seat_id, old_state, new_state)]  状态变化列表
        """
        ftype = frame.get('type', '')
        if ftype == 'HUMAN':
            return self._on_human(frame)
        elif ftype == 'RFID':
            return self._on_rfid(frame)
        elif ftype == 'ENV':
            self._on_env(frame)
        return []

    def _on_human(self, frame):
        seat_id = frame.get('seat', 'A01')
        value = frame.get('value', 0)
        if seat_id not in self.seats:
            self.add_seat(seat_id)
        seat = self.seats[seat_id]
        old = seat.state
        result = seat.on_human(value)
        if result:
            return [(seat_id, old, seat.state)]
        return []

    def _on_rfid(self, frame):
        seat_id = frame.get('seat', 'A01')
        card = frame.get('card', '')
        if seat_id not in self.seats:
            self.add_seat(seat_id)

        # 管理员卡 (FF 开头)
        if card.upper().startswith('FF'):
            seat = self.seats[seat_id]
            old = seat.state
            if seat.admin_clear():
                return [(seat_id, old, seat.state)]
            return []

        seat = self.seats[seat_id]
        old = seat.state
        result = seat.on_rfid(card)
        if result:
            return [(seat_id, old, seat.state)]
        return []

    def _on_env(self, frame):
        self.temp = frame.get('temp', self.temp)
        self.humi = frame.get('humi', self.humi)
        self.bad_env = (
            self.temp < self.TEMP_LOW or self.temp > self.TEMP_HIGH or
            self.humi < self.HUMI_LOW or self.humi > self.HUMI_HIGH
        )

    # -- 定时器 --

    def tick(self):
        """周期性调用, 检查超时. 返回变化列表."""
        changes = []
        for seat in self.seats.values():
            old = seat.state
            if seat.on_tick():
                changes.append((seat.seat_id, old, seat.state))
        return changes

    # -- 查询接口 (供成员 C) --

    def get_seat(self, seat_id):
        seat = self.seats.get(seat_id)
        if seat is None:
            return None
        d = seat.to_dict()
        d['temp'] = self.temp
        d['humi'] = self.humi
        d['bad_env'] = self.bad_env
        return d

    def get_all_seats(self):
        return [self.get_seat(sid) for sid in self.seats]

    def get_env(self):
        return {'temp': self.temp, 'humi': self.humi, 'bad_env': self.bad_env}

    def admin_clear_occupy(self, seat_id):
        seat = self.seats.get(seat_id)
        return seat.admin_clear() if seat else False

    def admin_release_seat(self, seat_id):
        seat = self.seats.get(seat_id)
        return seat.admin_release() if seat else False
