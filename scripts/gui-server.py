#!/usr/bin/env python3
"""Serves the index page (/web) plus a tiny launcher API:

  GET  /state   -> per-app command-line args and tokened viewer URLs (JSON)
  POST /launch  -> save args, restart the app, return its viewer URL (JSON)

Security (this listens on localhost, but localhost is not a trust boundary
in a browser — any website can send requests to it):
  * Host-header allowlist on every request  -> blocks DNS-rebinding
  * /launch requires the X-Requested-With header -> blocks cross-site form
    POSTs; cross-origin fetch with a custom header needs a CORS preflight,
    which this server never approves
  * /launch validates the Origin header when present -> browsers always send
    it on POST, and pages cannot forge it, so a browser request must come
    from our own page (absent Origin = non-browser client, e.g. local curl)
  * viewer URLs carry per-start random tokens (enforced by websockify);
    they are only readable same-origin, so other websites can't obtain them
"""
import http.server
import json
import os
import subprocess
import urllib.parse

APPS = {
    "netedit": {
        "args_file": "/tmp/netedit.args",
        "port": 6081,
        "token": os.environ.get("NETEDIT_TOKEN", ""),
    },
    "sumo-gui": {
        "args_file": "/tmp/sumo-gui.args",
        "port": 6082,
        "token": os.environ.get("SUMO_GUI_TOKEN", ""),
    },
}

ALLOWED_HOSTS = {"localhost", "127.0.0.1", "[::1]", "::1"}
LAUNCH_HEADER = "sumo-docker-gui"


def viewer_url(cfg, hostname):
    path = urllib.parse.quote("websockify?token=" + cfg["token"], safe="")
    return ("http://%s:%d/vnc.html?autoconnect=true&resize=scale&path=%s"
            % (hostname, cfg["port"], path))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/web", **kwargs)

    def hostname(self):
        return self.headers.get("Host", "").rsplit(":", 1)[0].strip()

    def host_allowed(self):
        if self.hostname() in ALLOWED_HOSTS:
            return True
        self.send_error(403, "forbidden host")
        return False

    def origin_allowed(self):
        origin = self.headers.get("Origin")
        if origin is None:
            return True  # non-browser client (e.g. curl on this machine)
        if urllib.parse.urlsplit(origin).hostname in {"localhost",
                                                      "127.0.0.1", "::1"}:
            return True
        self.send_error(403, "forbidden origin")
        return False

    def send_json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.host_allowed():
            return
        if self.path.rstrip("/") == "/state":
            state = {}
            for app, cfg in APPS.items():
                try:
                    args = open(cfg["args_file"]).read().strip()
                except OSError:
                    args = ""
                state[app] = {"args": args,
                              "url": viewer_url(cfg, self.hostname())}
            self.send_json(state)
        else:
            super().do_GET()

    def do_POST(self):
        if not self.host_allowed() or not self.origin_allowed():
            return
        if self.path.rstrip("/") != "/launch":
            self.send_error(404)
            return
        if self.headers.get("X-Requested-With") != LAUNCH_HEADER:
            self.send_error(403, "missing X-Requested-With header")
            return
        length = int(self.headers.get("Content-Length", 0))
        form = urllib.parse.parse_qs(self.rfile.read(length).decode())
        app = form.get("app", [""])[0]
        args = form.get("args", [""])[0].strip()
        if app not in APPS:
            self.send_error(400, "unknown app")
            return
        cfg = APPS[app]
        with open(cfg["args_file"], "w") as f:
            f.write(args)
        subprocess.run(["pkill", "-x", app])  # respawn loop restarts it
        self.send_json({"url": viewer_url(cfg, self.hostname())})


http.server.ThreadingHTTPServer(("0.0.0.0", 6080), Handler).serve_forever()
