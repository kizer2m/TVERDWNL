# TVer Downloader

**Version: 1.1.0**

A set of Python scripts for downloading videos from the Japanese streaming service [TVer.jp](https://tver.jp) using `yt-dlp`.  
Features a premium **CStyle Console UI** — colored output, progress bars, and consistent status icons across both scripts.

---

## Table of Contents

- [Project Files](#project-files)
- [Dependencies](#dependencies)
- [Quick Start](#quick-start)
- [Script Reference](#script-reference)
  - [tver\_downloader.py](#tver_downloaderpy)
  - [tver\_batch\_downloader.py](#tver_batch_downloaderpy)
- [Folder Structure](#folder-structure)
- [Proxy Setup](#proxy-setup)
- [Data Files](#data-files)
- [UI Design System](#ui-design-system)
- [Common Errors](#common-errors)
- [Changelog](#changelog)
- [License](#license)

---

## Project Files

| File | Purpose |
|---|---|
| `tver_downloader.py` | Download a single video by URL |
| `tver_batch_downloader.py` | Batch-download a list of URLs from `links.txt` |
| `tver_downloader.cmd` | Windows shortcut to run the single downloader |
| `tver_batch_downloader.cmd` | Windows shortcut to run the batch downloader |
| `links.txt` | List of URLs for batch downloading *(not tracked by git)* |
| `downloaded_archive.txt` | yt-dlp archive of already-downloaded video IDs *(auto-created, not tracked)* |
| `GEMINI.md` | Guidelines for the Gemini AI assistant working on this project |
| `CLAUDE.md` | Guidelines for the Claude AI assistant working on this project |

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

No additional Python packages are required — the scripts use only the standard library (`subprocess`, `sys`, `os`).

---

## Quick Start

### Single video

```bash
python tver_downloader.py
# → Enter the URL when prompted
```

Or double-click `tver_downloader.cmd` on Windows.

### Multiple videos (batch mode)

1. Add URLs to `links.txt`, one per line:

```
https://tver.jp/episodes/ep000000001
https://tver.jp/episodes/ep000000002
```

2. Run:

```bash
python tver_batch_downloader.py
```

Or double-click `tver_batch_downloader.cmd` on Windows.

---

## Script Reference

### tver\_downloader.py

Downloads **one** video from a URL entered interactively in the terminal.

**Behaviour:**
- Shows a CStyle boxed banner at startup.
- Prompts the user for a TVer URL with a styled `›` prompt.
- Creates the `Downloads/` folder automatically if it does not exist.
- Saves the video as MP4 (video + audio streams merged automatically).
- Embeds metadata into the output file via `--embed-metadata`.
- Displays clear `✓` / `✗` / `⚠` status feedback throughout the run.

**Run:**
```bash
python tver_downloader.py
```

---

### tver\_batch\_downloader.py

Downloads a **list** of videos from `links.txt`.

**Behaviour:**
- Shows a CStyle boxed banner and session info table at startup.
- Reads URLs from `links.txt` (comment lines starting with `#` and blank lines are ignored).
- Creates the `Downloads/` folder automatically if it does not exist.
- Processes each URL sequentially with `yt-dlp`.
- **After a successful download** → removes the URL from `links.txt`.
- **On failure** → leaves the URL in `links.txt` so it can be retried later.
- Records downloaded video IDs in `downloaded_archive.txt` to skip re-downloads on the next run.
- Prints a final summary with success / failure counts.

**Output filename template:** `%(title)s [%(id)s].mp4`

**Run:**
```bash
python tver_batch_downloader.py
```

---

## Folder Structure

```
TVERDWNL/
├── tver_downloader.py          # Single-video downloader
├── tver_batch_downloader.py    # Batch downloader
├── tver_downloader.cmd         # Windows run shortcut
├── tver_batch_downloader.cmd   # Windows run shortcut
├── links.txt                   # URL list for batch downloads  (git-ignored)
├── downloaded_archive.txt      # yt-dlp ID archive (auto-created, git-ignored)
├── Downloads/                  # Output folder  (auto-created, git-ignored)
├── GEMINI.md                   # AI assistant guidelines (Gemini)
├── CLAUDE.md                   # AI assistant guidelines (Claude)
└── README.md                   # This file
```

---

## Proxy Setup

TVer.jp is only accessible from Japan. To download from other countries you need a Japanese proxy or VPN.

In both scripts, find the line:

```python
proxy_address = None
```

and replace `None` with your proxy address:

```python
# HTTP proxy
proxy_address = 'http://127.0.0.1:8080'

# SOCKS5 proxy
proxy_address = 'socks5://user:password@host:port'
```

---

## Data Files

### links.txt

Contains the list of URLs for batch downloading. Format:

```
# This is a comment — this line will be skipped

https://tver.jp/episodes/ep000000001
https://tver.jp/episodes/ep000000002
```

> After each video is downloaded successfully, its URL is **automatically removed** from this file.

### downloaded_archive.txt

Created automatically by yt-dlp. Stores video IDs that have already been downloaded.  
If a video ID is present in the archive it **will not be downloaded again**, even if you add the URL back to `links.txt`.

> To re-download a video, delete its line from `downloaded_archive.txt`.

---

## UI Design System

Both scripts implement the **CStyle Console** design system:

| Element | Style |
|---|---|
| Startup banner | `╔══╗ ║ TITLE ║ ╚══╝` double-line box |
| Status icons | `✓` green · `✗` red · `⚠` yellow · `⟳` cyan · `✦` bold green · `│` gray |
| Separators | `  ────────────────────────────────────────────────────` dark gray |
| Info rows | `  │  Label   Value` dimmed key / bright value |
| Indent | 2-space leading indent on every output line |
| Progress bar | `━━━━────  62.5%  12.3 MB/s  ETA 00:04` (`━` filled / `─` empty) |
| Prompt | `  ›  Enter URL:` styled cyan arrow |

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `✗  yt-dlp not found` | yt-dlp is not installed or not in PATH | `pip install yt-dlp` |
| Non-zero exit code | Geo-restriction or video unavailable | Set up a Japanese proxy/VPN |
| Video skipped silently | Already present in `downloaded_archive.txt` | Remove its entry from the archive |
| `✗  links.txt not found or empty` | No URLs to download | Add URLs to `links.txt` |

---

## Changelog

### v1.1.0
- Applied **CStyle Console UI** to both scripts:
  - Boxed banner on startup
  - Icon-prefixed status lines (`✓` `✗` `⚠` `⟳` `✦`)
  - Dimmed key/value info rows for session details
  - Dark gray `─` separators framing download blocks and summaries
  - Consistent 2-space indent on all output lines
- Cleaned up emoji-based print statements
- Improved URL truncation in batch download block headers

### v1.0.0
- Initial release
- Single-video downloader (`tver_downloader.py`)
- Batch downloader (`tver_batch_downloader.py`) with auto-cleanup of `links.txt`
- Windows `.cmd` shortcuts
- `downloaded_archive.txt` support to skip already-downloaded videos

---

## License

MIT — free to use.

---

*TVer Downloader v1.1.0 · Author: kizer2m*
