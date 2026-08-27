FROM ghcr.io/eclipse-sumo/sumo:latest

RUN apt-get update && apt-get install -y --no-install-recommends \
      xvfb x11vnc novnc websockify openbox \
      fonts-thai-tlwg fonts-noto-cjk x11-utils xdotool && \
    rm -rf /var/lib/apt/lists/*

# Open application windows maximized (dialogs keep their natural size)
RUN sed -i 's|</applications>|<application type="normal"><maximized>yes</maximized></application></applications>|' \
    /etc/xdg/openbox/rc.xml

COPY web/index.html /web/index.html
COPY scripts/gui-server.py /usr/local/bin/gui-server.py
COPY scripts/start-gui.sh /usr/local/bin/start-gui.sh
RUN chmod +x /usr/local/bin/start-gui.sh /usr/local/bin/gui-server.py

EXPOSE 6080 6081 6082
ENTRYPOINT ["/usr/local/bin/start-gui.sh"]
