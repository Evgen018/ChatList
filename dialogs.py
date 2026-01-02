"""
Диалоговые окна для приложения ChatList.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QLineEdit, QMessageBox, QHeaderView,
    QCheckBox, QWidget, QComboBox, QSpinBox, QFileDialog, QTextEdit,
    QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from utils import (
    format_datetime, truncate_text, export_to_markdown,
    export_to_json, export_to_txt
)


class PromptHistoryDialog(QDialog):
    """Диалог истории промптов."""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.selected_prompt = None
        self.init_ui()
        self.load_prompts()
        
    def init_ui(self):
        """Инициализация интерфейса."""
        self.setWindowTitle("История промптов")
        self.setMinimumSize(800, 500)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Поиск
        search_layout = QHBoxLayout()
        search_label = QLabel("Поиск:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст для поиска...")
        self.search_input.textChanged.connect(self.search_prompts)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Таблица промптов
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Дата", "Промпт", "Теги", "ID"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.on_double_click)
        
        # Настройка колонок
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.select_button = QPushButton("Выбрать")
        self.select_button.clicked.connect(self.select_prompt)
        
        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_prompt)
        
        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.select_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(buttons_layout)
        
    def load_prompts(self, prompts=None):
        """Загрузить промпты в таблицу."""
        if prompts is None:
            prompts = self.db.get_all_prompts()
            
        self.table.setRowCount(len(prompts))
        
        for i, prompt in enumerate(prompts):
            # Дата
            date_item = QTableWidgetItem(format_datetime(prompt['date']))
            self.table.setItem(i, 0, date_item)
            
            # Промпт
            prompt_text = truncate_text(prompt['prompt_text'], 100)
            prompt_item = QTableWidgetItem(prompt_text)
            prompt_item.setToolTip(prompt['prompt_text'])
            self.table.setItem(i, 1, prompt_item)
            
            # Теги
            tags_item = QTableWidgetItem(prompt.get('tags', '') or '')
            self.table.setItem(i, 2, tags_item)
            
            # ID (скрыт)
            id_item = QTableWidgetItem(str(prompt['id']))
            self.table.setItem(i, 3, id_item)
            
        self.table.hideColumn(3)  # Скрываем колонку ID
        
    def search_prompts(self):
        """Поиск промптов."""
        query = self.search_input.text().strip()
        
        if query:
            prompts = self.db.search_prompts(query)
        else:
            prompts = self.db.get_all_prompts()
            
        self.load_prompts(prompts)
        
    def select_prompt(self):
        """Выбрать промпт."""
        selected_row = self.table.currentRow()
        
        if selected_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите промпт!")
            return
            
        prompt_id = int(self.table.item(selected_row, 3).text())
        self.selected_prompt = self.db.get_prompt_by_id(prompt_id)
        self.accept()
        
    def delete_prompt(self):
        """Удалить промпт."""
        selected_row = self.table.currentRow()
        
        if selected_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите промпт для удаления!")
            return
            
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить этот промпт?\n\n"
            "Это также удалит все связанные результаты.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            prompt_id = int(self.table.item(selected_row, 3).text())
            self.db.delete_prompt(prompt_id)
            self.table.removeRow(selected_row)
            QMessageBox.information(self, "Успех", "Промпт удалён!")
            
    def on_double_click(self):
        """Обработка двойного клика."""
        self.select_prompt()
        
    def get_selected_prompt(self):
        """Получить выбранный промпт."""
        return self.selected_prompt


class ModelsManagerDialog(QDialog):
    """Диалог управления моделями."""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.load_models()
        
    def init_ui(self):
        """Инициализация интерфейса."""
        self.setWindowTitle("Управление моделями")
        self.setMinimumSize(900, 500)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Описание
        info_label = QLabel(
            "Настройте модели нейросетей. Активные модели будут использоваться при отправке запросов.\n"
            "API-ключи хранятся в файле .env"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Таблица моделей
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Активна", "Название", "API URL", "Переменная ключа", "ID модели", "Статус"
        ])
        
        # Настройка колонок
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Добавить модель")
        self.add_button.clicked.connect(self.add_model)
        
        self.edit_button = QPushButton("Редактировать")
        self.edit_button.clicked.connect(self.edit_model)
        
        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_model)
        
        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.accept)
        
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(buttons_layout)
        
    def load_models(self):
        """Загрузить модели в таблицу."""
        from models import Model
        import os
        
        models_data = self.db.get_all_models()
        self.table.setRowCount(len(models_data))
        
        for i, model_data in enumerate(models_data):
            model = Model.from_db_row(model_data)
            
            # Чекбокс активности
            checkbox = QCheckBox()
            checkbox.setChecked(model.is_active)
            checkbox.stateChanged.connect(lambda state, m_id=model.id: self.toggle_model(m_id, state))
            
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout()
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_widget.setLayout(checkbox_layout)
            
            self.table.setCellWidget(i, 0, checkbox_widget)
            
            # Название
            self.table.setItem(i, 1, QTableWidgetItem(model.name))
            
            # API URL
            self.table.setItem(i, 2, QTableWidgetItem(model.api_url))
            
            # Переменная ключа
            self.table.setItem(i, 3, QTableWidgetItem(model.api_key_env))
            
            # ID модели
            self.table.setItem(i, 4, QTableWidgetItem(model.model_id))
            
            # Статус (настроен ли API-ключ)
            api_key = os.getenv(model.api_key_env)
            status = "✅ Настроен" if api_key else "⚠️ Ключ не найден"
            status_item = QTableWidgetItem(status)
            self.table.setItem(i, 5, status_item)
            
            # Скрытая колонка с ID
            id_item = QTableWidgetItem(str(model.id))
            self.table.setItem(i, 6, id_item) if self.table.columnCount() > 6 else None
            
    def toggle_model(self, model_id, state):
        """Переключить активность модели."""
        is_active = (state == Qt.Checked)
        self.db.update_model_status(model_id, is_active)
        
    def add_model(self):
        """Добавить новую модель."""
        dialog = ModelEditDialog(self.db, None, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_models()
            
    def edit_model(self):
        """Редактировать модель."""
        selected_row = self.table.currentRow()
        
        if selected_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите модель для редактирования!")
            return
            
        # TODO: Реализовать редактирование
        QMessageBox.information(self, "Информация", "Функция редактирования в разработке")
        
    def delete_model(self):
        """Удалить модель."""
        selected_row = self.table.currentRow()
        
        if selected_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите модель для удаления!")
            return
            
        model_name = self.table.item(selected_row, 1).text()
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить модель '{model_name}'?\n\n"
            "Это также удалит все связанные результаты.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Получаем ID модели (нужно добавить скрытую колонку)
            # Временное решение: ищем по имени
            models = self.db.get_all_models()
            model_id = next((m['id'] for m in models if m['name'] == model_name), None)
            
            if model_id:
                self.db.delete_model(model_id)
                self.load_models()
                QMessageBox.information(self, "Успех", "Модель удалена!")


class ModelEditDialog(QDialog):
    """Диалог добавления/редактирования модели."""
    
    def __init__(self, db, model=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.model = model
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса."""
        self.setWindowTitle("Добавить модель" if not self.model else "Редактировать модель")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Поля ввода
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Например: GPT-4 Turbo")
        
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("https://api.openai.com/v1/chat/completions")
        
        self.api_key_env_input = QLineEdit()
        self.api_key_env_input.setPlaceholderText("OPENAI_API_KEY")
        
        self.model_id_input = QLineEdit()
        self.model_id_input.setPlaceholderText("gpt-4-turbo-preview")
        
        # Добавляем поля в layout
        layout.addWidget(QLabel("Название:"))
        layout.addWidget(self.name_input)
        
        layout.addWidget(QLabel("API URL:"))
        layout.addWidget(self.api_url_input)
        
        layout.addWidget(QLabel("Переменная API-ключа (.env):"))
        layout.addWidget(self.api_key_env_input)
        
        layout.addWidget(QLabel("ID модели:"))
        layout.addWidget(self.model_id_input)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_model)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def save_model(self):
        """Сохранить модель."""
        name = self.name_input.text().strip()
        api_url = self.api_url_input.text().strip()
        api_key_env = self.api_key_env_input.text().strip()
        model_id = self.model_id_input.text().strip()
        
        if not all([name, api_url, api_key_env, model_id]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return
            
        try:
            self.db.add_model(name, api_url, api_key_env, model_id)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")


class SettingsDialog(QDialog):
    """Диалог настроек."""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """Инициализация интерфейса."""
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Таймаут
        layout.addWidget(QLabel("Таймаут запросов (сек):"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 120)
        self.timeout_spin.setValue(30)
        layout.addWidget(self.timeout_spin)
        
        # Повторы
        layout.addWidget(QLabel("Максимум повторных попыток:"))
        self.retries_spin = QSpinBox()
        self.retries_spin.setRange(0, 10)
        self.retries_spin.setValue(3)
        layout.addWidget(self.retries_spin)
        
        # Тема
        layout.addWidget(QLabel("Тема:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        layout.addWidget(self.theme_combo)
        
        # Формат экспорта
        layout.addWidget(QLabel("Формат экспорта по умолчанию:"))
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["markdown", "json", "txt"])
        layout.addWidget(self.export_format_combo)
        
        layout.addStretch()
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def load_settings(self):
        """Загрузить настройки."""
        settings = self.db.get_all_settings()
        
        self.timeout_spin.setValue(int(settings.get('timeout', 30)))
        self.retries_spin.setValue(int(settings.get('max_retries', 3)))
        
        theme = settings.get('theme', 'light')
        self.theme_combo.setCurrentText(theme)
        
        export_format = settings.get('export_format', 'markdown')
        self.export_format_combo.setCurrentText(export_format)
        
    def save_settings(self):
        """Сохранить настройки."""
        self.db.set_setting('timeout', str(self.timeout_spin.value()))
        self.db.set_setting('max_retries', str(self.retries_spin.value()))
        self.db.set_setting('theme', self.theme_combo.currentText())
        self.db.set_setting('export_format', self.export_format_combo.currentText())
        
        QMessageBox.information(self, "Успех", "Настройки сохранены!\n\nПерезапустите программу для применения изменений.")
        self.accept()


class ExportDialog(QDialog):
    """Диалог экспорта результатов."""
    
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.results = results
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса."""
        self.setWindowTitle("Экспорт результатов")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        layout.addWidget(QLabel("Выберите формат экспорта:"))
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Markdown (.md)", "JSON (.json)", "Текст (.txt)"])
        layout.addWidget(self.format_combo)
        
        layout.addWidget(QLabel(f"Будет экспортировано результатов: {len(self.results)}"))
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        export_button = QPushButton("Экспортировать")
        export_button.clicked.connect(self.export)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(export_button)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)
        
    def export(self):
        """Выполнить экспорт."""
        format_index = self.format_combo.currentIndex()
        
        if format_index == 0:  # Markdown
            filename, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как", "", "Markdown Files (*.md)"
            )
            if filename:
                results_dict = [self._result_to_dict(r) for r in self.results]
                if export_to_markdown(results_dict, filename):
                    QMessageBox.information(self, "Успех", "Результаты экспортированы!")
                    self.accept()
                    
        elif format_index == 1:  # JSON
            filename, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как", "", "JSON Files (*.json)"
            )
            if filename:
                results_dict = [self._result_to_dict(r) for r in self.results]
                if export_to_json(results_dict, filename):
                    QMessageBox.information(self, "Успех", "Результаты экспортированы!")
                    self.accept()
                    
        elif format_index == 2:  # TXT
            filename, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как", "", "Text Files (*.txt)"
            )
            if filename:
                results_dict = [self._result_to_dict(r) for r in self.results]
                if export_to_txt(results_dict, filename):
                    QMessageBox.information(self, "Успех", "Результаты экспортированы!")
                    self.accept()
                    
    def _result_to_dict(self, result):
        """Преобразовать Result в dict."""
        return {
            'model_name': result.model_name,
            'response_text': result.response_text,
            'response_time': result.response_time,
            'tokens_used': result.tokens_used,
            'error': result.error
        }

