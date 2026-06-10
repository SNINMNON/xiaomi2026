"""
E5 touchscreen launcher.

The UI itself is served by http_server.py. On U2P/E5 this helper opens the
local management page in a browser, optionally in kiosk mode when Chromium is
available.
"""

import os
import shutil
import subprocess
import sys


def local_url(port):
    return "http://127.0.0.1:%d/" % int(port)


def launch_touch_ui(port, browser=None, kiosk=False):
    url = local_url(port)
    cmd = _browser_command(url, browser, kiosk)
    if cmd is None:
        return False, url, "no browser launcher found"

    try:
        if sys.platform.startswith("win") and cmd == ["startfile", url]:
            os.startfile(url)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=_display_env())
        return True, url, "opened"
    except Exception as err:
        return False, url, str(err)


def _browser_command(url, browser, kiosk):
    if browser:
        return [browser, url]

    chromium = (
        shutil.which("chromium-browser")
        or shutil.which("chromium")
        or shutil.which("google-chrome")
        or shutil.which("chrome")
    )
    if chromium:
        if kiosk:
            return [chromium, "--kiosk", "--noerrdialogs", "--disable-infobars", url]
        return [chromium, url]

    if sys.platform.startswith("linux"):
        opener = shutil.which("xdg-open")
        if opener:
            return [opener, url]
    if sys.platform == "darwin":
        return ["open", url]
    if sys.platform.startswith("win"):
        return ["startfile", url]
    return None


def _display_env():
    env = os.environ.copy()
    if sys.platform.startswith("linux"):
        env.setdefault("DISPLAY", ":0")
        xauth = os.path.expanduser("~/.Xauthority")
        if os.path.exists(xauth):
            env.setdefault("XAUTHORITY", xauth)
    return env
