from PyQt6.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon, 
                            QMenu, QMessageBox, QWidget, QVBoxLayout, QLabel)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtGui import QIcon
from flask import Flask, render_template, request, jsonify, send_file
from src.core.monitor import MoodleMonitor
import sys
import threading
import os
from werkzeug.utils import secure_filename
import time
import winsound
import json
from datetime import datetime
import signal
import requests

app = Flask(__name__)
monitor = None
server_thread = None

UPLOAD_FOLDER = 'sounds'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_sites')
def get_sites():
    sites_data = {}
    for url, site in monitor.sites.items():
        sites_data[url] = {
            'name': site.name,
            'status': site.last_status,
            'is_active': site.is_active,
            'last_check': site.last_check_time,
            'up_sound': site.up_sound,
            'down_sound': site.down_sound,
            'group': site.group,
            'history': {
                'times': [h['time'].strftime('%H:%M:%S') for h in site.status_history[-20:]],
                'statuses': [1 if h['status'] else 0 for h in site.status_history[-20:]]
            }
        }
    return jsonify(sites_data)

@app.route('/add_site', methods=['POST'])
def add_site():
    data = request.json
    success = monitor.add_site(
        data['url'], 
        name=data.get('name'),
        group=data.get('group', 'Загальне')
    )
    return jsonify({'success': success})

@app.route('/remove_site', methods=['POST'])
def remove_site():
    data = request.json
    success = monitor.remove_site(data['url'])
    return jsonify({'success': success})

@app.route('/toggle_site', methods=['POST'])
def toggle_site():
    data = request.json
    success = monitor.toggle_site(data['url'])
    return jsonify({'success': success})

@app.route('/set_sounds', methods=['POST'])
def set_sounds():
    data = request.json
    success = monitor.set_site_sounds(
        data['url'], 
        data.get('up_sound'), 
        data.get('down_sound')
    )
    return jsonify({'success': success})

@app.route('/export_config', methods=['GET'])
def export_config():
    config = {
        'sites': {
            url: {
                'name': site.name,
                'group': site.group,
                'is_active': site.is_active,
                'up_sound': site.up_sound,
                'down_sound': site.down_sound
            }
            for url, site in monitor.sites.items()
        },
        'export_time': datetime.now().isoformat()
    }
    
    # Зберігаємо конфігурацію у тимчасовий файл
    temp_path = 'temp_config.json'
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    return send_file(
        temp_path,
        as_attachment=True,
        download_name='sites_config.json',
        mimetype='application/json'
    )

@app.route('/import_config', methods=['POST'])
def import_config():
    if 'config' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['config']
    try:
        config = json.load(file)
        for url, site_config in config['sites'].items():
            monitor.add_site(
                url,
                name=site_config.get('name'),
                group=site_config.get('group', 'Загальне')
            )
            site = monitor.sites.get(url)
            if site:
                site.is_active = site_config.get('is_active', True)
                site.up_sound = site_config.get('up_sound')
                site.down_sound = site_config.get('down_sound')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/upload_sound', methods=['POST'])
def upload_sound():
    if 'sound_file' not in request.files:
        return jsonify({'success': False})
    
    file = request.files['sound_file']
    url = request.form['url']
    sound_type = request.form['sound_type']
    
    if file:
        filename = secure_filename(file.filename)
        # Створюємо унікальне ім'я файлу
        base, ext = os.path.splitext(filename)
        filename = f"{base}_{sound_type}_{int(time.time())}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'file_path': file_path
        })
    
    return jsonify({'success': False})

@app.route('/play_sound', methods=['POST'])
def play_sound():
    data = request.json
    sound_name = data.get('sound')
    if sound_name:
        try:
            winsound.PlaySound(sound_name, winsound.SND_ALIAS)
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400
    return jsonify({'status': 'error', 'message': 'No sound specified'}), 400

@app.route('/shutdown')
def shutdown():
    # Функція для завершення Flask серверу
    os._exit(0)
    return 'Server shutting down...'

class CustomNotification(QWidget):
    def __init__(self, title, message, notification_type="info"):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Налаштування кольорів в залежності від типу
        if notification_type == "success":
            bg_color = "#10B981"  # зелений
            icon = "✅"
        elif notification_type == "error":
            bg_color = "#EF4444"  # червоний
            icon = "❌"
        else:
            bg_color = "#3B82F6"  # синій
            icon = "ℹ️"

        # Створюємо головний layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Створюємо віджет-контейнер для стилізації
        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet(f"""
            #container {{
                background-color: {bg_color};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        container_layout = QVBoxLayout()
        container.setLayout(container_layout)
        
        # Заголовок
        title_label = QLabel(f"{icon} {title}")
        title_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 5px;
        """)
        container_layout.addWidget(title_label)
        
        # Повідомлення
        message_label = QLabel(message)
        message_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 14px;
        """)
        message_label.setWordWrap(True)
        container_layout.addWidget(message_label)
        
        # Додаємо контейнер до головного layout
        layout.addWidget(container)
        
        # Налаштовуємо розмір та позицію
        self.setMinimumWidth(300)
        self.adjustSize()
        
        # Таймер для автоматичного закриття
        self.timer = QTimer()
        self.timer.timeout.connect(self.fade_out)
        self.timer.start(5000)  # 5 секунд
        
        # Анімація появи
        self.setWindowOpacity(0)
        self.fade_in()
        
    def fade_in(self):
        self.animation_step = 0
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self._fade_step)
        self.fade_timer.start(20)
        
    def _fade_step(self):
        self.animation_step += 0.1
        self.setWindowOpacity(self.animation_step)
        if self.animation_step >= 1:
            self.fade_timer.stop()
            
    def fade_out(self):
        self.animation_step = 1
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self._fade_out_step)
        self.fade_timer.start(20)
        
    def _fade_out_step(self):
        self.animation_step -= 0.1
        self.setWindowOpacity(self.animation_step)
        if self.animation_step <= 0:
            self.fade_timer.stop()
            self.close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сайт Монітор")
        self.setGeometry(100, 100, 1200, 800)
        
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("http://127.0.0.1:5001"))
        self.setCentralWidget(self.browser)
        
        self.setup_system_tray()
        self.is_minimized_to_tray = False
        self.notifications = []
        
        # Підключаємо обробники сигналів
        monitor.site_status_changed.connect(self.on_site_status_changed)
        monitor.notification_signals.show_notification.connect(self.show_notification)

    def show_notification(self, title, message, notification_type):
        """Показує кастомне повідомлення"""
        notification = CustomNotification(title, message, notification_type)
        
        # Розраховуємо позицію (правий нижній кут екрану)
        screen = QApplication.primaryScreen().geometry()
        notification_height = notification.height()
        
        # Зміщуємо існуючі повідомлення вгору
        for existing in self.notifications[:]:
            if not existing.isVisible():
                self.notifications.remove(existing)
                continue
            existing.move(screen.width() - existing.width() - 20,
                        screen.height() - existing.height() - 20 - 
                        (len(self.notifications) * (notification_height + 10)))
        
        # Додаємо нове повідомлення
        notification.move(screen.width() - notification.width() - 20,
                        screen.height() - notification.height() - 20)
        
        self.notifications.append(notification)
        notification.show()

    def on_site_status_changed(self, url, status, message):
        # Оновлюємо іконку трею залежно від загального статусу
        any_down = any(not site.last_status for site in monitor.sites.values() if site.is_active)
        if any_down:
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogCancelButton))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogApplyButton))
        
        self.tray_icon.setToolTip(message)
        # Показуємо спливаюче повідомлення
        self.tray_icon.showMessage(
            "Статус сайту змінився",
            message,
            QSystemTrayIcon.MessageIcon.Information,
            3000  # Показувати 3 секунди
        )

    def setup_system_tray(self):
        # Створюємо іконку трею
        self.tray_icon = QSystemTrayIcon(self)
        # Можна замінити на свою іконку
        self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        
        # Створюємо меню для трею
        tray_menu = QMenu()
        
        # Додаємо дії до меню
        show_action = tray_menu.addAction("Показати")
        show_action.triggered.connect(self.show)
        
        quit_action = tray_menu.addAction("Вийти")
        quit_action.triggered.connect(self.quit_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Додаємо обробник кліку по іконці трею
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isHidden():
                self.show()
            else:
                self.hide()

    def closeEvent(self, event):
        if not self.is_minimized_to_tray:
            msg = QMessageBox(self)
            msg.setWindowTitle("SiteWatcher")
            msg.setText("Закриття програми\n\nВиберіть дію:")
            msg.setInformativeText("⚠️ Увага: Якщо програму згорнуто у фоновий режим, закрити її можна\nбуде лише через Диспетчер завдань Windows")
            
            # Створюємо кнопки
            close_button = msg.addButton("Закрити", QMessageBox.ButtonRole.DestructiveRole)
            minimize_button = msg.addButton("Згорнути", QMessageBox.ButtonRole.ActionRole)
            cancel_button = msg.addButton("Скасувати", QMessageBox.ButtonRole.RejectRole)
            
            # Встановлюємо стилі для кнопок
            close_button.setStyleSheet("background-color: #DC2626; color: white; padding: 6px 16px;")
            minimize_button.setStyleSheet("background-color: #D97706; color: white; padding: 6px 16px;")
            cancel_button.setStyleSheet("background-color: #4B5563; color: white; padding: 6px 16px;")
            
            # Встановлюємо стиль для вікна повідомлення
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #1F2937;
                    color: white;
                }
                QLabel {
                    color: white;
                }
                QMessageBox QLabel#qt_msgbox_informativelabel {
                    color: white;
                }
            """)
            
            msg.exec()
            
            if msg.clickedButton() == close_button:
                self.quit_application()
            elif msg.clickedButton() == minimize_button:
                event.ignore()
                self.hide()
                self.is_minimized_to_tray = True
            else:
                event.ignore()
        else:
            event.ignore()
            self.hide()

    def quit_application(self):
        # Зупиняємо монітор
        monitor.stop()
        monitor.join(timeout=1)
        
        # Закриваємо браузер
        self.browser.close()
        
        # Приховуємо іконку трею
        self.tray_icon.hide()
        
        # Зупиняємо Flask сервер
        try:
            requests.get('http://127.0.0.1:5001/shutdown')
        except:
            pass  # Ігноруємо помилки, якщо сервер вже зупинено
        
        # Завершуємо програму
        QApplication.quit()

def run_flask():
    global server_thread
    server_thread = threading.current_thread()
    app.run(debug=False, port=5001, threaded=False)

def create_monitor():
    global monitor
    monitor = MoodleMonitor(check_interval=30)
    monitor.start()

if __name__ == '__main__':
    # Встановлюємо обробник сигналу для коректного завершення
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    create_monitor()
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Чекаємо поки Flask запуститься
    time.sleep(1)
    
    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(qt_app.exec())