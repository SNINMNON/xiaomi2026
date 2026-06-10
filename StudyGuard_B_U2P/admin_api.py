"""
Admin API facade for member C.

This module keeps HTTP/UI code away from the internal state-machine details.
All public methods return JSON-serializable dictionaries.
"""

import threading
import time

from config import MAX_AWAY_TIMEOUT, MIN_AWAY_TIMEOUT, STATE_LABELS


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


class AdminAPI:
    def __init__(self, state_machine, lock=None):
        self.sm = state_machine
        self.lock = lock or threading.RLock()
        self.started_at = time.time()

    def list_seats(self):
        with self.lock:
            seats = [self._decorate_seat(s) for s in self.sm.get_all_seats()]
            return {
                "ok": True,
                "seats": seats,
                "env": self.sm.get_env(),
                "config": self.get_config(),
                "updated_at": time.time(),
            }

    def get_seat(self, seat_id):
        with self.lock:
            seat = self.sm.get_seat(seat_id)
            if seat is None:
                raise ApiError(404, "seat not found")
            return {"ok": True, "seat": self._decorate_seat(seat)}

    def get_env(self):
        with self.lock:
            return {"ok": True, "env": self.sm.get_env(), "updated_at": time.time()}

    def get_config(self):
        with self.lock:
            return {
                "away_timeout": self.sm.away_timeout,
                "reserve_timeout": self.sm.reserve_timeout,
                "min_away_timeout": MIN_AWAY_TIMEOUT,
                "max_away_timeout": MAX_AWAY_TIMEOUT,
            }

    def set_away_timeout(self, seconds):
        try:
            value = float(seconds)
        except (TypeError, ValueError):
            raise ApiError(400, "timeout must be a number")
        if value < MIN_AWAY_TIMEOUT or value > MAX_AWAY_TIMEOUT:
            raise ApiError(
                400,
                "timeout must be between %.0f and %.0f seconds"
                % (MIN_AWAY_TIMEOUT, MAX_AWAY_TIMEOUT),
            )
        with self.lock:
            self.sm.set_away_timeout(value)
            return {"ok": True, "config": self.get_config()}

    def clear_occupy(self, seat_id):
        with self.lock:
            if self.sm.get_seat(seat_id) is None:
                raise ApiError(404, "seat not found")
            changed = self.sm.admin_clear_occupy(seat_id)
            seat = self._decorate_seat(self.sm.get_seat(seat_id))
            return {
                "ok": changed,
                "changed": changed,
                "seat": seat,
                "message": "cleared" if changed else "seat is not OCCUPY",
            }

    def release_seat(self, seat_id):
        with self.lock:
            if self.sm.get_seat(seat_id) is None:
                raise ApiError(404, "seat not found")
            changed = self.sm.admin_release_seat(seat_id)
            return {
                "ok": changed,
                "changed": changed,
                "seat": self._decorate_seat(self.sm.get_seat(seat_id)),
                "message": "released",
            }

    def _decorate_seat(self, seat):
        if seat is None:
            return None
        data = dict(seat)
        data["state_label"] = STATE_LABELS.get(data.get("state"), data.get("state", ""))
        data["human_label"] = "有人" if data.get("human") else "无人"
        return data
