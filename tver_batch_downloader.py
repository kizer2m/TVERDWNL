"""
tver_batch_downloader.py — Batch downloader for TVer.jp
Version: 1.1.0

Description:
    Reads a list of URLs from links.txt and downloads each video one by one
    using yt-dlp.
    After a successful download (video + audio merged), the corresponding URL
    is automatically removed from links.txt.
    Videos already downloaded are skipped (tracked via downloaded_archive.txt).
    All files are saved to the Downloads folder (created automatically if missing).

Usage:
    1. Add video URLs to links.txt — one URL per line.
    2. Run: python tver_batch_downloader.py

Dependencies:
    - yt-dlp  (install: pip install yt-dlp  or  winget install yt-dlp)

Files:
    links.txt              — list of URLs to download (one per line)
    downloaded_archive.txt — archive of already-downloaded video IDs (auto-created)
    Downloads/             — destination folder for downloaded files (auto-created)

Notes:
    - TVer.jp is geo-restricted to Japan. Set proxy_address to use a Japanese proxy/VPN.
    - Both HTTP/HTTPS and SOCKS5 proxies are supported.
    - Comment lines (#) and blank lines in links.txt are ignored.

Author: kizer2m
License: MIT
"""

import subprocess
import sys
import os

VERSION = "1.1.0"

# Path to the file that holds the list of URLs to download
LINKS_FILE = "links.txt"
# yt-dlp archive file — stores IDs of already-downloaded videos to avoid re-downloading
ARCHIVE_FILE = "downloaded_archive.txt"


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


def _ui_info_row(label: str, value: str):
    """Dimmed key/value info row."""
    print(f"  {C.DG}│{C.E}  {C.DM}{label}{C.E}  {C.W}{value}{C.E}")


def _ui_block_header(index: int, total: int, url: str):
    """Download block header with index and (truncated) URL."""
    short_url = url if len(url) <= 52 else url[:49] + '…'
    print()
    _ui_separator()
    _ui_status('│', f"{C.DM}[{index}/{total}]{C.E}  {C.W}{short_url}{C.E}", C.DG)
    _ui_separator()


# ─────────────────────────────────────────────────────
#  File helpers
# ─────────────────────────────────────────────────────

def _read_links(path: str) -> list[str]:
    """Return a list of non-empty URLs from the file, skipping comment lines (#)."""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]


def _remove_link_from_file(path: str, url: str) -> None:
    """Remove a specific URL from links.txt after it has been downloaded successfully."""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    # Keep every line except the one that matches the given URL (stripped comparison)
    new_lines = [ln for ln in lines if ln.strip() != url]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
        if new_lines:       # add a trailing newline if the file is not empty
            f.write("\n")


# ─────────────────────────────────────────────────────
#  Core downloader
# ─────────────────────────────────────────────────────

def download_single(url: str, output_dir: str, proxy: str | None) -> bool:
    """
    Download a single video from the given URL.

    :param url:        Video URL on TVer.jp
    :param output_dir: Destination folder for the downloaded file
    :param proxy:      Proxy address string or None
    :returns:          True if the download succeeded, False otherwise
    """
    command = [
        "yt-dlp",
        "--download-archive", ARCHIVE_FILE,
        "-P", output_dir,
        "--merge-output-format", "mp4",
        "-o", "%(title)s [%(id)s].%(ext)s",   # filename template
        "--embed-metadata",
        "--no-mtime",
        url,
    ]

    if proxy:
        command.extend(["--proxy", proxy])

    try:
        subprocess.run(command, check=True, capture_output=False, text=False)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        print()
        _ui_status('✗', 'yt-dlp not found. Install it or add it to PATH.', C.R)
        sys.exit(1)


def download_tver_videos_from_file(output_dir: str = "Downloads", proxy: str | None = None) -> None:
    """
    Batch-download TVer videos listed in links.txt.

    For each URL:
      - runs yt-dlp;
      - on success  → removes the URL from links.txt;
      - on failure  → leaves the URL in links.txt for a later retry.

    :param output_dir: Destination folder for downloaded videos (default: Downloads)
    :param proxy:      Proxy address string or None
    """
    _ui_banner(f'TVER BATCH  v{VERSION}', width=40, color=C.CN)

    # ── Validate links.txt ───────────────────────────
    if not os.path.exists(LINKS_FILE) or os.path.getsize(LINKS_FILE) == 0:
        _ui_status('✗', f"'{LINKS_FILE}' not found or empty.", C.R)
        _ui_status('│', 'Create the file and add URLs, one per line.', C.DG)
        print()
        return

    links = _read_links(LINKS_FILE)
    if not links:
        _ui_status('⚠', f"No active URLs found in '{LINKS_FILE}'.", C.Y)
        print()
        return

    # ── Session info ─────────────────────────────────
    _ui_header('Session Info', C.CN)
    _ui_info_row('URLs to download', str(len(links)))
    _ui_info_row('Archive file    ', ARCHIVE_FILE)
    _ui_info_row('Output folder   ', output_dir)
    if proxy:
        _ui_info_row('Proxy           ', proxy)
    print()

    # ── Create output folder ─────────────────────────
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        _ui_status('✓', f"Created download folder: {C.DM}{output_dir}{C.E}")

    # ── Download loop ────────────────────────────────
    success_count = 0
    fail_count    = 0

    for i, url in enumerate(links, start=1):
        _ui_block_header(i, len(links), url)
        print()

        ok = download_single(url, output_dir, proxy)
        print()

        if ok:
            _ui_status('✓', f"Downloaded successfully.", C.G)
            _remove_link_from_file(LINKS_FILE, url)
            success_count += 1
        else:
            _ui_status('✗', f"Download failed.", C.R)
            _ui_status('│', 'URL remains in links.txt for retry.', C.DG)
            fail_count += 1

    # ── Final summary ────────────────────────────────
    print()
    _ui_separator()
    if fail_count == 0:
        _ui_status('✦', f"{C.BO}All done!{C.E}  Succeeded: {C.G}{success_count}{C.E}  Failed: {C.DM}0{C.E}", C.G)
    else:
        _ui_status('✦', f"{C.BO}Finished.{C.E}  Succeeded: {C.G}{success_count}{C.E}  Failed: {C.R}{fail_count}{C.E}", C.Y)
        _ui_status('⚠', f"Failed URLs are still in '{LINKS_FILE}' for retry.", C.Y)
    _ui_separator()
    print()


# ─────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────

if __name__ == "__main__":

    # 🚨 PROXY SETUP 🚨
    # If you need a Japanese IP to bypass TVer geo-restriction, replace None with the address:
    # HTTP example:   proxy_address = 'http://127.0.0.1:8080'
    # SOCKS5 example: proxy_address = 'socks5://user:pass@host:port'
    proxy_address = None

    download_tver_videos_from_file(proxy=proxy_address)
