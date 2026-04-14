"""
tver_downloader.py — Single-video downloader for TVer.jp
Version: 1.0.0

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

VERSION = "1.0.0"


def download_tver_video(url: str, output_dir: str = "Downloads", proxy: str | None = None) -> None:
    """
    Download a single TVer.jp video using yt-dlp.

    :param url:        Video URL on TVer.jp (e.g. https://tver.jp/episodes/...)
    :param output_dir: Destination folder for the downloaded file.
    :param proxy:      Optional proxy string (e.g. 'http://127.0.0.1:8080').
                       Required to bypass TVer geo-restrictions outside Japan.
    """

    print(f"Attempting to download: {url}")

    # Create the output folder if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created download folder: {output_dir}")

    # yt-dlp arguments:
    #   -P {output_dir}            : set the output directory
    #   --merge-output-format mp4  : merge best video + audio streams into mp4
    #   --embed-metadata           : embed title/description metadata into the file
    #   --no-mtime                 : use the current time as the file modification time
    command = [
        "yt-dlp",
        "-P", output_dir,
        "--merge-output-format", "mp4",
        "--embed-metadata",
        "--no-mtime",
        url,
    ]

    # Append proxy flag if a proxy address was provided
    if proxy:
        # NOTE: Required to bypass TVer geo-blocking when accessing from outside Japan.
        command.extend(["--proxy", proxy])
        print(f"Using proxy: {proxy}")

    print("-" * 30)
    print(f"Running command: {' '.join(command)}")
    print("-" * 30)

    try:
        # Run yt-dlp; capture_output=False lets its progress bar show in the terminal.
        subprocess.run(command, check=True, capture_output=False, text=False)
        print("\n✅ Download complete.")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ yt-dlp exited with error code: {e.returncode}")
        print("--------------------")
        print("Possible reasons:")
        print("1. Geo-restriction. Make sure your VPN/proxy with a Japanese IP is active.")
        print("2. The video has been removed or is unavailable.")
        print("--------------------")

    except FileNotFoundError:
        print("\n❌ Error: yt-dlp not found. Make sure it is installed and available in PATH.")
        sys.exit(1)


if __name__ == "__main__":
    tver_url = input("Enter the TVer video URL (e.g. https://tver.jp/episodes/...): ").strip()

    # 🚨 PROXY SETUP 🚨
    # If you need to use a proxy (Japanese IP), replace None with the address string:
    # HTTP example:   proxy_address = 'http://127.0.0.1:8080'
    # SOCKS5 example: proxy_address = 'socks5://user:pass@host:port'
    proxy_address = None

    if not tver_url:
        print("No URL entered. Exiting.")
    else:
        download_tver_video(tver_url, proxy=proxy_address)
