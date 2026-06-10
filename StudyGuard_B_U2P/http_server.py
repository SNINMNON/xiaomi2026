"""
HTTP server and browser management page for the U2P side.

Endpoints follow README section 8.3:
  GET  /api/seats
  GET  /api/seats/<seat_id>
  POST /api/seats/<seat_id>/clear
  POST /api/seats/<seat_id>/release
  GET  /api/env
  POST /api/config/timeout
"""

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from admin_api import ApiError


DESKTOP_HTML_PATH = "/home/sunrise/Desktop/studyguard.html"


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>StudyGuard 管理终端</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f7f8;
      --panel: #ffffff;
      --ink: #182026;
      --muted: #697782;
      --line: #d9e0e5;
      --empty: #2f8f5b;
      --reserved: #286bb0;
      --using: #087c84;
      --away: #ad6b00;
      --occupy: #bd3434;
      --bad: #b42318;
      --focus: #1d4ed8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
      letter-spacing: 0;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 16px 20px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      position: sticky;
      top: 0;
      z-index: 2;
    }
    h1 { margin: 0; font-size: 22px; font-weight: 700; }
    .env { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; color: var(--muted); }
    .badge {
      min-height: 28px;
      padding: 4px 10px;
      border-radius: 6px;
      border: 1px solid var(--line);
      background: #fff;
      font-weight: 600;
      color: var(--ink);
    }
    .badge.bad { border-color: #f1b5af; color: var(--bad); background: #fff4f2; }
    main {
      display: grid;
      grid-template-columns: minmax(280px, 1fr) minmax(300px, 380px);
      gap: 18px;
      padding: 18px;
      max-width: 1180px;
      margin: 0 auto;
    }
    .section-title { margin: 0 0 10px; font-size: 15px; color: var(--muted); font-weight: 700; }
    .seat-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 10px;
    }
    .seat {
      min-height: 108px;
      border: 1px solid var(--line);
      background: var(--panel);
      border-left: 7px solid var(--empty);
      border-radius: 8px;
      padding: 12px;
      text-align: left;
      cursor: pointer;
      display: grid;
      align-content: space-between;
      gap: 8px;
    }
    .seat:focus { outline: 3px solid rgba(29, 78, 216, .22); }
    .seat.selected { border-color: var(--focus); box-shadow: 0 0 0 2px rgba(29, 78, 216, .12); }
    .seat.RESERVED { border-left-color: var(--reserved); }
    .seat.USING { border-left-color: var(--using); }
    .seat.AWAY { border-left-color: var(--away); }
    .seat.OCCUPY { border-left-color: var(--occupy); }
    .seat-name { font-size: 22px; font-weight: 800; }
    .seat-state { font-size: 14px; font-weight: 700; }
    .seat-meta { color: var(--muted); font-size: 13px; }
    .detail, .controls {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 14px;
    }
    .row {
      display: flex;
      justify-content: space-between;
      gap: 14px;
      padding: 8px 0;
      border-bottom: 1px solid #edf1f3;
    }
    .row:last-child { border-bottom: 0; }
    .label { color: var(--muted); }
    .value { font-weight: 700; text-align: right; overflow-wrap: anywhere; }
    button {
      min-height: 40px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 6px;
      padding: 8px 12px;
      font-weight: 700;
      cursor: pointer;
    }
    button.primary { border-color: #aac5e8; background: #eef6ff; color: #164d8f; }
    button.danger { border-color: #efb3ad; background: #fff4f2; color: var(--bad); }
    button:disabled { opacity: .45; cursor: not-allowed; }
    .buttons { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; }
    .timeout { display: grid; grid-template-columns: 1fr auto; gap: 8px; margin-top: 8px; }
    input {
      min-height: 40px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      font: inherit;
      width: 100%;
    }
    .status-line { min-height: 22px; color: var(--muted); font-size: 13px; margin-top: 8px; }
    @media (max-width: 760px) {
      header { align-items: flex-start; flex-direction: column; }
      main { grid-template-columns: 1fr; padding: 12px; }
      .seat-grid { grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); }
    }
  </style>
</head>
<body>
  <header>
    <h1>StudyGuard 管理终端</h1>
    <div class="env">
      <span class="badge" id="temp">温度 --</span>
      <span class="badge" id="humi">湿度 --</span>
      <span class="badge" id="envFlag">环境正常</span>
    </div>
  </header>
  <main>
    <section>
      <p class="section-title">座位地图</p>
      <div class="seat-grid" id="seatGrid"></div>
    </section>
    <aside>
      <div class="detail">
        <p class="section-title">座位详情</p>
        <div id="detail"></div>
        <div class="buttons">
          <button class="danger" id="clearBtn">清除占座</button>
          <button class="primary" id="releaseBtn">强制释放</button>
        </div>
      </div>
      <div class="controls">
        <p class="section-title">离开超时</p>
        <div class="timeout">
          <input id="timeoutInput" type="number" min="1" max="3600" step="1">
          <button id="saveTimeout">保存</button>
        </div>
        <div class="status-line" id="statusLine"></div>
      </div>
    </aside>
  </main>
  <script>
    let seats = [];
    let selectedSeat = null;

    function qs(id) { return document.getElementById(id); }
    function stateClass(state) { return ["EMPTY","RESERVED","USING","AWAY","OCCUPY"].includes(state) ? state : "EMPTY"; }
    function setStatus(text) { qs("statusLine").textContent = text || ""; }

    async function requestJson(url, options) {
      const res = await fetch(url, options || {});
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || ("HTTP " + res.status));
      return data;
    }

    function renderEnv(env) {
      qs("temp").textContent = "温度 " + Number(env.temp || 0).toFixed(1) + "C";
      qs("humi").textContent = "湿度 " + Number(env.humi || 0).toFixed(1) + "%RH";
      const flag = qs("envFlag");
      flag.textContent = env.bad_env ? "BAD_ENV" : "环境正常";
      flag.classList.toggle("bad", !!env.bad_env);
    }

    function renderSeats() {
      const grid = qs("seatGrid");
      grid.innerHTML = "";
      seats.forEach((seat) => {
        const btn = document.createElement("button");
        btn.className = "seat " + stateClass(seat.state) + (seat.seat === selectedSeat ? " selected" : "");
        btn.type = "button";
        btn.innerHTML =
          '<div class="seat-name">' + seat.seat + '</div>' +
          '<div class="seat-state">' + (seat.state_label || seat.state) + '</div>' +
          '<div class="seat-meta">' + (seat.human_label || "") + ' / 卡 ' + (seat.card || "-") + '</div>';
        btn.onclick = () => { selectedSeat = seat.seat; renderSeats(); renderDetail(); };
        grid.appendChild(btn);
      });
      if (!selectedSeat && seats.length) selectedSeat = seats[0].seat;
    }

    function renderDetail() {
      const seat = seats.find((s) => s.seat === selectedSeat);
      const detail = qs("detail");
      const clearBtn = qs("clearBtn");
      const releaseBtn = qs("releaseBtn");
      if (!seat) {
        detail.innerHTML = '<div class="row"><span class="label">状态</span><span class="value">未选择</span></div>';
        clearBtn.disabled = true;
        releaseBtn.disabled = true;
        return;
      }
      detail.innerHTML =
        row("座位", seat.seat) +
        row("状态", seat.state_label || seat.state) +
        row("卡号", seat.card || "-") +
        row("人体感应", seat.human_label || "-") +
        row("离开计时", Number(seat.away_seconds || 0).toFixed(1) + " 秒");
      clearBtn.disabled = seat.state !== "OCCUPY";
      releaseBtn.disabled = seat.state === "EMPTY";
    }

    function row(label, value) {
      return '<div class="row"><span class="label">' + label + '</span><span class="value">' + value + '</span></div>';
    }

    async function refresh() {
      try {
        const data = await requestJson("/api/seats");
        seats = data.seats || [];
        renderEnv(data.env || {});
        if (data.config) qs("timeoutInput").value = data.config.away_timeout;
        if (selectedSeat && !seats.find((s) => s.seat === selectedSeat)) selectedSeat = null;
        renderSeats();
        renderDetail();
      } catch (err) {
        setStatus("刷新失败: " + err.message);
      }
    }

    async function postSeat(action) {
      if (!selectedSeat) return;
      try {
        const data = await requestJson("/api/seats/" + encodeURIComponent(selectedSeat) + "/" + action, { method: "POST" });
        setStatus(data.message || "操作完成");
        await refresh();
      } catch (err) {
        setStatus("操作失败: " + err.message);
      }
    }

    qs("clearBtn").onclick = () => postSeat("clear");
    qs("releaseBtn").onclick = () => postSeat("release");
    qs("saveTimeout").onclick = async () => {
      try {
        const value = Number(qs("timeoutInput").value);
        await requestJson("/api/config/timeout", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ seconds: value })
        });
        setStatus("离开超时已保存");
        await refresh();
      } catch (err) {
        setStatus("保存失败: " + err.message);
      }
    };

    refresh();
    setInterval(refresh, 1000);
  </script>
</body>
</html>
"""


class StudyGuardHandler(BaseHTTPRequestHandler):
    api = None

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        try:
            if path == "/":
                self._send_html(INDEX_HTML)
            elif path == "/studyguard.html":
                self._send_file(DESKTOP_HTML_PATH, "text/html; charset=utf-8")
            elif path == "/api/seats":
                self._send_json(200, self.api.list_seats())
            elif path.startswith("/api/seats/"):
                seat_id = unquote(path.split("/", 3)[3])
                self._send_json(200, self.api.get_seat(seat_id))
            elif path == "/api/env":
                self._send_json(200, self.api.get_env())
            elif path == "/api/config":
                self._send_json(200, {"ok": True, "config": self.api.get_config()})
            elif path == "/health":
                self._send_json(200, {"ok": True, "time": time.time()})
            else:
                self._send_json(404, {"ok": False, "error": "not found"})
        except ApiError as err:
            self._send_json(err.status, {"ok": False, "error": err.message})
        except Exception as err:
            self._send_json(500, {"ok": False, "error": str(err)})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        try:
            if path.startswith("/api/seats/") and path.endswith("/clear"):
                seat_id = unquote(path.split("/")[3])
                self._send_json(200, self.api.clear_occupy(seat_id))
            elif path.startswith("/api/seats/") and path.endswith("/release"):
                seat_id = unquote(path.split("/")[3])
                self._send_json(200, self.api.release_seat(seat_id))
            elif path == "/api/config/timeout":
                body = self._read_body()
                seconds = body.get("seconds", body.get("timeout", None))
                self._send_json(200, self.api.set_away_timeout(seconds))
            else:
                self._send_json(404, {"ok": False, "error": "not found"})
        except ApiError as err:
            self._send_json(err.status, {"ok": False, "error": err.message})
        except Exception as err:
            self._send_json(500, {"ok": False, "error": str(err)})

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_common_headers("application/json")
        self.end_headers()

    def log_message(self, fmt, *args):
        print("[HTTP] " + fmt % args)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b""
        ctype = self.headers.get("Content-Type", "")
        if "application/json" in ctype:
            return json.loads(raw.decode("utf-8") or "{}")
        form = parse_qs(raw.decode("utf-8"))
        return {k: v[-1] for k, v in form.items()}

    def _send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_common_headers("application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, html):
        data = html.encode("utf-8")
        self.send_response(200)
        self._send_common_headers("text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path, content_type):
        if not os.path.exists(path):
            self._send_json(404, {"ok": False, "error": "file not found"})
            return
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self._send_common_headers(content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_common_headers(self, content_type):
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def start_http_server(api, host, port):
    handler_cls = type("BoundStudyGuardHandler", (StudyGuardHandler,), {"api": api})
    server = ThreadingHTTPServer((host, port), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    server.thread = thread
    return server
