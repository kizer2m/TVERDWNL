# TVer Downloader

**Version: 2.1.0**

A Python CLI tool for downloading videos from the Japanese streaming service [TVer.jp](https://tver.jp) using `yt-dlp`.  
Features a premium **CStyle Console UI** — colored output, animated progress bars, phase tracking (video / audio / merge), and consistent status icons.

---

## Table of Contents

- [Project Files](#project-files)
- [Dependencies](#dependencies)
- [Quick Start](#quick-start)
- [Menu Options](#menu-options)
- [Proxy Setup (.env)](#proxy-setup-env)
- [Data Files](#data-files)
- [Folder Structure](#folder-structure)
- [UI Design System](#ui-design-system)
- [Common Errors](#common-errors)
- [Changelog](#changelog)
- [License](#license)

---

## Project Files

| File | Purpose |
|---|---|
| `tver.py` | Main script — interactive 4-option menu |
| `tver.cmd` | Windows shortcut to run `tver.py` |
| `.env` | Proxy configuration *(not tracked by git after initial push)* |
| `links.txt` | URL list for batch downloads *(auto-created, git-ignored)* |
| `downloaded_archive.txt` | yt-dlp archive of already-downloaded IDs *(auto-created, git-ignored)* |

---

## Dependencies

- **Python 3.10+**
- **yt-dlp**

Install yt-dlp:

```bash
# via pip
pip install yt-dlp

# via winget (Windows)
winget install yt-dlp

# update to the latest version
yt-dlp -U
```

No additional Python packages are required — the script uses only the standard library.

---

## Quick Start

```bash
python tver.py
```

Or double-click `tver.cmd` on Windows.

On each start the script automatically:
1. Checks that `yt-dlp` is available in PATH
2. Creates `Downloads/`, `Downloads/thumbnails/`, `links.txt`, and `.env` if they are missing
3. Reads the proxy from `.env` and validates it (TCP connection to the proxy host)
4. Opens the interactive menu

---

## Menu Options

```
  ──────────────────────────────────────────────────────────
  │  1  Download single video
  │  2  Download from file  (links.txt)
  │  3  Download playlist
  │  4  Exit
  ──────────────────────────────────────────────────────────
```

### 1 — Download single video
Paste any TVer.jp episode URL when prompted.  
The script fetches title + description, downloads video and audio streams with animated per-phase progress bars, merges them to MP4, and saves a thumbnail and a metadata `.txt` file alongside the video.

### 2 — Download from links.txt
Reads URLs from `links.txt` (one per line; lines starting with `#` are ignored).  
Each successful download removes its URL from `links.txt`. Failed URLs stay for retry.  
Duplicate detection is done against `downloaded_archive.txt`.

### 3 — Download playlist
Paste a TVer.jp series / playlist URL.  
The script lists all episodes, checks the archive, and downloads only new ones.

---

## Proxy Setup (.env)

TVer.jp is **geo-restricted to Japan**. To download from outside Japan you need a Japanese proxy or VPN.

### Configuration

Edit the `.env` file in the project root (auto-created on first run):

```ini
# ─────────────────────────────────────────────────────────────────────
#  TVer Downloader — Proxy Configuration
# ─────────────────────────────────────────────────────────────────────
#
#  Supported proxy formats:
#
#    HTTP proxy:
#      TVER_PROXY=http://host:port
#      TVER_PROXY=http://username:password@host:port
#
#    HTTPS proxy:
#      TVER_PROXY=https://host:port
#      TVER_PROXY=https://username:password@host:port
#
#    SOCKS5 proxy (recommended for speed):
#      TVER_PROXY=socks5://host:port
#      TVER_PROXY=socks5://username:password@host:port
#
#  To disable proxy, leave the value empty:
#      TVER_PROXY=
#
# ─────────────────────────────────────────────────────────────────────

TVER_PROXY=socks5://login:password@IP:port
```

### Proxy check on startup

Every time the script starts it opens a TCP connection to the proxy host on the configured port.

| Result | Meaning |
|---|---|
| `✓  Proxy is ready.` | Host is reachable — downloads will use it |
| `✗  Proxy is not responding.` | Host unreachable — check credentials / switch VPN |
| `⚠  No proxy configured.` | `TVER_PROXY` is empty — TVer may block the request |

---

## Data Files

### links.txt

URL list for batch mode. Format:

```
# This is a comment — skipped
https://tver.jp/episodes/ep000000001
https://tver.jp/episodes/ep000000002
```

After each successful download the URL is **automatically removed** from this file.

### downloaded_archive.txt

Maintained automatically by yt-dlp. Stores video IDs already downloaded.  
A video whose ID appears in the archive will be **skipped** even if the URL is added again.

> To force a re-download, delete the corresponding line from `downloaded_archive.txt`.

---

## Folder Structure

```
TVERDWNL/
├── tver.py                     # Main script (unified downloader)
├── tver.cmd                    # Windows run shortcut
├── .env                        # Proxy config  (git-ignored after initial push)
├── links.txt                   # URL list for batch downloads  (git-ignored)
├── downloaded_archive.txt      # yt-dlp ID archive  (auto-created, git-ignored)
├── Downloads/                  # Output folder  (auto-created, git-ignored)
│   └── thumbnails/             # Downloaded thumbnails
└── README.md
```

---

## UI Design System

The script uses the **CStyle Console** design system throughout:

| Element | Style |
|---|---|
| Startup banner | `╔══╗ ║ TITLE ║ ╚══╝` double-line box |
| Status icons | `✓` green · `✗` red · `⚠` yellow · `⟳` cyan · `✦` bold green · `│` gray |
| Separators | `  ────────────────────────────────────────────────────` dark gray |
| Info rows | `  │  Label   Value` dimmed key / bright value |
| Indent | 2-space leading indent on every output line |
| Progress bar | `━━━━────  62.5%  12.3 MB/s  ETA 00:04` (`━` filled / `─` empty) |
| Phase labels | `▶ Video` blue · `♪ Audio` magenta · `⊕ Merge` green |
| Prompt | `  ›  Enter URL:` styled cyan arrow |

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `✗  yt-dlp not found` | yt-dlp is not installed or not in PATH | `pip install yt-dlp` |
| `✗  Proxy is not responding` | Proxy host unreachable | Fix credentials or enable a Japanese VPN |
| `⚠  No proxy configured` | `TVER_PROXY` is empty | Add proxy to `.env` or use a VPN |
| Non-zero exit code from yt-dlp | Geo-restriction or video removed | Ensure Japanese IP is active |
| Video skipped silently | ID already in `downloaded_archive.txt` | Remove its entry from the archive |
| `✗  links.txt not found or empty` | Batch mode with no URLs | Add URLs to `links.txt` |

---

## Changelog

### v2.1.0
- `.env` file for proxy configuration (no more hardcoded proxy in code)
- Startup environment check: auto-creates `Downloads/`, `thumbnails/`, `links.txt`, `.env`
- TCP-based proxy validation on every startup (`socket.create_connection`)
- Removed `tver_downloader.py`, `tver_batch_downloader.py`, and their `.cmd` launchers
- All functionality consolidated into `tver.py`

### v2.0.0
- Unified all functionality into a single `tver.py` with a 4-option interactive menu
- Per-stream animated progress bars with phase labels (Video / Audio / Merge)
- Merge phase animated with elapsed timer via reader thread + queue
- Thumbnail download → `Downloads/thumbnails/`
- Metadata (title + description) saved as `.txt` alongside each video
- Playlist download support
- Duplicate detection via `downloaded_archive.txt`

### v1.1.0
- Applied **CStyle Console UI** to both original scripts

### v1.0.0
- Initial release with `tver_downloader.py` and `tver_batch_downloader.py`

---

## License

MIT — free to use.

---

*TVer Downloader v2.1.0 · Author: kizer2m*
