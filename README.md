# sumo-docker-gui

Run the [Eclipse SUMO](https://eclipse.dev/sumo/) GUI applications — **netedit**
and **sumo-gui** — on macOS, in your browser. No XQuartz needed.

## Why

Recent macOS versions (Tahoe / 26.x) broke the OpenGL (GLX) path that XQuartz
relies on, so SUMO's native GUI applications open with a dark grey,
non-rendering canvas ([XQuartz#446](https://github.com/XQuartz/XQuartz/issues/446),
[XQuartz#452](https://github.com/XQuartz/XQuartz/issues/452)) — and the XQuartz
maintainers consider it a macOS bug they can't fix.

This project sidesteps X11 on the Mac entirely: the SUMO GUIs run inside a
Docker container on virtual displays (Xvfb) and are viewed in the browser via
noVNC. Rendering, non-US keyboards, and CJK menu labels all work.

## Quick start

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/)
(or any Docker with compose v2.17+).

```bash
git clone https://github.com/callmeott/sumo-docker-gui.git
cd sumo-docker-gui
docker compose up -d --build
open http://localhost:6080
```

The index page lets you launch **netedit** and **sumo-gui**, each with an
**editable command line** — set arguments like `-s /data/mynet.net.xml` or
`-c /data/run.sumocfg` and hit *Launch / Restart*. *Open window* views the
running instance without restarting it.

## Your data

The folder in `SUMO_DATA` (default: this repo folder) is mounted at `/data`
inside the container. Point it at your scenario folder:

```bash
SUMO_DATA=~/my-sumo-scenarios docker compose up -d
```

Files opened/saved under `/data` in the GUI persist in that folder.

## Configuration

| Env var | Default | Meaning |
| --- | --- | --- |
| `SUMO_DATA` | `.` | Host folder mounted at `/data` |
| `SCREEN` | `1920x1080` | Virtual display resolution (set in the service `environment:`) |
| `UI_FONT` | `Noto Sans CJK SC` | UI font (FOX uses a single font for all UI text) |

Ports: `6080` index/launcher, `6081` netedit, `6082` sumo-gui — all bound to
`127.0.0.1` on purpose, because the VNC sessions and the command launcher are
unauthenticated. Don't re-bind them to a public interface.

## Notes & limitations

- Only netedit and sumo-gui are windowed programs; all other SUMO tools are
  command-line. Run them with `docker compose exec sumo-gui bash` (or install
  SUMO natively — the CLI tools work fine on macOS, it's only the GUI that
  needs this workaround).
- Quitting an app in the GUI just respawns it — use the index page to restart
  with different arguments.
- The upstream SUMO image is linux/amd64; on Apple Silicon it runs under
  Rosetta emulation. Fine for editing; very large networks may feel sluggish.
- Keyboard: direct layouts (Thai, European, …) reach the applications
  (`x11vnc -add_keysyms`), but SUMO's GUI toolkit (FOX 1.6) discards non-Latin
  characters in text fields — a toolkit limitation that exists on native Linux
  too. IME-composed input (Chinese/Japanese/Korean) doesn't work over VNC.
- The Language menu and other CJK labels render correctly (Noto Sans CJK is
  forced as the UI font; FOX does no per-glyph font fallback).

## Credits

[Eclipse SUMO](https://eclipse.dev/sumo/) is developed by the German Aerospace
Center (DLR) and community — see the [documentation](https://sumo.dlr.de/docs/).
This project is an unaffiliated convenience wrapper around the official
[SUMO Docker image](https://github.com/eclipse-sumo/sumo/pkgs/container/sumo).
