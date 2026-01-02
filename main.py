"""
Главный файл приложения ChatList.
Графический интерфейс на PyQt5.
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QLabel,
    QLineEdit, QMessageBox, QProgressDialog, QHeaderView, QCheckBox,
    QDialog, QDialogButtonBox, QSplitter, QMenuBar, QMenu, QAction,
    QFileDialog, QStatusBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

from db import Database
from models import Model, PromptRequest, Result
from config import APP_NAME, VERSION, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
from utils import truncate_text, format_response_time, format_tokens

# Импорт диалоговых окон
from dialogs import PromptHistoryDialog, ModelsManagerDialog, SettingsDialog


class SendRequestThread(QThread):
    """Поток для отправки запросов к API (чтобы не блокировать GUI)."""
    
    progress = pyqtSignal(str, Result)  # Сигнал для обновления прогресса
    finished = pyqtSignal(list)  # Сигнал завершения
    
    def __init__(self, prompt, models):
        super().__init__()
        self.prompt = prompt
        self.models = models
        
    def run(self):
        """Выполнить отправку запросов."""
        request = PromptRequest(self.prompt, self.models)
        results = request.send_to_models(progress_callback=self._on_progress)
        self.finished.emit(results)
        
    def _on_progress(self, model_name, result):
        """Callback для обновления прогресса."""
        self.progress.emit(model_name, result)


class MainWindow(QMainWindow):
    """Главное окно приложения ChatList."""
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.db.init_schema()
        
        self.current_prompt_id = None
        self.current_results = []
        self.request_thread = None
        
        self.init_ui()
        self.load_window_settings()
        
    def init_ui(self):
        """Инициализация интерфейса."""
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # Создаём меню
        self.create_menu()
        
        # Создаём статус бар
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готов к работе")
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Верхняя панель: ввод промпта
        prompt_group = self.create_prompt_input()
        main_layout.addWidget(prompt_group)
        
        # Центральная панель: таблица результатов
        self.results_table = self.create_results_table()
        main_layout.addWidget(self.results_table, stretch=1)
        
        # Нижняя панель: кнопки действий
        actions_layout = self.create_actions_panel()
        main_layout.addLayout(actions_layout)
        
    def create_menu(self):
        """Создать меню приложения."""
        menubar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menubar.addMenu("Файл")
        
        export_action = QAction("Экспорт результатов...", self)
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню "Управление"
        manage_menu = menubar.addMenu("Управление")
        
        history_action = QAction("История промптов...", self)
        history_action.triggered.connect(self.show_history)
        manage_menu.addAction(history_action)
        
        models_action = QAction("Управление моделями...", self)
        models_action.triggered.connect(self.show_models_manager)
        manage_menu.addAction(models_action)
        
        settings_action = QAction("Настройки...", self)
        settings_action.triggered.connect(self.show_settings)
        manage_menu.addAction(settings_action)
        
        # Меню "Справка"
        help_menu = menubar.addMenu("Справка")
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_prompt_input(self):
        """Создать панель ввода промпта."""
        group = QWidget()
        layout = QVBoxLayout()
        group.setLayout(layout)
        
        # Заголовок
        label = QLabel("Введите промпт:")
        label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(label)
        
        # Поле ввода промпта
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Напишите ваш вопрос или запрос здесь...")
        self.prompt_input.setMaximumHeight(120)
        layout.addWidget(self.prompt_input)
        
        # Поле для тегов
        tags_layout = QHBoxLayout()
        tags_label = QLabel("Теги:")
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("python, api, openai (необязательно)")
        tags_layout.addWidget(tags_label)
        tags_layout.addWidget(self.tags_input)
        layout.addLayout(tags_layout)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.send_button = QPushButton("Отправить")
        self.send_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.send_button.clicked.connect(self.send_request)
        
        self.history_button = QPushButton("История")
        self.history_button.clicked.connect(self.show_history)
        
        self.clear_button = QPushButton("Очистить")
        self.clear_button.clicked.connect(self.clear_prompt)
        
        buttons_layout.addWidget(self.send_button)
        buttons_layout.addWidget(self.history_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        return group
        
    def create_results_table(self):
        """Создать таблицу результатов."""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "Выбрано", "Модель", "Ответ", "Время", "Токены"
        ])
        
        # Настройка размеров колонок
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        # Включаем сортировку
        table.setSortingEnabled(True)
        
        # Разрешаем выделение текста
        table.setSelectionBehavior(QTableWidget.SelectItems)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        return table
        
    def create_actions_panel(self):
        """Создать панель с кнопками действий."""
        layout = QHBoxLayout()
        
        self.save_button = QPushButton("Сохранить выбранные")
        self.save_button.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        self.save_button.clicked.connect(self.save_selected_results)
        self.save_button.setEnabled(False)
        
        self.clear_results_button = QPushButton("Очистить результаты")
        self.clear_results_button.clicked.connect(self.clear_results)
        self.clear_results_button.setEnabled(False)
        
        self.export_button = QPushButton("Экспорт...")
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        
        layout.addWidget(self.save_button)
        layout.addWidget(self.clear_results_button)
        layout.addWidget(self.export_button)
        layout.addStretch()
        
        return layout
        
    def send_request(self):
        """Отправить запрос в модели."""
        prompt = self.prompt_input.toPlainText().strip()
        
        if not prompt:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите промпт!")
            return
            
        # Получаем активные модели
        models_data = self.db.get_active_models()
        
        if not models_data:
            QMessageBox.warning(
                self, 
                "Ошибка", 
                "Нет активных моделей!\n\nПерейдите в Управление → Управление моделями и активируйте нужные модели."
            )
            return
            
        models = [Model.from_db_row(m) for m in models_data]
        
        # Проверяем, настроены ли API-ключи
        configured_models = [m for m in models if m.is_configured()]
        
        if not configured_models:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Не найдены API-ключи для активных моделей!\n\n"
                "Создайте файл .env и добавьте необходимые API-ключи."
            )
            return
            
        # Сохраняем промпт в БД
        tags = self.tags_input.text().strip()
        self.current_prompt_id = self.db.add_prompt(prompt, tags if tags else None)
        
        # Очищаем предыдущие результаты
        self.clear_results()
        
        # Отключаем кнопку отправки
        self.send_button.setEnabled(False)
        self.send_button.setText("Отправка...")
        self.statusBar.showMessage(f"Отправка запроса в {len(configured_models)} модел(и/ей)...")
        
        # Создаём и запускаем поток
        self.request_thread = SendRequestThread(prompt, configured_models)
        self.request_thread.progress.connect(self.on_request_progress)
        self.request_thread.finished.connect(self.on_request_finished)
        self.request_thread.start()
        
    def on_request_progress(self, model_name, result):
        """Обработка прогресса отправки."""
        self.statusBar.showMessage(f"Получен ответ от {model_name}...")
        
    def on_request_finished(self, results):
        """Обработка завершения отправки."""
        self.current_results = results
        self.display_results(results)
        
        # Включаем кнопки
        self.send_button.setEnabled(True)
        self.send_button.setText("Отправить")
        self.save_button.setEnabled(True)
        self.clear_results_button.setEnabled(True)
        self.export_button.setEnabled(True)
        
        # Подсчёт успешных ответов
        successful = len([r for r in results if r.is_success()])
        self.statusBar.showMessage(f"Получено {successful} из {len(results)} ответов")
        
    def display_results(self, results):
        """Отобразить результаты в таблице."""
        self.results_table.setRowCount(len(results))
        
        for i, result in enumerate(results):
            # Чекбокс
            checkbox = QCheckBox()
            if result.is_success():
                checkbox.setChecked(True)
            else:
                checkbox.setEnabled(False)
            checkbox.stateChanged.connect(lambda state, idx=i: self.on_checkbox_changed(idx, state))
            
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout()
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_widget.setLayout(checkbox_layout)
            
            self.results_table.setCellWidget(i, 0, checkbox_widget)
            
            # Название модели
            model_item = QTableWidgetItem(result.model_name)
            self.results_table.setItem(i, 1, model_item)
            
            # Ответ
            if result.is_success():
                response_text = truncate_text(result.response_text, 200)
            else:
                response_text = f"❌ {result.error}"
                
            response_item = QTableWidgetItem(response_text)
            response_item.setToolTip(result.response_text if result.is_success() else result.error)
            self.results_table.setItem(i, 2, response_item)
            
            # Время ответа
            time_item = QTableWidgetItem(format_response_time(result.response_time))
            time_item.setTextAlignment(Qt.AlignCenter)
            self.results_table.setItem(i, 3, time_item)
            
            # Токены
            tokens_item = QTableWidgetItem(format_tokens(result.tokens_used))
            tokens_item.setTextAlignment(Qt.AlignCenter)
            self.results_table.setItem(i, 4, tokens_item)
            
        # Автоподгон высоты строк
        self.results_table.resizeRowsToContents()
        
    def on_checkbox_changed(self, row_index, state):
        """Обработка изменения чекбокса."""
        if row_index < len(self.current_results):
            self.current_results[row_index].selected = (state == Qt.Checked)
            
    def save_selected_results(self):
        """Сохранить выбранные результаты в БД."""
        if not self.current_prompt_id:
            QMessageBox.warning(self, "Ошибка", "Нет активного промпта!")
            return
            
        selected_results = [r for r in self.current_results if r.selected and r.is_success()]
        
        if not selected_results:
            QMessageBox.information(self, "Информация", "Не выбрано ни одного результата!")
            return
            
        try:
            for result in selected_results:
                self.db.save_result(
                    self.current_prompt_id,
                    result.model_id,
                    result.response_text,
                    result.response_time,
                    result.tokens_used
                )
                
            QMessageBox.information(
                self,
                "Успех",
                f"Сохранено результатов: {len(selected_results)}"
            )
            
            self.statusBar.showMessage(f"Сохранено {len(selected_results)} результат(ов)")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")
            
    def clear_results(self):
        """Очистить таблицу результатов."""
        self.results_table.setRowCount(0)
        self.current_results = []
        self.save_button.setEnabled(False)
        self.clear_results_button.setEnabled(False)
        self.export_button.setEnabled(False)
        
    def clear_prompt(self):
        """Очистить поле ввода промпта."""
        self.prompt_input.clear()
        self.tags_input.clear()
        
    def export_results(self):
        """Экспорт результатов."""
        if not self.current_results:
            QMessageBox.information(self, "Информация", "Нет результатов для экспорта!")
            return
            
        from dialogs import ExportDialog
        dialog = ExportDialog(self.current_results, self)
        dialog.exec_()
        
    def show_history(self):
        """Показать окно истории промптов."""
        dialog = PromptHistoryDialog(self.db, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_prompt = dialog.get_selected_prompt()
            if selected_prompt:
                self.prompt_input.setPlainText(selected_prompt['prompt_text'])
                self.tags_input.setText(selected_prompt.get('tags', '') or '')
                
    def show_models_manager(self):
        """Показать окно управления моделями."""
        dialog = ModelsManagerDialog(self.db, self)
        dialog.exec_()
        
    def show_settings(self):
        """Показать окно настроек."""
        dialog = SettingsDialog(self.db, self)
        dialog.exec_()
        
    def show_about(self):
        """Показать окно О программе."""
        QMessageBox.about(
            self,
            "О программе",
            f"<h2>{APP_NAME}</h2>"
            f"<p>Версия: {VERSION}</p>"
            f"<p>Программа для отправки промптов в несколько нейросетей и сравнения их ответов.</p>"
            f"<p><b>Технологии:</b> Python, PyQt5, SQLite</p>"
            f"<p><b>Поддерживаемые модели:</b> GPT-4, DeepSeek, Groq, Claude и др.</p>"
        )
        
    def load_window_settings(self):
        """Загрузить сохранённые настройки окна."""
        # TODO: Загрузка размера и позиции окна из БД
        pass
        
    def save_window_settings(self):
        """Сохранить настройки окна."""
        # TODO: Сохранение размера и позиции окна в БД
        pass
        
    def closeEvent(self, event):
        """Обработка закрытия окна."""
        self.save_window_settings()
        self.db.close()
        event.accept()


def main():
    """Главная функция запуска приложения."""
    app = QApplication(sys.argv)
    
    # Устанавливаем стиль приложения
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
