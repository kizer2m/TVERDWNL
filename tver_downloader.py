"""
tver_downloader.py — Одиночный загрузчик видео с TVer.jp
Версия: 1.0.0

Описание:
    Скачивает одно видео с TVer.jp по введённому URL при помощи yt-dlp.
    Видео сохраняется в папку Downloads (создаётся автоматически).

Использование:
    python tver_downloader.py
    -> Введите URL видео при запросе.

Зависимости:
    - yt-dlp  (установить: pip install yt-dlp  или  winget install yt-dlp)

Заметки:
    - Для обхода гео-блокировки TVer установите переменную proxy_address.
    - Поддерживаются HTTP/HTTPS и SOCKS5 прокси.

Автор: (ваш никнейм)
Лицензия: MIT
"""

import subprocess
import sys
import os

VERSION = "1.0.0"

def download_tver_video(url, output_dir="Downloads", proxy=None):
    """
    Скачивает видео с TVer, используя yt-dlp.

    :param url: URL видео на TVer.jp (например, https://tver.jp/episodes/...)
    :param output_dir: Папка для сохранения файла.
    :param proxy: Опционально, строка прокси (например, 'http://127.0.0.1:8080').
                  Требуется для обхода гео-ограничений TVer.
    """
    
    print(f"Попытка скачать: {url}")
    
    # Создаем папку для загрузок, если она не существует
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Создана папка для загрузок: {output_dir}")

    # Основные аргументы yt-dlp:
    # -P {output_dir}: Указывает папку вывода
    # --merge-output-format mp4: yt-dlp автоматически выберет лучшие потоки и объединит их в mp4
    # (убрана опция -f best, вызвавшая ошибку)
    command = [
        "yt-dlp",
        "-P", output_dir,
        "--merge-output-format", "mp4",
        "--embed-metadata",
        "--no-mtime",
        url
    ]

    # Добавляем прокси, если указан
    if proxy:
        # ВАЖНО: Требуется для обхода гео-блокировки TVer, если вы не в Японии.
        command.extend(["--proxy", proxy])
        print(f"Используется прокси: {proxy}")
        
    print("-" * 30)
    print(f"Выполняемая команда: {' '.join(command)}")
    print("-" * 30)

    try:
        # Запускаем yt-dlp
        # capture_output=False позволяет видеть прогресс yt-dlp в консоли.
        process = subprocess.run(command, check=True, capture_output=False, text=False)
        print("\n✅ Загрузка завершена.")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка при выполнении yt-dlp. Код возврата: {e.returncode}")
        print("--------------------")
        print("Возможные причины:")
        print("1. Гео-блокировка. Убедитесь, что ваш VPN/прокси с японским IP работает.")
        print("2. Видео удалено или недоступно.")
        print("--------------------")
    except FileNotFoundError:
        print("\n❌ Ошибка: yt-dlp не найден. Убедитесь, что он установлен и доступен в PATH.")
        sys.exit(1)


if __name__ == "__main__":
    tver_url = input("Введите URL видео с TVer (например, https://tver.jp/episodes/...): ").strip()
    
    # 🚨 НАСТРОЙКА ПРОКСИ 🚨
    # Если вам нужно использовать прокси (японский IP), замените None на строку:
    # Пример HTTP: 'http://127.0.0.1:8080'
    # Пример SOCKS5: 'socks5://user:pass@host:port'
    proxy_address = None 
    
    if not tver_url:
        print("URL не был введен. Завершение.")
    else:
        download_tver_video(tver_url, proxy=proxy_address)

