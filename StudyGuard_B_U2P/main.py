import argparse
import signal
import threading
import time

from admin_api import AdminAPI
from c2_receiver import C2Receiver
from config import (
    DEFAULT_AWAY_TIMEOUT,
    DEFAULT_HTTP_HOST,
    DEFAULT_HTTP_PORT,
    DEFAULT_RESERVE_TIMEOUT,
    DEFAULT_SEATS,
)
from http_server import start_http_server
from seat_state import SeatState, SeatStateMachine
from ui_touch import launch_touch_ui


_STATE_COLORS = {
    SeatState.EMPTY:    '\033[32mEMPTY\033[0m',
    SeatState.RESERVED: '\033[34mRESERVED\033[0m',
    SeatState.USING:    '\033[36mUSING\033[0m',
    SeatState.AWAY:     '\033[33mAWAY\033[0m',
    SeatState.OCCUPY:   '\033[31mOCCUPY\033[0m',
}


def print_status(sm, lock=None):
    if lock is None:
        env = sm.get_env()
        seats = sm.get_all_seats()
    else:
        with lock:
            env = sm.get_env()
            seats = sm.get_all_seats()
    flag = ' \033[31m[BAD_ENV]\033[0m' if env['bad_env'] else ''
    print(f"\n{'='*58}")
    print(f"  StudyGuard  温度:{env['temp']:.1f}C  湿度:{env['humi']:.1f}%RH{flag}")
    print(f"  {'-'*54}")
    for s in seats:
        st = SeatState(s['state'])
        card = s['card'] or '-'
        human = '有人' if s['human'] else '无人'
        extra = f" 离开{s['away_seconds']:.0f}s" if st == SeatState.AWAY else ''
        print(f"  {s['seat']}: {_STATE_COLORS.get(st, st.value)}  卡:{card}  {human}{extra}")
    print(f"{'='*58}\n")


def main():
    p = argparse.ArgumentParser(description='StudyGuard U2P 集成管理终端')
    p.add_argument('--port', default='/dev/ttyS1', help='C2 串口路径')
    p.add_argument('--baud', type=int, default=115200)
    p.add_argument('--seat', default=DEFAULT_SEATS, help='座位列表, 逗号分隔')
    p.add_argument('--away-timeout', type=float, default=DEFAULT_AWAY_TIMEOUT)
    p.add_argument('--reserve-timeout', type=float, default=DEFAULT_RESERVE_TIMEOUT)
    p.add_argument('--http-host', default=DEFAULT_HTTP_HOST)
    p.add_argument('--http-port', type=int, default=DEFAULT_HTTP_PORT)
    p.add_argument('--no-http', action='store_true', help='不启动手机端 HTTP 管理服务')
    p.add_argument('--open-ui', action='store_true', help='启动后在本机打开 E5/本地管理页面')
    p.add_argument('--kiosk', action='store_true', help='用 Chromium kiosk 模式打开 E5 页面')
    p.add_argument('--browser', default=None, help='指定本地浏览器路径')
    args = p.parse_args()

    seat_ids = [x.strip() for x in args.seat.split(',') if x.strip()]

    sm = SeatStateMachine(seat_ids, args.away_timeout, args.reserve_timeout)
    state_lock = threading.RLock()
    api = AdminAPI(sm, state_lock)
    print(f"[SM] 座位: {seat_ids}  离开超时: {args.away_timeout}s  预约超时: {args.reserve_timeout}s")

    httpd = None
    if not args.no_http:
        httpd = start_http_server(api, args.http_host, args.http_port)
        print(f"[HTTP] 管理页面: http://{args.http_host}:{args.http_port}/")
        print(f"[HTTP] 本机 E5 页面: http://127.0.0.1:{args.http_port}/")
        if args.open_ui or args.kiosk:
            ok, url, msg = launch_touch_ui(args.http_port, args.browser, args.kiosk)
            print(f"[UI] {url}  {'已打开' if ok else '未打开'} ({msg})")

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

    print_status(sm, state_lock)
    last_tick = time.time()
    last_print = time.time()

    try:
        while running:
            now = time.time()

            # 处理接收帧
            if has_hw:
                while True:
                    frame = rcv.get_frame()
                    if frame is None:
                        break
                    print(f"[RX] {frame}")
                    with state_lock:
                        changes = sm.handle_frame(frame)
                        bad_env = frame.get('type') == 'ENV' and sm.bad_env
                        temp, humi = sm.temp, sm.humi
                    for sid, old, new in changes:
                        print(f"[状态] {sid}: {old.value} -> {new.value}")
                    if bad_env:
                        print(f"[环境] BAD_ENV  temp={temp:.1f}  humi={humi:.1f}")

            # 定时器
            if now - last_tick >= 1.0:
                with state_lock:
                    tick_changes = sm.tick()
                for sid, old, new in tick_changes:
                    print(f"[超时] {sid}: {old.value} -> {new.value}")
                last_tick = now

            # 周期打印
            if now - last_print >= 5.0:
                print_status(sm, state_lock)
                last_print = now

            time.sleep(0.1)
    finally:
        rcv.close()
        if httpd is not None:
            httpd.shutdown()
            httpd.server_close()
    print("[MAIN] 已退出")


if __name__ == '__main__':
    main()
