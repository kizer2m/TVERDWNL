"""
tver_downloader.py — Single-video downloader for TVer.jp
Version: 1.1.0

Description:
    Downloads a single video from TVer.jp for a given URL using yt-dlp.
    The video is saved to the Downloads folder (created automatically if missing).

Usage:
    python tver_downloader.py
    -> Enter the video URL when prompted.

Dependencies:
    - yt-dlp  (install: pip install yt-dlp  or  winget install yt-dlp)

Notes:
    - TVer.jp is geo-restricted to Japan. Set proxy_address to use a Japanese proxy/VPN.
    - Both HTTP/HTTPS and SOCKS5 proxies are supported.

Author: kizer2m
License: MIT
"""

import subprocess
import sys
import os

VERSION = "1.1.0"

# ─────────────────────────────────────────────────────
#  CStyle Console — Colors & UI helpers
# ─────────────────────────────────────────────────────

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
    """Thin horizontal separator line."""
    print(f"  {color}{'─' * 56}{C.E}")


def _ui_banner(title: str, width: int = 50, color: str = C.CN):
    """Double-line boxed banner for major sections."""
    pad = width - len(title) - 2
    l = pad // 2
    r = pad - l
    print()
    print(f"  {color}╔{'═' * width}╗{C.E}")
    print(f"  {color}║{' ' * l}{title}{' ' * r}║{C.E}")
    print(f"  {color}╚{'═' * width}╝{C.E}")
    print()


def _ui_header(title: str, color: str = C.CN):
    """Section header with decorative line."""
    print()
    print(f"  {color}{C.BO}{title}{C.E}")
    print(f"  {color}{'─' * len(title)}{C.E}")
    print()


def _ui_status(icon: str, message: str, color: str = C.G):
    """Single status line with colored icon."""
    print(f"  {color}{icon}{C.E}  {message}")


def _ui_prompt(label: str = '') -> str:
    """Consistent input prompt. Returns stripped string."""
    prompt_text = f"  {C.CN}›{C.E}  {label}: " if label else f"  {C.CN}›{C.E}  "
    sys.stdout.write(prompt_text)
    sys.stdout.flush()
    return input('').strip()


def _ui_info_row(label: str, value: str):
    """Dimmed key/value info row."""
    print(f"  {C.DG}│{C.E}  {C.DM}{label}{C.E}  {C.W}{value}{C.E}")


# ─────────────────────────────────────────────────────
#  Progress hook for yt-dlp
# ─────────────────────────────────────────────────────

_SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
_spin_idx = 0


def _progress_bar_str(pct: float, width: int = 20) -> str:
    """Build ━─ style gradient progress bar string."""
    filled = int(width * pct / 100)
    empty  = width - filled
    bar = f"\033[96m{'━' * filled}\033[36m{'─' * empty}{C.E}"
    return bar


def _progress_hook(d: dict):
    """yt-dlp progress hook with CStyle progress bar."""
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
        line  = (f"\r  {C.CN}{spin}{C.E}  {bar}"
                 f"  {C.BO}{pct:5.1f}%{C.E}"
                 f"  {C.DM}{speed}  {eta}{C.E}   ")
        sys.stdout.write(line)
        sys.stdout.flush()
    elif d['status'] == 'finished':
        bar = f"\033[92m{'━' * 20}{C.E}"
        sys.stdout.write(
            f"\r  {C.G}✓{C.E}  {bar}  {C.BO}100.0%{C.E}"
            f"  {C.G}Done!{C.E}          \n"
        )
        sys.stdout.flush()


# ─────────────────────────────────────────────────────
#  Core downloader
# ─────────────────────────────────────────────────────

def download_tver_video(url: str, output_dir: str = "Downloads", proxy: str | None = None) -> None:
    """
    Download a single TVer.jp video using yt-dlp.

    :param url:        Video URL on TVer.jp (e.g. https://tver.jp/episodes/...)
    :param output_dir: Destination folder for the downloaded file.
    :param proxy:      Optional proxy string (e.g. 'http://127.0.0.1:8080').
                       Required to bypass TVer geo-restrictions outside Japan.
    """
    # Show what we're about to download
    _ui_separator()
    _ui_info_row("URL   ", url)
    _ui_info_row("Folder", output_dir)
    if proxy:
        _ui_info_row("Proxy ", proxy)
    _ui_separator()
    print()

    # Create the output folder if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        _ui_status('✓', f"Created download folder: {C.DM}{output_dir}{C.E}")

    # Build yt-dlp command
    command = [
        "yt-dlp",
        "-P", output_dir,
        "--merge-output-format", "mp4",
        "--embed-metadata",
        "--no-mtime",
        url,
    ]

    if proxy:
        command.extend(["--proxy", proxy])

    _ui_status('⟳', 'Starting download…', C.CN)
    print()

    try:
        subprocess.run(command, check=True, capture_output=False, text=False)

        print()
        _ui_separator()
        _ui_status('✦', f"{C.BO}Download complete.{C.E}", C.G)
        _ui_separator()
        print()

    except subprocess.CalledProcessError as e:
        print()
        _ui_separator()
        _ui_status('✗', f"yt-dlp exited with error code: {C.BO}{e.returncode}{C.E}", C.R)
        print()
        _ui_status('│', 'Possible reasons:', C.DG)
        _ui_status('│', '1. Geo-restriction — make sure a Japanese VPN/proxy is active.', C.DG)
        _ui_status('│', '2. The video has been removed or is unavailable.', C.DG)
        _ui_separator()
        print()

    except FileNotFoundError:
        print()
        _ui_status('✗', 'yt-dlp not found. Make sure it is installed and available in PATH.', C.R)
        print()
        sys.exit(1)


# ─────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────

if __name__ == "__main__":
    _ui_banner(f'TVER DOWNLOADER  v{VERSION}', width=40, color=C.CN)

    tver_url = _ui_prompt('Enter TVer video URL (e.g. https://tver.jp/episodes/…)')

    # 🚨 PROXY SETUP 🚨
    # If you need to use a proxy (Japanese IP), replace None with the address string:
    # HTTP example:   proxy_address = 'http://127.0.0.1:8080'
    # SOCKS5 example: proxy_address = 'socks5://user:pass@host:port'
    proxy_address = None

    if not tver_url:
        print()
        _ui_status('⚠', 'No URL entered. Exiting.', C.Y)
        print()
    else:
        download_tver_video(tver_url, proxy=proxy_address)
