"""
tver_batch_downloader.py — Batch downloader for TVer.jp
Version: 1.0.0

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

VERSION = "1.0.0"

# Path to the file that holds the list of URLs to download
LINKS_FILE = "links.txt"
# yt-dlp archive file — stores IDs of already-downloaded videos to avoid re-downloading
ARCHIVE_FILE = "downloaded_archive.txt"


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
        "-o", "%(title)s [%(id)s].%(ext)s",   # filename template (no path prefix — -P handles that)
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
        print("\n❌ Error: yt-dlp not found. Install it or add it to PATH.")
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
    print(f"TVer Batch Downloader v{VERSION}")
    print("=" * 50)

    if not os.path.exists(LINKS_FILE) or os.path.getsize(LINKS_FILE) == 0:
        print(f"❌ Error: '{LINKS_FILE}' not found or empty.")
        print("Create the file and add URLs, one per line.")
        return

    links = _read_links(LINKS_FILE)
    if not links:
        print(f"ℹ️  No active URLs found in '{LINKS_FILE}'.")
        return

    # Create the output folder if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 Created download folder: {output_dir}")

    if proxy:
        print(f"🌐 Using proxy: {proxy}")

    print(f"📂 URLs to download:  {len(links)}")
    print(f"📦 Download archive:  {ARCHIVE_FILE}")
    print(f"💾 Output folder:     {output_dir}")
    print("-" * 50)

    success_count = 0
    fail_count = 0

    for i, url in enumerate(links, start=1):
        print(f"\n[{i}/{len(links)}] Downloading: {url}")
        print("-" * 50)

        ok = download_single(url, output_dir, proxy)

        if ok:
            print(f"✅ Done: {url}")
            _remove_link_from_file(LINKS_FILE, url)
            success_count += 1
        else:
            print(f"❌ Failed: {url}")
            print("   URL remains in links.txt for retry.")
            fail_count += 1

    print("\n" + "=" * 50)
    print(f"🎉 All done. Succeeded: {success_count}, Failed: {fail_count}")
    if fail_count:
        print(f"⚠️  Failed URLs are still in '{LINKS_FILE}'.")


if __name__ == "__main__":

    # 🚨 PROXY SETUP 🚨
    # If you need a Japanese IP to bypass TVer geo-restriction, replace None with the address:
    # HTTP example:   proxy_address = 'http://127.0.0.1:8080'
    # SOCKS5 example: proxy_address = 'socks5://user:pass@host:port'
    proxy_address = None

    download_tver_videos_from_file(proxy=proxy_address)
