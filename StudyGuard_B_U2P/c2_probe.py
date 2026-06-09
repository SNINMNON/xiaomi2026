"""C2 raw-link probe for U2P.

This script initializes the U2P-side C2 as coordinator and prints both raw UART
bytes and parsed StudyGuard frames. Use it before running the full state machine
when debugging the U1P -> C2 -> C2 -> U2P link.
"""

import argparse
import binascii
import time

import serial

from c2_receiver import C2Receiver


def main():
    parser = argparse.ArgumentParser(description="Probe U2P C2 raw receive data")
    parser.add_argument("--port", default="/dev/ttyS2")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--seconds", type=float, default=60.0)
    args = parser.parse_args()

    receiver = C2Receiver(args.port, args.baud, timeout=0.2)
    receiver.open()
    print(f"[C2] opened {args.port} at {args.baud}bps")

    ok = receiver.init_as_coordinator()
    print(f"[C2] init_as_coordinator={ok}")
    print(f"[C2] capture {args.seconds:.0f}s; reset/power-cycle U1P now if needed")

    serial_port = receiver.ser
    deadline = time.time() + args.seconds
    raw_total = 0

    while time.time() < deadline:
        waiting = serial_port.in_waiting
        if waiting:
            chunk = serial_port.read(waiting)
            raw_total += len(chunk)
            print(
                "[RAW]",
                len(chunk),
                binascii.hexlify(chunk).decode("ascii"),
                chunk.decode("ascii", errors="replace"),
            )
            receiver._buf += chunk
            receiver._drain()
            while True:
                frame = receiver.get_frame()
                if frame is None:
                    break
                print(f"[FRAME] {frame}")
        else:
            time.sleep(0.05)

    print(f"[C2] done raw_total={raw_total}")
    receiver.close()


if __name__ == "__main__":
    main()
