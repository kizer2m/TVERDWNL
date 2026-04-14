# TVer Downloader 1

**Version: 1.0.0**

A set of Python scripts for downloading videos from the Japanese streaming service [TVer.jp](https://tver.jp) using `yt-dlp`.

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
- [Common Errors](#common-errors)
- [License](#license)

---

## Project Files

| File | Purpose |
|---|---|
| `tver_downloader.py` | Download a single video by URL |
| `tver_batch_downloader.py` | Batch-download a list of URLs from `links.txt` |
| `tver_downloader.cmd` | Shortcut to run the single downloader |
| `tver_batch_downloader.cmd` | Shortcut to run the batch downloader |
| `links.txt` | List of URLs for batch downloading |
| `downloaded_archive.txt` | yt-dlp archive of already-downloaded video IDs (auto-created) |

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

---

## Quick Start

### Single video

```bash
python tver_downloader.py
# → Enter the URL when prompted
```

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

---

## Script Reference

### tver\_downloader.py

Downloads **one** video from the URL entered by the user in the terminal.

**Behaviour:**
- Creates the `Downloads/` folder automatically if it does not exist.
- Saves the video as MP4 (video and audio streams are merged automatically).
- Embeds metadata into the output file.

**Run:**
```bash
python tver_downloader.py
```

---

### tver\_batch\_downloader.py

Downloads a **list** of videos from `links.txt`.

**Behaviour:**
- Reads URLs from `links.txt` (comment lines starting with `#` and blank lines are ignored).
- Creates the `Downloads/` folder automatically if it does not exist.
- Processes each URL one by one with `yt-dlp`.
- ✅ **After a successful download**, removes the URL from `links.txt`.
- ❌ **On failure**, leaves the URL in `links.txt` so it can be retried later.
- Records downloaded video IDs in `downloaded_archive.txt` to avoid re-downloading on the next run.

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
├── tver_downloader.cmd         # Run shortcut
├── tver_batch_downloader.cmd   # Run shortcut
├── links.txt                   # URL list for batch downloads
├── downloaded_archive.txt      # yt-dlp ID archive (auto-created)
└── Downloads/                  # Output folder for downloaded videos (auto-created)
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

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `yt-dlp not found` | yt-dlp is not installed or not in PATH | `pip install yt-dlp` |
| Non-zero exit code | Geo-restriction or video unavailable | Set up a Japanese proxy/VPN |
| Video skipped | Already present in `downloaded_archive.txt` | Remove its entry from the archive |
| `links.txt` is empty | No URLs to download | Add URLs to the file |

---

## License

MIT — free to use.

---

*TVer Downloader v1.0.0*
