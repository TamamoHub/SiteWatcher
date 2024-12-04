import PyInstaller.__main__
import os

# Створюємо список файлів та папок для включення
additional_files = [
    ('templates', 'templates'),
    ('sounds', 'sounds'),  # Папка для звуків
    ('sites_config.json', '.'),  # Конфігурація сайтів
]

# Формуємо команду для PyInstaller
command = [
    'main.py',  # Головний файл
    '--name=SiteMonitor',  # Назва exe файлу
    '--onefile',  # Створити один exe файл
    '--windowed',  # Приховати консоль
    '--icon=icon.ico',  # Іконка (створіть або видаліть цей параметр, якщо немає)
    '--add-data=templates;templates',  # Додаємо папку templates
    '--add-data=sounds;sounds',  # Додаємо папку sounds
    '--add-data=sites_config.json;.',  # Додаємо конфіг
    # Необхідні імпорти
    '--hidden-import=PyQt6.QtWebEngineCore',
    '--hidden-import=engineio.async_drivers.threading',
    '--hidden-import=PyQt6.QtGui',
    '--hidden-import=PyQt6.QtCore',
    '--hidden-import=PyQt6.QtWidgets',
    '--hidden-import=PyQt6.QtWebEngineWidgets',
    # Збираємо всі необхідні пакети
    '--collect-all=flask',
    '--collect-all=winsound',
]

# Запускаємо PyInstaller
PyInstaller.__main__.run(command) 