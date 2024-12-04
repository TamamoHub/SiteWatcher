import threading
import time
import requests
from datetime import datetime, timedelta
import winsound
import json
import os
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QSystemTrayIcon, QWidget, QVBoxLayout, QLabel, QPushButton, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor, QPalette
from PyQt6.QtCore import Qt, QTimer
import urllib3

class Site:
    def __init__(self, url, name=None, group='Загальне'):
        self.url = url
        self.name = name or url
        self.group = group
        self.is_active = True
        self.last_status = None
        self.last_check_time = None
        self.up_sound = "SystemAsterisk"
        self.down_sound = "SystemHand"
        self.status_history = []
        self.error_count = 0
        self.max_errors = 3
        self.last_error = None
        self.check_interval = 30  # інтервал перевірки в секундах
        self.next_check_time = None

    def update_status(self, status, check_time):
        self.status_history.append({
            'time': check_time,
            'status': status
        })
        
        if len(self.status_history) > 100:
            self.status_history = self.status_history[-100:]
        
        self.last_status = status
        self.last_check_time = check_time
        self.next_check_time = check_time + timedelta(seconds=self.check_interval)

class NotificationSignals(QObject):
    show_notification = pyqtSignal(str, str, str)  # title, message, type

class StatusSignals(QObject):
    site_status_changed = pyqtSignal(str, bool, str)  # url, status, message

class MoodleMonitor(threading.Thread):
    def __init__(self, check_interval=30):
        super().__init__()
        self.check_interval = check_interval
        self.sites = {}
        self.running = True
        self.signals = StatusSignals()
        self.notification_signals = NotificationSignals()
        self.site_status_changed = self.signals.site_status_changed
        
        # Вимикаємо попередження про незахищені запити
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        if not os.path.exists('sites_config.json'):
            self.save_config()
        
        self.load_config()

    def show_notification(self, title, message, notification_type="info"):
        """Відправляє сигнал для показу повідомлення в головному потоці"""
        self.notification_signals.show_notification.emit(title, message, notification_type)

    def check_site(self, site):
        try:
            # Налаштування для requests
            session = requests.Session()
            session.mount('http://', requests.adapters.HTTPAdapter(
                max_retries=3,
                pool_connections=100,
                pool_maxsize=100
            ))
            session.mount('https://', requests.adapters.HTTPAdapter(
                max_retries=3,
                pool_connections=100,
                pool_maxsize=100
            ))
            
            # Встановлюємо більший таймаут і додаємо headers
            response = session.get(
                site.url, 
                timeout=30,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                verify=False  # Вимикаємо перевірку SSL для локальних адрес
            )
            
            current_time = datetime.now()
            
            if response.status_code == 200:
                site.error_count = 0
                if site.last_status is False:
                    winsound.PlaySound(site.up_sound, winsound.SND_ALIAS)
                    
                    title = f"{site.name} відновив роботу"
                    message = f"""
🌐 Сайт знову доступний
📍 URL: {site.url}
📁 Група: {site.group}
⏰ Час: {current_time.strftime('%H:%M:%S')}
                    """.strip()
                    
                    self.show_notification(title, message, "success")
                    self.site_status_changed.emit(site.url, True, title)
                
                site.update_status(True, current_time)
                site.last_error = None
            else:
                self._handle_site_error(site, current_time, f"HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError as e:
            error_msg = "Помилка підключення: Сервер недоступний"
            self._handle_site_error(site, datetime.now(), error_msg)
        except requests.exceptions.Timeout as e:
            error_msg = "Помилка: Час очікування минув"
            self._handle_site_error(site, datetime.now(), error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Помилка запиту: {str(e)}"
            self._handle_site_error(site, datetime.now(), error_msg)
        except Exception as e:
            error_msg = f"Невідома помилка: {str(e)}"
            self._handle_site_error(site, datetime.now(), error_msg)

    def _handle_site_error(self, site, current_time, error_message):
        site.error_count += 1
        site.last_error = error_message
        
        if site.error_count >= site.max_errors:
            if site.last_status is not False:
                winsound.PlaySound(site.down_sound, winsound.SND_ALIAS)
                
                title = f"{site.name} не працює"
                message = f"""
⚠️ Сайт недоступний
📍 URL: {site.url}
📁 Група: {site.group}
⏰ Час: {current_time.strftime('%H:%M:%S')}
❌ Помилка: {error_message}
                """.strip()
                
                self.show_notification(title, message, "error")
                self.site_status_changed.emit(site.url, False, title)
            
            site.update_status(False, current_time)

    def run(self):
        while self.running:
            current_time = datetime.now()
            for site in self.sites.values():
                if site.is_active:
                    if not site.next_check_time or current_time >= site.next_check_time:
                        self.check_site(site)
            time.sleep(1)

    def stop(self):
        self.running = False

    def add_site(self, url, name=None, group='Загальне'):
        if url not in self.sites:
            self.sites[url] = Site(url, name, group)
            self.save_config()
            return True
        return False

    def remove_site(self, url):
        if url in self.sites:
            del self.sites[url]
            self.save_config()
            return True
        return False

    def toggle_site(self, url):
        if url in self.sites:
            self.sites[url].is_active = not self.sites[url].is_active
            self.save_config()
            return True
        return False

    def set_site_sounds(self, url, up_sound=None, down_sound=None):
        if url in self.sites:
            site = self.sites[url]
            if up_sound:
                site.up_sound = up_sound
            if down_sound:
                site.down_sound = down_sound
            self.save_config()
            return True
        return False

    def load_config(self):
        try:
            if os.path.exists('sites_config.json'):
                with open('sites_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for url, site_config in config.get('sites', {}).items():
                        self.add_site(
                            url,
                            name=site_config.get('name'),
                            group=site_config.get('group', 'Загальне')
                        )
                        site = self.sites.get(url)
                        if site:
                            site.is_active = site_config.get('is_active', True)
                            site.up_sound = site_config.get('up_sound')
                            site.down_sound = site_config.get('down_sound')
        except Exception as e:
            print(f"Error loading config: {e}")
            self.save_config()
    
    def save_config(self):
        try:
            config = {
                'sites': {
                    url: {
                        'name': site.name,
                        'group': site.group,
                        'is_active': site.is_active,
                        'up_sound': site.up_sound,
                        'down_sound': site.down_sound
                    }
                    for url, site in self.sites.items()
                },
                'save_time': datetime.now().isoformat()
            }
            
            with open('sites_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def wait(self):
        if self.is_alive():
            self.join()