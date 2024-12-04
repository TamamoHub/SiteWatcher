# 🌐 SiteMonitor

<div align="center">

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg?cacheSeconds=2592000)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
[![Windows Support](https://img.shields.io/badge/Windows-0078D6?style=flat&logo=windows&logoColor=white)](https://www.microsoft.com/windows)

**Сучасний десктопний додаток для моніторингу доступності веб-сайтів**

[🚀 Можливості](#-можливості) •
[📥 Встановлення](#-встановлення) •
[🛠️ Розробка](#%EF%B8%8F-розробка) •
[📖 Документація](#-документація) •
[📝 Ліцензія](#-ліцензія)

<img src="docs/images/preview.png" alt="SiteMonitor Preview" width="800"/>

</div>

## 🚀 Можливості

### 🎯 Основні функції
- 🔄 Моніторинг сайтів в реальному часі
- 📊 Графіки статусу для кожного сайту
- 📁 Групування сайтів за категоріями
- 🔍 Сортування за назвою, статусом та часом
- 💾 Експорт та імпорт конфігурації

### 🎨 Інтерфейс
- 🌓 Темна та світла теми
- 💫 Анімовані сповіщення
- 🎯 Стекування повідомлень
- 🖼️ Сучасний Fluent-подібний дизайн
- 📱 Адаптивний інтерфейс

## 📥 Встановлення

### Використання готового релізу

1. Завантажте останній реліз з [сторінки релізів](https://github.com/yourusername/SiteMonitor/releases)
2. Розпакуйте архів
3. Запустіть `SiteMonitor.exe`

### Встановлення з вихідного коду

```bash
# Клонуємо репозиторій
git clone https://github.com/yourusername/SiteMonitor.git
cd SiteMonitor

# Створюємо віртуальне середовище
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows

# Встановлюємо залежності
pip install -r requirements.txt

# Запускаємо програму
python main.py
```

## 🛠️ Розробка

### Вимоги
- Python 3.8+
- PyQt6
- Flask
- Requests

### Структура проекту
```
SiteMonitor/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   └── monitor.py
│   └── ui/
│       └── templates/
├── sounds/
├── templates/
├── main.py
├── build.py
├── requirements.txt
└── README.md
```

### Збірка
```bash
# Встановлюємо PyInstaller
pip install pyinstaller

# Збираємо проект
python build.py
```

## 📖 Документація

### Конфігурація сайтів
Конфігурація сайтів зберігається в файлі `sites_config.json`:
```json
{
    "sites": {
        "https://example.com": {
            "name": "Example Site",
            "group": "Main",
            "is_active": true,
            "up_sound": "SystemAsterisk",
            "down_sound": "SystemHand"
        }
    }
}
```

### API Endpoints
- `GET /` - Головна сторінка
- `GET /get_sites` - Отримати список сайтів
- `POST /add_site` - Додати новий сайт
- `POST /remove_site` - Видалити сайт
- `POST /toggle_site` - Увімкнути/вимкнути моніторинг
- `GET /export_config` - Експортувати конфігурацію
- `POST /import_config` - Імпортувати конфігурацію


## 📝 Ліцензія

Цей проект ліцензовано за умовами ліцензії MIT - див. файл [LICENSE](LICENSE) для деталей.

## 🙏 Подяки

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) за чудовий GUI фреймворк
- [Flask](https://flask.palletsprojects.com/) за легкий веб-фрейморк
- [Chart.js](https://www.chartjs.org/) за красиві графіки
- [Tailwind CSS](https://tailwindcss.com/) за стильний дизайн

## 👥 Автори

- [@TamamoHub](https://github.com/TamamoHub) - Ідея та початкова робота

## 💙💛 Зроблено в Україні з любов'ю

---

<div align="center">
    <sub>Якщо вам подобається проєкт, поставте ⭐️!</sub>
</div> 
