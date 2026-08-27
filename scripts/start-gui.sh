#!/bin/bash
# Starts the SUMO GUI stack inside the container:
#   netedit  on display :1  -> noVNC on port 6081
#   sumo-gui on display :2  -> noVNC on port 6082
#   index page + launcher API on port 6080 (gui-server.py)
# SCREEN and UI_FONT are overridable via the environment (see env.sample).
#
# Security model (see README): every VNC session is protected by a random
# per-start token enforced by websockify — browsers allow any website to open
# WebSockets to localhost, so without the token a malicious page could take
# over the GUI. The tokens are embedded in the links served by gui-server.py,
# which only same-origin pages can read.
set -e

SCREEN="${SCREEN:-1920x1080}"
WIDTH="${SCREEN%x*}"
HEIGHT="${SCREEN#*x}"

# FOX apps render all UI text with a single Xft font (no per-glyph fallback);
# force one with broad coverage so CJK labels (e.g. the Language menu) render.
UI_FONT="${UI_FONT:-Noto Sans CJK SC}"
cat > /etc/fonts/local.conf <<FONTCONF
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <match target="pattern">
    <edit name="family" mode="prepend" binding="strong"><string>${UI_FONT}</string></edit>
  </match>
</fontconfig>
FONTCONF

run_app() {
  local app="$1" display="$2" vncport="$3" wsport="$4" token="$5"
  Xvfb "$display" -screen 0 "${WIDTH}x${HEIGHT}x24" &
  sleep 1
  DISPLAY="$display" openbox &
  # -localhost: VNC reachable only via websockify in this container
  # -add_keysyms lets non-US layouts (e.g. Thai) type over VNC
  x11vnc -display "$display" -rfbport "$vncport" -localhost \
         -nopw -forever -shared -quiet -xkb -add_keysyms &
  # session token gates the WebSocket endpoint
  umask 077
  echo "$token: localhost:$vncport" > "/tmp/$app.token"
  websockify --web=/usr/share/novnc \
             --token-plugin TokenFile --token-source "/tmp/$app.token" \
             "$wsport" &
  # respawn on exit, re-reading the (web-editable) args file each time
  # ("|| true" keeps the loop alive under set -e when the app is killed)
  ( while true; do
      DISPLAY="$display" "$app" $(cat "/tmp/$app.args" 2>/dev/null) || true
      sleep 2
    done ) &
}

new_token() { python3 -c "import secrets; print(secrets.token_urlsafe(24))"; }
export NETEDIT_TOKEN="$(new_token)"
export SUMO_GUI_TOKEN="$(new_token)"

cd /data
run_app netedit  :1 5901 6081 "$NETEDIT_TOKEN"
run_app sumo-gui :2 5902 6082 "$SUMO_GUI_TOKEN"

exec python3 /usr/local/bin/gui-server.py
