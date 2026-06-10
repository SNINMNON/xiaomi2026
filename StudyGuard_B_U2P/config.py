"""
Shared configuration for the U2P management side.

Member C modules import these defaults, while command-line arguments in
main.py can still override the runtime values for demos and debugging.
"""

DEFAULT_SEATS = "A01"
DEFAULT_HTTP_HOST = "0.0.0.0"
DEFAULT_HTTP_PORT = 8080
DEFAULT_AWAY_TIMEOUT = 30.0
DEFAULT_RESERVE_TIMEOUT = 60.0

MIN_AWAY_TIMEOUT = 1.0
MAX_AWAY_TIMEOUT = 3600.0

STATE_LABELS = {
    "EMPTY": "空闲",
    "RESERVED": "已预约",
    "USING": "使用中",
    "AWAY": "临时离开",
    "OCCUPY": "疑似占座",
}
