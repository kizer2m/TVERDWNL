"""
tver_batch_downloader.py — Пакетный загрузчик видео с TVer.jp
Версия: 1.0.0

Описание:
    Читает список ссылок из файла links.txt и скачивает каждое видео
    по очереди при помощи yt-dlp.
    После успешной загрузки и объединения видео+аудио ссылка
    автоматически удаляется из links.txt.
    Уже скачанные видео пропускаются (контролируется через downloaded_archive.txt).
    Все файлы сохраняются в папку Downloads (создаётся автоматически).

Использование:
    1. Добавьте ссылки в links.txt (каждая ссылка — с новой строки).
    2. Запустите: python tver_batch_downloader.py

Зависимости:
    - yt-dlp  (установить: pip install yt-dlp  или  winget install yt-dlp)

Файлы:
    links.txt              — список URL для загрузки (один на строку)
    downloaded_archive.txt — архив ID уже скачанных видео (создаётся автоматически)
    Downloads/             — папка с загруженными файлами  (создаётся автоматически)

Заметки:
    - Для обхода гео-блокировки TVer установите переменную proxy_address.
    - Поддерживаются HTTP/HTTPS и SOCKS5 прокси.
    - Комментарии (#) и пустые строки в links.txt пропускаются.

Автор: (ваш никнейм)
Лицензия: MIT
"""

import subprocess
import sys
import os

VERSION = "1.0.0"

# Имя файла, содержащего список ссылок
LINKS_FILE = "links.txt"
# Файл-архив для yt-dlp (хранит ID уже скачанных видео, чтобы не качать повторно)
ARCHIVE_FILE = "downloaded_archive.txt"


def _read_links(path: str) -> list[str]:
    """Возвращает список непустых ссылок из файла (строки-комментарии # пропускаются)."""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]


def _remove_link_from_file(path: str, url: str) -> None:
    """Удаляет конкретную ссылку из файла links.txt после успешной загрузки."""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    # Оставляем все строки, кроме той, что совпадает с url (с учётом пробелов)
    new_lines = [ln for ln in lines if ln.strip() != url]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
        if new_lines:          # добавляем финальный перевод строки, если файл не пуст
            f.write("\n")


def download_single(url: str, output_dir: str, proxy: str | None) -> bool:
    """
    Скачивает одно видео по переданному URL.

    :param url:        URL видео на TVer.jp
    :param output_dir: Папка для сохранения файла
    :param proxy:      Строка прокси или None
    :returns:          True — загрузка прошла успешно, False — ошибка
    """
    command = [
        "yt-dlp",
        "--download-archive", ARCHIVE_FILE,
        "-P", output_dir,
        "--merge-output-format", "mp4",
        "-o", "%(title)s [%(id)s].%(ext)s",
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
        print("\n❌ Ошибка: yt-dlp не найден. Установите его или добавьте в PATH.")
        sys.exit(1)


def download_tver_videos_from_file(output_dir: str = "Downloads", proxy: str | None = None) -> None:
    """
    Пакетная загрузка видео с TVer из файла links.txt.

    Для каждой ссылки:
      - запускает yt-dlp;
      - при успехе удаляет ссылку из links.txt;
      - при ошибке оставляет ссылку в файле для повторной попытки.

    :param output_dir: Папка для сохранения видео (по умолчанию — Downloads)
    :param proxy:      Строка прокси или None
    """
    print(f"TVer Batch Downloader v{VERSION}")
    print("=" * 50)

    if not os.path.exists(LINKS_FILE) or os.path.getsize(LINKS_FILE) == 0:
        print(f"❌ Ошибка: Файл '{LINKS_FILE}' не найден или пуст.")
        print("Создайте файл и вставьте в него ссылки (каждая с новой строки).")
        return

    links = _read_links(LINKS_FILE)
    if not links:
        print(f"ℹ️  В файле '{LINKS_FILE}' нет активных ссылок.")
        return

    # Создаём папку для загрузок, если её нет
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 Создана папка для загрузок: {output_dir}")

    if proxy:
        print(f"🌐 Используется прокси: {proxy}")

    print(f"📂 Всего ссылок к загрузке: {len(links)}")
    print(f"📦 Архив уже скачанных:      {ARCHIVE_FILE}")
    print(f"💾 Папка вывода:             {output_dir}")
    print("-" * 50)

    success_count = 0
    fail_count = 0

    for i, url in enumerate(links, start=1):
        print(f"\n[{i}/{len(links)}] Скачиваю: {url}")
        print("-" * 50)

        ok = download_single(url, output_dir, proxy)

        if ok:
            print(f"✅ Готово: {url}")
            _remove_link_from_file(LINKS_FILE, url)
            success_count += 1
        else:
            print(f"❌ Ошибка при загрузке: {url}")
            print("   Ссылка остаётся в links.txt для повторной попытки.")
            fail_count += 1

    print("\n" + "=" * 50)
    print(f"🎉 Загрузка завершена. Успешно: {success_count}, Ошибок: {fail_count}")
    if fail_count:
        print(f"⚠️  Неудачные ссылки остались в '{LINKS_FILE}'.")


if __name__ == "__main__":

    # 🚨 НАСТРОЙКА ПРОКСИ 🚨
    # Если вам нужно использовать прокси (японский IP), замените None на строку:
    # Пример HTTP:   proxy_address = 'http://127.0.0.1:8080'
    # Пример SOCKS5: proxy_address = 'socks5://user:pass@host:port'
    proxy_address = None

    download_tver_videos_from_file(proxy=proxy_address)
