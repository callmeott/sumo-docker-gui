# Run SUMO on macOS — sumo-docker-gui

[Eclipse SUMO](https://eclipse.dev/sumo/) is a free traffic simulation package.
Its two graphical programs — **netedit** (the network editor) and **sumo-gui**
(the simulation viewer) — **no longer work on recent versions of macOS**: the
windows open but show only a grey screen, because macOS broke the graphics
layer (OpenGL in XQuartz) that they depend on
([details](https://github.com/XQuartz/XQuartz/issues/446)). This is not
something you can fix by reinstalling.

This project is the workaround: the two GUI programs run inside a Docker
container and appear **in your web browser**. The container ships a complete
SUMO installation, so this is all you need — installing SUMO on the Mac
itself is optional (see below).

![What you get: a launch page at http://localhost:6080](https://raw.githubusercontent.com/callmeott/sumo-docker-gui/main/docs/index-page.png)

---

## Setup (once)

Only two steps — the container brings its own complete SUMO installation,
so you do **not** need to install SUMO on the Mac first. Allow ~15 minutes.

### Step 1 — Install Docker Desktop

1. Download **Docker Desktop for Mac** (Apple silicon):
   <https://www.docker.com/products/docker-desktop/>
2. Open the downloaded `.dmg`, drag Docker into Applications, and launch it
   once. Wait until the whale icon in the menu bar stops animating.

Docker must be running whenever you use the GUI.

### Step 2 — Get this tool and start it

In Terminal:

```bash
git clone https://github.com/callmeott/sumo-docker-gui.git
cd sumo-docker-gui
cp env.sample .env
mkdir -p ~/Sumo
docker compose up -d --build
```

(No git? Use **Code → Download ZIP** on the GitHub page, unzip it, and `cd`
into the folder instead of the first two lines.)

The first start downloads and builds the container — a few minutes on a
normal connection. Later starts take seconds.

Then open: **<http://localhost:6080>** — you'll see the launch page with
buttons for netedit and sumo-gui. Bookmark it. **Setup done.**

---

## Everyday use

- **Start** (e.g. after a reboot): open Docker Desktop, then in Terminal:
  `cd sumo-docker-gui && docker compose up -d`
- **Open the GUI:** go to <http://localhost:6080>, click **Launch / Restart**
  on the program you want. It opens in a new tab.
- **Stop:** `docker compose stop` (or just quit Docker Desktop).

### Where do my files go?

Your SUMO files live in the **`~/Sumo`** folder on your Mac (created in
step 2; change it by editing `SUMO_DATA` in the `.env` file). Inside
netedit / sumo-gui, that same folder is called **`/data`**:

| On your Mac | Inside the GUI |
| --- | --- |
| `~/Sumo/mynet.net.xml` | `/data/mynet.net.xml` |
| `~/Sumo/bangkok/run.sumocfg` | `/data/bangkok/run.sumocfg` |

Anything you save under `/data` appears in `~/Sumo` — and nothing outside it
is visible to the container.

### The editable command line

Each launch card has a command-line box. Leave it empty to start the program
plain, or add arguments before clicking **Launch / Restart**, e.g.:

- netedit: `-s /data/mynet.net.xml` (open a network)
- sumo-gui: `-c /data/run.sumocfg` (open a simulation configuration)

All options are in the [sumo-gui](https://sumo.dlr.de/docs/sumo-gui.html) and
[netedit](https://sumo.dlr.de/docs/netedit.html) documentation. **Open
window** shows the running program without restarting it.

### Command-line tools (netconvert, duarouter, …)

The rest of SUMO is command-line only. Two ways to use it:

- **Inside the container (nothing extra to install):**

  ```bash
  docker compose exec sumo-gui bash
  # you now have sumo, netconvert, duarouter, ... with your files in /data
  ```

- **Natively on the Mac (optional):** install SUMO from
  <https://sumo.dlr.de/docs/Downloads.php> (under **macOS**, the
  `sumo-<version>.pkg` installer; if macOS refuses to open it, right-click →
  **Open**), then tell your Terminal where it is by pasting this block:

  ```bash
  cat >> ~/.zshrc <<'EOF'
  export SUMO_HOME="/Library/Frameworks/EclipseSUMO.framework/Versions/Current/EclipseSUMO/share/sumo"
  export PATH="$SUMO_HOME/bin:$PATH"
  EOF
  ```

  (If your Terminal uses bash instead of zsh, use `~/.bash_profile` in place
  of `~/.zshrc`.) Open a new Terminal window and check with `sumo --version`.
  The GUI programs still won't open natively — that's what this project is
  for — but all command-line tools will work.

---

## Configuration

All settings live in `.env` (copy of `env.sample`):

| Setting | Default | Meaning |
| --- | --- | --- |
| `SUMO_DATA` | `~/Sumo` | Mac folder that appears as `/data` in the GUI |
| `SCREEN` | `1920x1080` | Virtual screen size (bigger = sharper) |
| `UI_FONT` | `Noto Sans CJK SC` | Application UI font |

After changing `.env`, run `docker compose up -d` again.

Ports `6080` (launcher), `6081` (netedit), `6082` (sumo-gui) are bound to
`127.0.0.1` on purpose — the sessions are unauthenticated, so they are only
reachable from your own Mac. Don't re-bind them to a public interface.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `Cannot connect to the Docker daemon` | Start Docker Desktop and wait for the whale icon to settle |
| `port is already allocated` | Another app uses 6080/6081/6082 — change the left-hand port numbers in `docker-compose.yml` |
| Browser can't reach `localhost:6080` | `docker compose ps` — if nothing is running, `docker compose up -d` |
| A GUI tab shows black | The program is restarting; wait a few seconds and reload the tab |
| Mounted folder is empty in `/data` | Check `SUMO_DATA` in `.env` points to the right folder, then `docker compose up -d` |

## Notes & limitations

- netedit and sumo-gui are the only windowed SUMO programs; all other tools
  (netconvert, duarouter, the Python tools, …) are command-line — see
  "Command-line tools" above for running them in the container or natively.
- Quitting a program in the GUI just respawns it — use the launch page to
  restart it with different arguments.
- The upstream SUMO image is linux/amd64; on Apple silicon it runs under
  Rosetta emulation. Fine for editing; huge networks may feel sluggish.
- Keyboard: direct layouts (Thai, European, …) work, but SUMO's GUI toolkit
  (FOX 1.6) discards non-Latin characters in text fields — a toolkit
  limitation that exists on native Linux too. IME-composed input
  (Chinese/Japanese/Korean) doesn't work over VNC.

## Credits

[Eclipse SUMO](https://eclipse.dev/sumo/) is developed by the German
Aerospace Center (DLR) and community — see the
[documentation](https://sumo.dlr.de/docs/). This project is an unaffiliated
convenience wrapper around the official
[SUMO Docker image](https://github.com/eclipse-sumo/sumo/pkgs/container/sumo).
