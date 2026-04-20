"""
tver.py — Unified TVer.jp Downloader
Version: 2.1.0

Description:
    All-in-one downloader for TVer.jp with an interactive 4-option menu:
      1. Download a single video
      2. Download from links.txt (batch)
      3. Download a playlist
      4. Exit

    Features:
      - CStyle Console UI throughout
      - Per-stream progress bars (audio / video / merge)
      - Duplicate detection (skips already-downloaded files)
      - Thumbnail download → Downloads/thumbnails/<title>.jpg
      - Metadata (title + description) → Downloads/<title>.txt
      - Playlist title + "N of M" counter in the console

Dependencies:
    - yt-dlp  (pip install yt-dlp  or  winget install yt-dlp)

Notes:
    - TVer.jp is geo-restricted to Japan; set proxy_address if needed.

Author: kizer2m
License: MIT
"""

import subprocess
import sys
import os
import json
import re
import shutil
import socket
import queue
import threading
import time

VERSION      = "2.1.0"
OUTPUT_DIR   = "Downloads"
LINKS_FILE   = "links.txt"
ARCHIVE_FILE = "downloaded_archive.txt"
THUMB_DIR    = os.path.join(OUTPUT_DIR, "thumbnails")
ENV_FILE     = ".env"

# Directories that must exist before the script runs
_BASE_DIRS = [OUTPUT_DIR, THUMB_DIR]


# ─────────────────────────────────────────────────────────────────────────────
#  CStyle Console — Colors & UI helpers
# ─────────────────────────────────────────────────────────────────────────────

class C:
    """ANSI color shortcuts."""
    H  = '\033[95m'   # Magenta/hot
    B  = '\033[94m'   # Blue
    CN = '\033[96m'   # Cyan
    G  = '\033[92m'   # Green
    Y  = '\033[93m'   # Yellow
    R  = '\033[91m'   # Red
    BO = '\033[1m'    # Bold
    DM = '\033[2m'    # Dim
    IT = '\033[3m'    # Italic
    W  = '\033[97m'   # Bright White
    DG = '\033[90m'   # Dark Gray
    E  = '\033[0m'    # Reset


def _ui_separator(color: str = '\033[90m'):
    print(f"  {color}{'─' * 56}{C.E}")


def _ui_banner(title: str, width: int = 50, color: str = C.CN):
    # pad fills the interior space (width chars between the two ║)
    pad = width - len(title)
    l = max(pad // 2, 0)
    r = max(pad - l, 0)
    print()
    print(f"  {color}╔{'═' * width}╗{C.E}")
    print(f"  {color}║{' ' * l}{title}{' ' * r}║{C.E}")
    print(f"  {color}╚{'═' * width}╝{C.E}")
    print()


def _ui_header(title: str, color: str = C.CN):
    print()
    print(f"  {color}{C.BO}{title}{C.E}")
    print(f"  {color}{'─' * len(title)}{C.E}")
    print()


def _ui_status(icon: str, message: str, color: str = C.G):
    print(f"  {color}{icon}{C.E}  {message}")


def _ui_info_row(label: str, value: str):
    print(f"  {C.DG}│{C.E}  {C.DM}{label}{C.E}  {C.W}{value}{C.E}")


def _ui_prompt(label: str = '') -> str:
    prompt_text = f"  {C.CN}›{C.E}  {label}: " if label else f"  {C.CN}›{C.E}  "
    sys.stdout.write(prompt_text)
    sys.stdout.flush()
    return input('').strip()


def _ui_menu_item(num: str, label: str):
    print(f"  {C.DG}│{C.E}  {C.CN}{C.BO}{num}{C.E}  {C.W}{label}{C.E}")



def _ui_video_header(title: str, index: int, total: int):
    """Display a clean video header with index counter."""
    print()
    _ui_separator(C.DG)
    short_title = title if len(title) <= 48 else title[:45] + '…'
    print(f"  {C.CN}⟳{C.E}  {C.BO}{short_title}{C.E}")
    print(f"  {C.DG}│{C.E}  {C.DM}Video {C.E}{C.W}{C.BO}{index}{C.E}{C.DM} of {C.E}{C.W}{C.BO}{total}{C.E}")
    _ui_separator(C.DG)


# ─────────────────────────────────────────────────────────────────────────────
#  Progress tracking (stream-aware)
# ─────────────────────────────────────────────────────────────────────────────

_SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
_spin_idx = 0

# State shared between the two hooks
_dl_state: dict = {
    "phase": "video",   # "audio" | "video" | "merge"
    "audio_done": False,
    "video_done": False,
}


def _progress_bar_str(pct: float, width: int = 22) -> str:
    filled = int(width * pct / 100)
    empty  = width - filled
    return f"\033[96m{'━' * filled}\033[36m{'─' * empty}{C.E}"


def _phase_label(phase: str) -> str:
    labels = {
        "audio": f"{C.H}♪ Audio  {C.E}",
        "video": f"{C.B}▶ Video  {C.E}",
        "merge": f"{C.G}⊕ Merge  {C.E}",
    }
    return labels.get(phase, f"{C.DM}{phase}{C.E}")


def _build_progress_hook(phase: str):
    """Return a yt-dlp progress hook function tagged with a stream phase label."""
    global _spin_idx

    def hook(d: dict):
        global _spin_idx
        if d['status'] == 'downloading':
            pct_raw = d.get('_percent_str', '  0.0%').strip().replace('%', '')
            try:
                pct = float(pct_raw)
            except ValueError:
                pct = 0.0
            speed = d.get('_speed_str', '').strip()
            eta   = d.get('_eta_str', '').strip()
            bar   = _progress_bar_str(pct)
            spin  = _SPINNER[_spin_idx % len(_SPINNER)]
            _spin_idx += 1
            label = _phase_label(phase)
            line  = (f"\r  {C.CN}{spin}{C.E}  {label} {bar}"
                     f"  {C.BO}{pct:5.1f}%{C.E}"
                     f"  {C.DM}{speed}  {eta}{C.E}   ")
            sys.stdout.write(line)
            sys.stdout.flush()

        elif d['status'] == 'finished':
            bar = f"\033[92m{'━' * 22}{C.E}"
            label = _phase_label(phase)
            sys.stdout.write(
                f"\r  {C.G}✓{C.E}  {label} {bar}"
                f"  {C.BO}100.0%{C.E}  {C.G}Готово!{C.E}          \n"
            )
            sys.stdout.flush()

    return hook


# ─────────────────────────────────────────────────────────────────────────────
#  Startup — Environment check, .env loader, proxy validator
# ─────────────────────────────────────────────────────────────────────────────

def _load_env(path: str = ENV_FILE) -> dict:
    """
    Parse a simple KEY=VALUE .env file.
    Lines starting with # or empty lines are ignored.
    Returns a dict of {KEY: VALUE}.
    """
    result = {}
    if not os.path.exists(path):
        return result
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                result[key.strip()] = val.strip()
    return result


def _ensure_environment() -> None:
    """
    Silently create required directories and files if they don't exist.
    Only prints output when something is actually created.
    """
    created_any = False

    # ── Required directories ──────────────────────────────────────────
    for d in _BASE_DIRS:
        if not os.path.exists(d):
            os.makedirs(d)
            _ui_status('✓', f"Created directory  {C.DM}{d}/{C.E}")
            created_any = True

    # ── links.txt ────────────────────────────────────────────────────
    if not os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, "w", encoding="utf-8") as f:
            f.write("# Add TVer.jp video URLs here, one per line.\n")
        _ui_status('✓', f"Created file       {C.DM}{LINKS_FILE}{C.E}")
        created_any = True

    # ── .env ────────────────────────────────────────────────────────
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.write(
                "# TVer Downloader — proxy configuration\n"
                "# Supported formats:\n"
                "#   HTTP:   TVER_PROXY=http://user:pass@host:port\n"
                "#   SOCKS5: TVER_PROXY=socks5://user:pass@host:port\n"
                "# Leave empty to disable proxy:\n"
                "TVER_PROXY=\n"
            )
        _ui_status('⚠', f"{C.Y}.env created — add your TVER_PROXY to {C.W}{ENV_FILE}{C.Y}.{C.E}", C.Y)
        created_any = True

    if created_any:
        print()


def _parse_proxy_host_port(proxy: str) -> tuple[str, int] | None:
    """
    Extract (host, port) from a proxy URL of the form:
      scheme://[user:pass@]host:port
    Returns None if parsing fails.
    """
    try:
        # Strip scheme
        rest = proxy.split("://", 1)[-1]   # user:pass@host:port  or  host:port
        # Strip credentials if present
        if "@" in rest:
            rest = rest.rsplit("@", 1)[-1]  # host:port
        host, port_str = rest.rsplit(":", 1)
        return host.strip(), int(port_str.strip())
    except Exception:
        return None


def _check_proxy(proxy: str | None) -> bool | None:
    """
    Validate proxy by opening a raw TCP connection to proxy host:port.
    Works for HTTP, HTTPS, and SOCKS5 without external libraries.
    Returns:
        True  — proxy host:port is reachable
        False — connection refused / timed out
        None  — no proxy configured
    """
    if not proxy:
        return None

    _ui_status('⟳', f"Checking proxy  {C.DM}{proxy}{C.E}", C.CN)

    addr = _parse_proxy_host_port(proxy)
    if addr is None:
        _ui_status('⚠', f"{C.Y}Could not parse proxy address.{C.E}", C.Y)
        return False

    host, port = addr
    try:
        with socket.create_connection((host, port), timeout=8):
            pass
        return True
    except (OSError, socket.timeout):
        return False


def _startup_proxy_check(env: dict) -> str | None:
    """
    Load proxy from env dict, validate it, print CStyle result.
    Returns the proxy string to use (or None).
    """
    raw = env.get("TVER_PROXY", "").strip()
    proxy = raw if raw else None

    _ui_header("Proxy Status", C.DG)

    if proxy is None:
        _ui_status('⚠', f"{C.Y}No proxy configured in {C.W}{ENV_FILE}{C.Y}.{C.E}", C.Y)
        _ui_status('│', f"{C.DM}TVer.jp is geo-restricted to Japan.{C.E}", C.DG)
        _ui_status('│', f"{C.DM}Add TVER_PROXY=... to {ENV_FILE} or enable a Japanese VPN.{C.E}", C.DG)
        print()
        return None

    result = _check_proxy(proxy)

    if result is True:
        _ui_status('✓', f"{C.G}Proxy is {C.BO}ready{C.E}{C.G}.{C.E}  {C.DM}{proxy}{C.E}")
    else:
        _ui_status('✗', f"{C.R}Proxy is {C.BO}not responding{C.E}{C.R}.{C.E}  {C.DM}{proxy}{C.E}", C.R)
        _ui_status('│', f"{C.DM}Tip: Check proxy credentials/host, or switch to a Japanese VPN.{C.E}", C.DG)
    print()
    return proxy


# ─────────────────────────────────────────────────────────────────────────────
#  Folder / file helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def _sanitize_filename(name: str) -> str:
    """Remove characters that are illegal in Windows/Linux filenames."""
    return re.sub(r'[\\/:*?"<>|]', '_', name).strip()


def _read_links(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]


def _remove_link_from_file(path: str, url: str):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    new_lines = [ln for ln in lines if ln.strip() != url]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
        if new_lines:
            f.write("\n")


def _yt_dlp_available() -> bool:
    return shutil.which("yt-dlp") is not None


# ─────────────────────────────────────────────────────────────────────────────
#  Metadata / thumbnail helpers (yt-dlp JSON)
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_info(url: str, proxy: str | None, flat: bool = False) -> dict | None:
    """Run yt-dlp --dump-json and return parsed dict (or None on failure)."""
    cmd = ["yt-dlp", "--dump-json", "--no-warnings", "--quiet", "--no-playlist"]
    if flat:
        cmd.append("--flat-playlist")
    if proxy:
        cmd.extend(["--proxy", proxy])
    cmd.append(url)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=30,
        )
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        if not lines:
            return None
        return json.loads(lines[0])
    except Exception:
        return None


def _fetch_playlist_info(url: str, proxy: str | None) -> dict | None:
    """
    Retrieve flat playlist metadata: returns dict with keys
    'title', 'entries' (list of {id, title, url}).
    """
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-single-json",
        "--no-warnings",
        "--quiet",
    ]
    if proxy:
        cmd.extend(["--proxy", proxy])
    cmd.append(url)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=60,
        )
        if not result.stdout.strip():
            return None
        return json.loads(result.stdout)
    except Exception:
        return None


def _save_metadata(title: str, description: str, output_dir: str):
    """Save title+description to a .txt file named after the video."""
    safe = _sanitize_filename(title)
    path = os.path.join(output_dir, f"{safe}.txt")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Title: {title}\n\n")
            f.write(f"Description:\n{description or '(no description)'}\n")
        _ui_status('✓', f"Metadata  → {C.DM}{safe}.txt{C.E}")
    except Exception as e:
        _ui_status('⚠', f"Could not save metadata: {e}", C.Y)


def _download_thumbnail(url: str, title: str, proxy: str | None):
    """Download thumbnail image to Downloads/thumbnails/<title>.jpg"""
    _ensure_dir(THUMB_DIR)
    safe = _sanitize_filename(title)
    out_template = os.path.join(THUMB_DIR, f"{safe}.%(ext)s")
    cmd = [
        "yt-dlp",
        "--write-thumbnail",
        "--skip-download",
        "--no-warnings",
        "--quiet",
        "-o", out_template,
    ]
    if proxy:
        cmd.extend(["--proxy", proxy])
    cmd.append(url)
    try:
        subprocess.run(cmd, capture_output=True, check=False)
        # rename any webp → jpg for convenience
        for ext in ("webp", "jpg", "jpeg", "png"):
            candidate = os.path.join(THUMB_DIR, f"{safe}.{ext}")
            if os.path.exists(candidate):
                _ui_status('✓', f"Thumbnail → {C.DM}thumbnails/{safe}.{ext}{C.E}")
                return
        _ui_status('⚠', "Thumbnail not available (platform did not provide one).", C.Y)
    except Exception as e:
        _ui_status('⚠', f"Thumbnail download error: {e}", C.Y)


# ─────────────────────────────────────────────────────────────────────────────
#  Already-downloaded detection
# ─────────────────────────────────────────────────────────────────────────────

def _is_in_archive(video_id: str) -> bool:
    """Check if a video ID is already in downloaded_archive.txt."""
    if not os.path.exists(ARCHIVE_FILE):
        return False
    with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if video_id in line:
                return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
#  Core download (single video, with phase progress bars)
# ─────────────────────────────────────────────────────────────────────────────

def _download_video_subprocess(
    url: str,
    output_dir: str,
    proxy: str | None,
    use_archive: bool = True,
    extra_args: list | None = None,
) -> bool:
    """
    Call yt-dlp as a subprocess.
    Uses a reader thread + queue so the main thread can animate
    the merge phase even while ffmpeg produces no output.
    Returns True on success.
    """
    _ensure_dir(output_dir)

    cmd = ["yt-dlp"]
    if use_archive:
        cmd.extend(["--download-archive", ARCHIVE_FILE])
    cmd.extend([
        "-P", output_dir,
        "--merge-output-format", "mp4",
        "-o", "%(title)s [%(id)s].%(ext)s",
        "--embed-metadata",
        "--no-mtime",
        "--no-playlist",
        "--newline",
        "--progress",
    ])
    if proxy:
        cmd.extend(["--proxy", proxy])
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(url)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        # ── Reader thread: pushes stdout lines into a queue ────────────
        _DONE = object()           # sentinel — signals end of stream
        line_q: queue.Queue = queue.Queue()

        def _reader():
            for ln in proc.stdout:
                line_q.put(ln)
            line_q.put(_DONE)

        threading.Thread(target=_reader, daemon=True).start()

        # ── State ──────────────────────────────────────────────────────
        stream_index = 0           # increments on each "Destination:" line
        phase        = "video"     # current phase label
        spin         = 0
        merge_start: float | None = None

        while True:
            try:
                raw_line = line_q.get(timeout=0.09)   # ~11 fps animation
            except queue.Empty:
                # ── Animate merge while ffmpeg is silent ────────────────
                if merge_start is not None:
                    elapsed  = time.monotonic() - merge_start
                    fake_pct = min(97.0, elapsed / (elapsed + 28) * 100)
                    bar      = _progress_bar_str(fake_pct)
                    label    = _phase_label("merge")
                    sp       = _SPINNER[spin % len(_SPINNER)]
                    spin    += 1
                    e_str    = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"
                    sys.stdout.write(
                        f"\r  {C.CN}{sp}{C.E}  {label} {bar}"
                        f"  {C.BO}{fake_pct:5.1f}%{C.E}"
                        f"  {C.DM}elapsed {e_str}{C.E}   "
                    )
                    sys.stdout.flush()
                continue

            if raw_line is _DONE:
                break

            line = raw_line.rstrip()

            # ── Phase detection ────────────────────────────────────────
            # Stream counter: first Destination = video, second = audio
            if "[download]" in line and "destination:" in line.lower():
                stream_index += 1
                phase = "video" if stream_index == 1 else "audio"
                continue

            # Merge detection: suppress the raw line, start timing
            if "[Merger]" in line or "Merging formats" in line:
                if merge_start is None:
                    merge_start = time.monotonic()
                phase = "merge"
                continue

            # Skip noisy internal lines
            if any(s in line for s in (
                "Deleting original file",
                "already been recorded",
                "[ffmpeg]",
                "[ExtractAudio]",
            )):
                continue

            # ── Progress line ──────────────────────────────────────────
            pct_match = re.search(r'(\d+\.\d+)%', line)
            if pct_match and "[download]" in line:
                pct     = float(pct_match.group(1))
                speed_m = re.search(r'at\s+([\d.]+\s*\S+/s)', line)
                eta_m   = re.search(r'ETA\s+(\S+)', line)
                speed   = speed_m.group(1) if speed_m else ""
                eta     = eta_m.group(1)   if eta_m   else ""
                bar     = _progress_bar_str(pct)
                label   = _phase_label(phase)
                sp      = _SPINNER[spin % len(_SPINNER)]
                spin   += 1
                sys.stdout.write(
                    f"\r  {C.CN}{sp}{C.E}  {label} {bar}"
                    f"  {C.BO}{pct:5.1f}%{C.E}"
                    f"  {C.DM}{speed}  ETA {eta}{C.E}   "
                )
                sys.stdout.flush()
                continue

            # ── Stream 100 % ───────────────────────────────────────────
            if "[download] 100%" in line:
                bar   = f"\033[92m{'━' * 22}{C.E}"
                label = _phase_label(phase)
                sys.stdout.write(
                    f"\r  {C.G}✓{C.E}  {label} {bar}"
                    f"  {C.BO}100.0%{C.E}  {C.G}Done!{C.E}          \n"
                )
                sys.stdout.flush()
                continue

            # ── Already in archive ─────────────────────────────────────
            if "has already been recorded" in line or "already in archive" in line:
                _ui_status('│', f"{C.DM}Already downloaded — skipping.{C.E}", C.DG)

        # ── Merge finalise: overwrite animation line with Done ─────────
        if merge_start is not None:
            elapsed = time.monotonic() - merge_start
            e_str   = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"
            bar     = f"\033[92m{'━' * 22}{C.E}"
            label   = _phase_label("merge")
            sys.stdout.write(
                f"\r  {C.G}✓{C.E}  {label} {bar}"
                f"  {C.BO}100.0%{C.E}  {C.DM}elapsed {e_str}{C.E}  {C.G}Done!{C.E}          \n"
            )
            sys.stdout.flush()

        proc.wait()
        return proc.returncode == 0

    except FileNotFoundError:
        print()
        _ui_status('✗', 'yt-dlp not found. Install it and add it to PATH.', C.R)
        sys.exit(1)



# ─────────────────────────────────────────────────────────────────────────────
#  Option 1 — Download single video
# ─────────────────────────────────────────────────────────────────────────────

def menu_single(proxy: str | None):
    _ui_banner("SINGLE VIDEO", width=40, color=C.CN)
    url = _ui_prompt("TVer.jp video URL")
    if not url:
        _ui_status('⚠', 'No URL entered. Returning to menu.', C.Y)
        return

    print()
    _ui_status('⟳', 'Fetching video info…', C.CN)

    info = _fetch_info(url, proxy)
    title       = info.get("title", "video") if info else "video"
    description = info.get("description", "") if info else ""
    video_id    = info.get("id", "") if info else ""

    print()
    _ui_separator()
    _ui_info_row("Title ", title)
    _ui_info_row("URL   ", url[:60] + ("…" if len(url) > 60 else ""))
    if proxy:
        _ui_info_row("Proxy ", proxy)
    _ui_separator()
    print()

    # Check archive
    if video_id and _is_in_archive(video_id):
        _ui_status('│', f"{C.Y}Already downloaded (found in archive). Skipping.{C.E}", C.DG)
        print()
        return

    _ui_video_header(title, 1, 1)
    print()

    ok = _download_video_subprocess(url, OUTPUT_DIR, proxy, use_archive=True)

    print()
    _ui_separator()
    if ok:
        _ui_status('✦', f"{C.BO}Downloaded!{C.E}", C.G)
        if info:
            _save_metadata(title, description, OUTPUT_DIR)
            _download_thumbnail(url, title, proxy)
    else:
        _ui_status('✗', 'Download failed.', C.R)
        _ui_status('│', '1. Make sure a Japanese VPN/proxy is active.', C.DG)
        _ui_status('│', '2. The video may have been removed or is unavailable.', C.DG)
    _ui_separator()
    print()


# ─────────────────────────────────────────────────────────────────────────────
#  Option 2 — Download from links.txt
# ─────────────────────────────────────────────────────────────────────────────

def menu_batch(proxy: str | None):
    _ui_banner("BATCH DOWNLOAD", width=40, color=C.CN)

    if not os.path.exists(LINKS_FILE) or os.path.getsize(LINKS_FILE) == 0:
        _ui_status('✗', f"'{LINKS_FILE}' not found or empty.", C.R)
        _ui_status('│', 'Add URLs to the file, one per line.', C.DG)
        print()
        return

    links = _read_links(LINKS_FILE)
    if not links:
        _ui_status('⚠', f"No active URLs found in '{LINKS_FILE}'.", C.Y)
        print()
        return

    total = len(links)
    _ui_header('Session Info', C.CN)
    _ui_info_row('URLs to download', str(total))
    _ui_info_row('Archive file    ', ARCHIVE_FILE)
    _ui_info_row('Output folder   ', OUTPUT_DIR)
    if proxy:
        _ui_info_row('Proxy           ', proxy)
    print()

    _ensure_dir(OUTPUT_DIR)

    # ── Check which are already downloaded ────────────────────────────
    already_count = 0
    to_download   = []
    _ui_status('⟳', 'Checking archive…', C.CN)
    for url in links:
        info   = _fetch_info(url, proxy)        # no flat — works for episode URLs
        vid_id = info.get("id", "") if info else ""
        if vid_id and _is_in_archive(vid_id):
            already_count += 1
        else:
            to_download.append((url, info))

    if already_count:
        _ui_status('│', f"{C.Y}Already downloaded: {C.BO}{already_count}{C.E}"
                        f"{C.Y} of {C.BO}{total}{C.E}. Skipping them.", C.DG)
    new_count = len(to_download)
    _ui_status('⟳', f"To download: {C.W}{C.BO}{new_count}{C.E}", C.CN)
    print()

    success_count = 0
    fail_count    = 0

    for i, (url, info) in enumerate(to_download, start=1):
        title       = info.get("title", url) if info else url
        description = info.get("description", "") if info else ""

        _ui_video_header(title, i, new_count)
        print()

        ok = _download_video_subprocess(url, OUTPUT_DIR, proxy, use_archive=True)
        print()

        if ok:
            _ui_status('✓', 'Downloaded successfully.', C.G)
            _remove_link_from_file(LINKS_FILE, url)
            _save_metadata(title, description, OUTPUT_DIR)
            _download_thumbnail(url, title, proxy)
            success_count += 1
        else:
            _ui_status('✗', 'Download failed.', C.R)
            _ui_status('│', 'URL remains in links.txt for retry.', C.DG)
            fail_count += 1

    print()
    _ui_separator()
    if fail_count == 0:
        _ui_status('✦', f"{C.BO}All done!{C.E}  "
                        f"Succeeded: {C.G}{success_count}{C.E}  Failed: {C.DM}0{C.E}", C.G)
    else:
        _ui_status('✦', f"{C.BO}Finished.{C.E}  "
                        f"Succeeded: {C.G}{success_count}{C.E}  Failed: {C.R}{fail_count}{C.E}", C.Y)
        _ui_status('⚠', f"Failed URLs remain in '{LINKS_FILE}' for retry.", C.Y)
    _ui_separator()
    print()


# ─────────────────────────────────────────────────────────────────────────────
#  Option 3 — Download playlist
# ─────────────────────────────────────────────────────────────────────────────

def menu_playlist(proxy: str | None):
    _ui_banner("PLAYLIST", width=40, color=C.CN)
    url = _ui_prompt("TVer.jp playlist URL")
    if not url:
        _ui_status('⚠', 'No URL entered. Returning to menu.', C.Y)
        return

    print()
    _ui_status('⟳', 'Fetching playlist info…', C.CN)

    playlist = _fetch_playlist_info(url, proxy)
    if not playlist:
        _ui_status('✗', 'Could not retrieve playlist data. '
                        'Check the URL / proxy.', C.R)
        print()
        return

    playlist_title = playlist.get("title") or playlist.get("playlist_title") or "Playlist"
    entries = playlist.get("entries", [])
    total   = len(entries)

    if total == 0:
        _ui_status('⚠', 'Playlist is empty.', C.Y)
        print()
        return

    print()
    _ui_separator()
    _ui_info_row("Playlist ", playlist_title)
    _ui_info_row("Videos   ", str(total))
    if proxy:
        _ui_info_row("Proxy    ", proxy)
    _ui_separator()
    print()

    _ensure_dir(OUTPUT_DIR)
    _ensure_dir(THUMB_DIR)

    # ── Check archive ──────────────────────────────────────────────────
    already_count = 0
    to_download   = []
    _ui_status('⟳', 'Checking archive…', C.CN)
    for entry in entries:
        vid_id = entry.get("id", "")
        if vid_id and _is_in_archive(vid_id):
            already_count += 1
        else:
            to_download.append(entry)

    if already_count:
        _ui_status('│', f"{C.Y}Already downloaded: {C.BO}{already_count}{C.E}"
                        f"{C.Y} of {C.BO}{total}{C.E}. Skipping.", C.DG)
    new_count = len(to_download)
    _ui_status('⟳', f"To download: {C.W}{C.BO}{new_count}{C.E}", C.CN)
    print()

    if new_count == 0:
        _ui_status('✦', 'All playlist videos are already downloaded!', C.G)
        print()
        return

    success_count = 0
    fail_count    = 0

    for i, entry in enumerate(to_download, start=1):
        entry_id  = entry.get("id", "")
        entry_url = entry.get("url") or entry.get("webpage_url") or url
        if entry_id and "tver.jp" not in entry_url:
            # yt-dlp may only carry a relative ID — reconstruct URL
            entry_url = f"https://tver.jp/episodes/{entry_id}"

        # Fetch full info for this specific entry
        info        = _fetch_info(entry_url, proxy) or {}
        title       = info.get("title") or entry.get("title") or entry_id or f"video_{i}"
        description = info.get("description", "")

        print()
        _ui_separator(C.H)
        print(f"  {C.H}{C.BO}» Playlist: {playlist_title}{C.E}")
        _ui_separator(C.H)

        _ui_video_header(title, i, new_count)
        print()

        ok = _download_video_subprocess(entry_url, OUTPUT_DIR, proxy, use_archive=True)
        print()

        if ok:
            _ui_status('✓', 'Downloaded successfully.', C.G)
            _save_metadata(title, description, OUTPUT_DIR)
            _download_thumbnail(entry_url, title, proxy)
            success_count += 1
        else:
            _ui_status('✗', 'Download failed.', C.R)
            fail_count += 1

    print()
    _ui_separator()
    if fail_count == 0:
        _ui_status('✦', f"{C.BO}Playlist complete!{C.E}  "
                        f"Succeeded: {C.G}{success_count}{C.E}  Failed: {C.DM}0{C.E}", C.G)
    else:
        _ui_status('✦', f"{C.BO}Finished.{C.E}  "
                        f"Succeeded: {C.G}{success_count}{C.E}  Failed: {C.R}{fail_count}{C.E}", C.Y)
    _ui_separator()
    print()


# ─────────────────────────────────────────────────────────────────────────────
#  Main menu
# ─────────────────────────────────────────────────────────────────────────────

def _main_menu():
    while True:
        _ui_separator(C.DG)
        _ui_menu_item("1", "Download single video")
        _ui_menu_item("2", "Download from file  (links.txt)")
        _ui_menu_item("3", "Download playlist")
        _ui_menu_item("4", "Exit")
        _ui_separator(C.DG)
        print()

        choice = _ui_prompt("Select option (1-4)")

        if choice == "1":
            menu_single(PROXY)
        elif choice == "2":
            menu_batch(PROXY)
        elif choice == "3":
            menu_playlist(PROXY)
        elif choice == "4":
            print()
            _ui_status('✦', 'Goodbye!', C.G)
            print()
            sys.exit(0)
        else:
            print()
            _ui_status('⚠', f"Unknown option: '{choice}'. Enter 1–4.", C.Y)
            print()


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # Change working directory to script location so relative paths work
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # ── Startup banner ────────────────────────────────────────────────
    _ui_banner(f"TVER DOWNLOADER  v{VERSION}", width=44, color=C.CN)

    # ── Check yt-dlp ──────────────────────────────────────────────────
    if not _yt_dlp_available():
        _ui_status('✗', 'yt-dlp not found in PATH.', C.R)
        _ui_status('│', 'Install: pip install yt-dlp', C.DG)
        _ui_status('│', '    or:  winget install yt-dlp', C.DG)
        print()
        sys.exit(1)

    # ── Environment check (dirs, files) ───────────────────────────────
    _ensure_environment()

    # ── Load .env and validate proxy ──────────────────────────────────
    _env = _load_env(ENV_FILE)
    PROXY = _startup_proxy_check(_env)

    # ── Launch menu ───────────────────────────────────────────────────
    try:
        _main_menu()
    except KeyboardInterrupt:
        print()
        print()
        _ui_status('⚠', 'Interrupted by user (Ctrl+C).', C.Y)
        print()
        sys.exit(0)
