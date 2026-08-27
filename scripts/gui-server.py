#!/usr/bin/env python3
"""Serves the index page (/web) plus a tiny launcher API:

  GET  /args    -> current command-line args per app (JSON)
  POST /launch  -> save args, restart the app, redirect to its noVNC page

The respawn loop in start-gui.sh re-reads the args file on every restart.
"""
import http.server
import json
import subprocess
import urllib.parse

APPS = {
    "netedit":  {"args_file": "/tmp/netedit.args",  "port": 6081},
    "sumo-gui": {"args_file": "/tmp/sumo-gui.args", "port": 6082},
}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/web", **kwargs)

    def do_GET(self):
        if self.path.rstrip("/") == "/args":
            data = {}
            for app, cfg in APPS.items():
                try:
                    data[app] = open(cfg["args_file"]).read().strip()
                except OSError:
                    data[app] = ""
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.rstrip("/") != "/launch":
            self.send_error(404)
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
        hostname = self.headers.get("Host", "localhost").split(":")[0]
        self.send_response(303)
        self.send_header("Location",
                         "http://%s:%d/vnc.html?autoconnect=true&resize=scale"
                         % (hostname, cfg["port"]))
        self.end_headers()


http.server.ThreadingHTTPServer(("0.0.0.0", 6080), Handler).serve_forever()
