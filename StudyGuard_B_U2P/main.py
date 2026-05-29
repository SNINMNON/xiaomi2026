"""
StudyGuard U2P 端主程序 (成员 B 交付版本).

启动 C2 数据接收 + 座位状态机, 终端打印状态变化.
成员 C 将在此基础上集成 E5 触摸屏 UI 和 HTTP 管理服务.

用法:
  python main.py --port /dev/ttyS1 --seat A01,A02 --away-timeout 30
"""

import argparse
import signal
import sys
import time

from c2_receiver import C2Receiver
from seat_state import SeatState, SeatStateMachine


_STATE_COLORS = {
    SeatState.EMPTY:    '\033[32mEMPTY\033[0m',
    SeatState.RESERVED: '\033[34mRESERVED\033[0m',
    SeatState.USING:    '\033[36mUSING\033[0m',
    SeatState.AWAY:     '\033[33mAWAY\033[0m',
    SeatState.OCCUPY:   '\033[31mOCCUPY\033[0m',
}


def print_status(sm):
    env = sm.get_env()
    flag = ' \033[31m[BAD_ENV]\033[0m' if env['bad_env'] else ''
    print(f"\n{'='*58}")
    print(f"  StudyGuard  温度:{env['temp']:.1f}C  湿度:{env['humi']:.1f}%RH{flag}")
    print(f"  {'-'*54}")
    for s in sm.get_all_seats():
        st = SeatState(s['state'])
        card = s['card'] or '-'
        human = '有人' if s['human'] else '无人'
        extra = f" 离开{s['away_seconds']:.0f}s" if st == SeatState.AWAY else ''
        print(f"  {s['seat']}: {_STATE_COLORS.get(st, st.value)}  卡:{card}  {human}{extra}")
    print(f"{'='*58}\n")


def main():
    p = argparse.ArgumentParser(description='StudyGuard U2P 状态管理')
    p.add_argument('--port', default='/dev/ttyS1', help='C2 串口路径')
    p.add_argument('--baud', type=int, default=115200)
    p.add_argument('--seat', default='A01', help='座位列表, 逗号分隔')
    p.add_argument('--away-timeout', type=float, default=30.0)
    p.add_argument('--reserve-timeout', type=float, default=60.0)
    args = p.parse_args()

    seat_ids = [x.strip() for x in args.seat.split(',') if x.strip()]

    sm = SeatStateMachine(seat_ids, args.away_timeout, args.reserve_timeout)
    print(f"[SM] 座位: {seat_ids}  离开超时: {args.away_timeout}s  预约超时: {args.reserve_timeout}s")

    rcv = C2Receiver(args.port, args.baud)
    has_hw = False
    try:
        rcv.open()
        print(f"[C2] {args.port} 已打开, {args.baud}bps")
        has_hw = True
    except Exception as e:
        print(f"[C2] 串口不可用: {e}")
        print("[C2] 纯状态机模式 (无硬件)")

    if has_hw:
        print("[C2] 初始化协调器...")
        ok = rcv.init_as_coordinator()
        print(f"[C2] 初始化{'成功' if ok else '失败, 将继续接收'}")
        rcv.start()

    running = True

    def on_signal(sig, frame):
        nonlocal running
        print("\n[MAIN] 退出中...")
        running = False

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    print_status(sm)
    last_tick = time.time()
    last_print = time.time()

    while running:
        now = time.time()

        # 处理接收帧
        if has_hw:
            while True:
                frame = rcv.get_frame()
                if frame is None:
                    break
                for sid, old, new in sm.handle_frame(frame):
                    print(f"[状态] {sid}: {old.value} -> {new.value}")
                if frame.get('type') == 'ENV' and sm.bad_env:
                    print(f"[环境] BAD_ENV  temp={sm.temp:.1f}  humi={sm.humi:.1f}")

        # 定时器
        if now - last_tick >= 1.0:
            for sid, old, new in sm.tick():
                print(f"[超时] {sid}: {old.value} -> {new.value}")
            last_tick = now

        # 周期打印
        if now - last_print >= 5.0:
            print_status(sm)
            last_print = now

        time.sleep(0.1)

    rcv.close()
    print("[MAIN] 已退出")


if __name__ == '__main__':
    main()
