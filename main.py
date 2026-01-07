"""
ChatList — приложение для сравнения ответов нейросетей.
"""

import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QComboBox,
    QMessageBox,
    QProgressBar,
    QSplitter,
    QFrame,
    QSpinBox,
    QFileDialog,
    QDialog,
    QTextBrowser,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont


class MarkdownViewerDialog(QDialog):
    """Диалог для просмотра ответа в формате Markdown."""

    def __init__(self, title: str, content: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Ответ: {title}")
        self.setMinimumSize(800, 600)
        self.setup_ui(content)

    def setup_ui(self, content: str):
        layout = QVBoxLayout(self)

        # Текстовый браузер с поддержкой Markdown
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setMarkdown(content)
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.text_browser)

        # Кнопки
        buttons_layout = QHBoxLayout()

        copy_btn = QPushButton("📋 Копировать")
        copy_btn.clicked.connect(lambda: self.copy_to_clipboard(content))
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        buttons_layout.addWidget(copy_btn)

        buttons_layout.addStretch()

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)

    def copy_to_clipboard(self, content: str):
        """Копировать содержимое в буфер обмена."""
        clipboard = QApplication.clipboard()
        clipboard.setText(content)
        QMessageBox.information(self, "Готово", "Текст скопирован в буфер обмена")

from db import Database
from models import ModelManager, ResultsStore
from network import send_to_models_sync
from logger import (
    log_request,
    log_response,
    log_save_results,
    log_export,
    log_error,
    log_app_start,
    log_app_close,
)


class RequestWorker(QThread):
    """Поток для отправки запросов к API."""

    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, prompt: str, models: list, timeout: int = 60):
        super().__init__()
        self.prompt = prompt
        self.models = models
        self.timeout = timeout

    def run(self):
        try:
            results = send_to_models_sync(self.prompt, self.models, self.timeout)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class RequestTab(QWidget):
    """Вкладка «Запрос»."""

    request_sent = pyqtSignal(str, list)  # prompt, models

    def __init__(self, db: Database, model_manager: ModelManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.model_manager = model_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Заголовок и CRUD кнопки
        header_layout = QHBoxLayout()
        title = QLabel("Введите промпт")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # CRUD кнопки для промптов
        self.view_prompt_btn = QPushButton("📖 Просмотр")
        self.view_prompt_btn.clicked.connect(self.view_prompt)
        self.view_prompt_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        header_layout.addWidget(self.view_prompt_btn)

        self.edit_prompt_btn = QPushButton("✏️ Изменить")
        self.edit_prompt_btn.clicked.connect(self.edit_prompt)
        self.edit_prompt_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        header_layout.addWidget(self.edit_prompt_btn)

        self.delete_prompt_btn = QPushButton("🗑️ Удалить")
        self.delete_prompt_btn.clicked.connect(self.delete_prompt)
        self.delete_prompt_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        header_layout.addWidget(self.delete_prompt_btn)

        layout.addLayout(header_layout)

        # Выбор сохранённого промпта
        saved_layout = QHBoxLayout()
        saved_label = QLabel("Сохранённые промпты:")
        self.prompts_combo = QComboBox()
        self.prompts_combo.setMinimumWidth(300)
        self.prompts_combo.currentIndexChanged.connect(self.on_prompt_selected)
        self.refresh_prompts_btn = QPushButton("⟳")
        self.refresh_prompts_btn.setFixedWidth(30)
        self.refresh_prompts_btn.clicked.connect(self.load_saved_prompts)
        saved_layout.addWidget(saved_label)
        saved_layout.addWidget(self.prompts_combo, 1)
        saved_layout.addWidget(self.refresh_prompts_btn)
        layout.addLayout(saved_layout)

        # Текстовое поле для промпта
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Введите ваш запрос здесь...")
        self.prompt_edit.setMinimumHeight(150)
        self.prompt_edit.setStyleSheet("""
            QTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #3498db;
            }
        """)
        layout.addWidget(self.prompt_edit)

        # Теги
        tags_layout = QHBoxLayout()
        tags_label = QLabel("Теги:")
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("теги через запятую")
        tags_layout.addWidget(tags_label)
        tags_layout.addWidget(self.tags_edit, 1)
        layout.addLayout(tags_layout)

        # Кнопки
        buttons_layout = QHBoxLayout()

        self.save_prompt_btn = QPushButton("💾 Сохранить промпт")
        self.save_prompt_btn.clicked.connect(self.save_prompt)
        self.save_prompt_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        buttons_layout.addWidget(self.save_prompt_btn)

        buttons_layout.addStretch()

        self.send_btn = QPushButton("🚀 Отправить")
        self.send_btn.clicked.connect(self.send_request)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        buttons_layout.addWidget(self.send_btn)

        layout.addLayout(buttons_layout)

        # Прогресс
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 5px;
                background-color: #ecf0f1;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Загрузка сохранённых промптов
        self.load_saved_prompts()

    def load_saved_prompts(self):
        """Загрузить список сохранённых промптов."""
        self.prompts_combo.clear()
        self.prompts_combo.addItem("— Выберите промпт —", None)
        prompts = self.db.get_prompts(limit=50)
        for prompt in prompts:
            text = prompt["text"][:50] + "..." if len(prompt["text"]) > 50 else prompt["text"]
            self.prompts_combo.addItem(text, prompt["id"])

    def on_prompt_selected(self, index):
        """Обработка выбора промпта из списка."""
        prompt_id = self.prompts_combo.currentData()
        if prompt_id:
            prompt = self.db.get_prompt_by_id(prompt_id)
            if prompt:
                self.prompt_edit.setText(prompt["text"])
                self.tags_edit.setText(prompt["tags"])

    def save_prompt(self):
        """Сохранить промпт в базу данных."""
        text = self.prompt_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Ошибка", "Введите текст промпта")
            return

        tags = self.tags_edit.text().strip()
        self.db.add_prompt(text, tags)
        self.load_saved_prompts()
        self.status_label.setText("Промпт сохранён")

    def view_prompt(self):
        """Просмотр выбранного промпта."""
        prompt_id = self.prompts_combo.currentData()
        if not prompt_id:
            QMessageBox.warning(self, "Ошибка", "Выберите промпт")
            return
        prompt = self.db.get_prompt_by_id(prompt_id)
        if prompt:
            dialog = MarkdownViewerDialog("Промпт", prompt["text"], self)
            dialog.exec_()

    def edit_prompt(self):
        """Редактировать выбранный промпт."""
        prompt_id = self.prompts_combo.currentData()
        if not prompt_id:
            QMessageBox.warning(self, "Ошибка", "Выберите промпт")
            return
        prompt = self.db.get_prompt_by_id(prompt_id)
        if prompt:
            # Загрузить в редактор
            self.prompt_edit.setText(prompt["text"])
            self.tags_edit.setText(prompt["tags"])
            # Удалить старый и сохранить как новый при нажатии "Сохранить"
            self.status_label.setText("Редактирование промпта. Измените и нажмите 'Сохранить'")

    def delete_prompt(self):
        """Удалить выбранный промпт."""
        prompt_id = self.prompts_combo.currentData()
        if not prompt_id:
            QMessageBox.warning(self, "Ошибка", "Выберите промпт")
            return
        reply = QMessageBox.question(
            self, "Подтверждение", "Удалить выбранный промпт?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_prompt(prompt_id)
            self.load_saved_prompts()
            self.prompt_edit.clear()
            self.tags_edit.clear()
            self.status_label.setText("Промпт удалён")

    def send_request(self):
        """Отправить запрос во все активные модели."""
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Ошибка", "Введите текст промпта")
            return

        models = self.model_manager.get_active_models()
        if not models:
            QMessageBox.warning(
                self, "Ошибка", "Нет активных моделей. Добавьте модели на вкладке «Модели»."
            )
            return

        self.request_sent.emit(prompt, models)


class ResultsTab(QWidget):
    """Вкладка «Результаты»."""

    def __init__(self, db: Database, results_store: ResultsStore, parent=None):
        super().__init__(parent)
        self.db = db
        self.results_store = results_store
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Заголовок и CRUD кнопки
        header_layout = QHBoxLayout()
        title = QLabel("Результаты запроса")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # CRUD кнопки
        self.view_result_btn = QPushButton("📖 Просмотр")
        self.view_result_btn.clicked.connect(self.view_selected_result)
        self.view_result_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        header_layout.addWidget(self.view_result_btn)

        self.delete_result_btn = QPushButton("🗑️ Удалить")
        self.delete_result_btn.clicked.connect(self.delete_selected_result)
        self.delete_result_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        header_layout.addWidget(self.delete_result_btn)

        layout.addLayout(header_layout)

        # Кнопки выбора
        select_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("☑ Выбрать все")
        self.select_all_btn.clicked.connect(self.select_all)
        select_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("☐ Снять все")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        select_layout.addWidget(self.deselect_all_btn)
        
        select_layout.addStretch()
        layout.addLayout(select_layout)

        # Текущий промпт
        self.prompt_label = QLabel("")
        self.prompt_label.setWordWrap(True)
        self.prompt_label.setStyleSheet("""
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            color: #495057;
        """)
        layout.addWidget(self.prompt_label)

        # Таблица результатов
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["", "Модель", "Ответ", "Токены"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.results_table.setColumnWidth(0, 30)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSortingEnabled(True)
        self.results_table.setWordWrap(True)  # Перенос текста
        self.results_table.verticalHeader().setDefaultSectionSize(120)  # Высота строк
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.doubleClicked.connect(self.view_selected_result)
        self.results_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 10px;
            }
        """)
        layout.addWidget(self.results_table)

        # Кнопки
        buttons_layout = QHBoxLayout()

        self.save_btn = QPushButton("💾 Сохранить выбранные")
        self.save_btn.clicked.connect(self.save_selected)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        buttons_layout.addWidget(self.save_btn)

        buttons_layout.addStretch()

        self.clear_btn = QPushButton("🗑 Очистить")
        self.clear_btn.clicked.connect(self.clear_results)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        buttons_layout.addWidget(self.clear_btn)

        layout.addLayout(buttons_layout)

    def update_results(self):
        """Обновить таблицу результатов."""
        self.results_table.setRowCount(0)

        prompt = self.results_store.current_prompt
        if prompt:
            display_prompt = prompt[:200] + "..." if len(prompt) > 200 else prompt
            self.prompt_label.setText(f"Промпт: {display_prompt}")
        else:
            self.prompt_label.setText("")

        for i, result in enumerate(self.results_store.results):
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)

            # Чекбокс
            checkbox = QCheckBox()
            checkbox.setChecked(result.selected)
            checkbox.stateChanged.connect(lambda state, idx=i: self.toggle_selection(idx))
            self.results_table.setCellWidget(row, 0, checkbox)

            # Модель
            model_item = QTableWidgetItem(result.model_name)
            if not result.success:
                model_item.setForeground(Qt.red)
            self.results_table.setItem(row, 1, model_item)

            # Ответ (показываем больше текста)
            response_text = result.response[:1000] + "..." if len(result.response) > 1000 else result.response
            response_item = QTableWidgetItem(response_text)
            response_item.setToolTip(result.response)
            response_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.results_table.setItem(row, 2, response_item)

            # Токены
            tokens_item = QTableWidgetItem(str(result.tokens))
            self.results_table.setItem(row, 3, tokens_item)

        self.results_table.resizeRowsToContents()

    def toggle_selection(self, index: int):
        """Переключить выбор результата."""
        self.results_store.toggle_selection(index)

    def select_all(self):
        """Выбрать все результаты."""
        self.results_store.select_all()
        self.update_results()

    def deselect_all(self):
        """Снять выбор со всех."""
        self.results_store.deselect_all()
        self.update_results()

    def save_selected(self):
        """Сохранить выбранные результаты."""
        selected = self.results_store.get_selected()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Не выбрано ни одного результата")
            return

        results_to_save = [
            {
                "prompt_text": r.prompt_text,
                "model_name": r.model_name,
                "model_id": r.model_id,
                "response": r.response,
                "tokens": r.tokens,
            }
            for r in selected
        ]

        self.db.save_results(results_to_save)
        log_save_results(len(results_to_save))
        QMessageBox.information(
            self, "Успех", f"Сохранено {len(results_to_save)} результатов"
        )

    def clear_results(self):
        """Очистить результаты."""
        self.results_store.clear()
        self.update_results()

    def get_selected_row(self) -> int:
        """Получить индекс выбранной строки."""
        selected = self.results_table.selectedItems()
        if not selected:
            return -1
        return selected[0].row()

    def view_selected_result(self):
        """Просмотр выбранного результата."""
        row = self.get_selected_row()
        if row < 0 or row >= len(self.results_store.results):
            QMessageBox.warning(self, "Ошибка", "Выберите результат")
            return
        result = self.results_store.results[row]
        dialog = MarkdownViewerDialog(result.model_name, result.response, self)
        dialog.exec_()

    def delete_selected_result(self):
        """Удалить выбранный результат из временного хранилища."""
        row = self.get_selected_row()
        if row < 0 or row >= len(self.results_store.results):
            QMessageBox.warning(self, "Ошибка", "Выберите результат")
            return
        reply = QMessageBox.question(
            self, "Подтверждение", "Удалить выбранный результат?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            del self.results_store._results[row]
            self.update_results()


class ModelsTab(QWidget):
    """Вкладка «Модели»."""

    def __init__(self, model_manager: ModelManager, parent=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self.setup_ui()
        self.load_models()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Заголовок и CRUD кнопки
        header_layout = QHBoxLayout()
        title = QLabel("Управление моделями")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.view_model_btn = QPushButton("📖 Просмотр")
        self.view_model_btn.clicked.connect(self.view_model)
        self.view_model_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        header_layout.addWidget(self.view_model_btn)

        self.edit_model_btn = QPushButton("✏️ Изменить")
        self.edit_model_btn.clicked.connect(self.edit_model)
        self.edit_model_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        header_layout.addWidget(self.edit_model_btn)

        self.delete_model_btn = QPushButton("🗑️ Удалить")
        self.delete_model_btn.clicked.connect(self.delete_selected_model)
        self.delete_model_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        header_layout.addWidget(self.delete_model_btn)

        layout.addLayout(header_layout)

        # Таблица моделей
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(6)
        self.models_table.setHorizontalHeaderLabels(
            ["Активна", "Название", "Провайдер", "URL", "API-ключ", "Model ID"]
        )
        self.models_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.models_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.models_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.models_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.models_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.models_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.models_table.setColumnWidth(0, 60)
        self.models_table.setAlternatingRowColors(True)
        self.models_table.setSortingEnabled(True)
        self.models_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.models_table)
        
        # Кэш моделей для доступа по индексу
        self.models_cache = []

        # Форма добавления
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)

        form_title = QLabel("Добавить модель")
        form_title.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(form_title)

        row1 = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Название")
        row1.addWidget(self.name_edit)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["openai", "anthropic", "google", "openrouter"])
        row1.addWidget(self.provider_combo)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("API URL")
        row2.addWidget(self.url_edit)
        form_layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Имя переменной окружения (напр. OPENAI_API_KEY)")
        row3.addWidget(self.api_key_edit)

        self.model_id_edit = QLineEdit()
        self.model_id_edit.setPlaceholderText("Model ID")
        row3.addWidget(self.model_id_edit)
        form_layout.addLayout(row3)

        add_btn = QPushButton("➕ Добавить")
        add_btn.clicked.connect(self.add_model)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        form_layout.addWidget(add_btn)

        layout.addWidget(form_frame)

        # Кнопка добавления моделей по умолчанию
        default_btn = QPushButton("📋 Добавить модели по умолчанию")
        default_btn.clicked.connect(self.add_default_models)
        default_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        layout.addWidget(default_btn)

    def load_models(self):
        """Загрузить список моделей."""
        self.models_table.setRowCount(0)
        self.models_cache = self.model_manager.get_all_models()

        for model in self.models_cache:
            row = self.models_table.rowCount()
            self.models_table.insertRow(row)

            # Чекбокс активности
            checkbox = QCheckBox()
            checkbox.setChecked(bool(model["is_active"]))
            checkbox.stateChanged.connect(
                lambda state, mid=model["id"]: self.toggle_model(mid)
            )
            self.models_table.setCellWidget(row, 0, checkbox)

            # Данные
            self.models_table.setItem(row, 1, QTableWidgetItem(model["name"]))
            self.models_table.setItem(row, 2, QTableWidgetItem(model["provider"]))
            self.models_table.setItem(row, 3, QTableWidgetItem(model["api_url"]))
            self.models_table.setItem(row, 4, QTableWidgetItem(model["api_key_env"]))
            self.models_table.setItem(row, 5, QTableWidgetItem(model["model_id"]))

    def add_model(self):
        """Добавить новую модель."""
        name = self.name_edit.text().strip()
        provider = self.provider_combo.currentText()
        url = self.url_edit.text().strip()
        api_key_env = self.api_key_edit.text().strip()
        model_id = self.model_id_edit.text().strip()

        if not all([name, url, api_key_env, model_id]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        self.model_manager.add_model(
            name=name,
            provider=provider,
            api_url=url,
            api_key_env=api_key_env,
            model_id=model_id,
        )

        # Очистка формы
        self.name_edit.clear()
        self.url_edit.clear()
        self.api_key_edit.clear()
        self.model_id_edit.clear()

        self.load_models()

    def toggle_model(self, model_id: int):
        """Переключить активность модели."""
        self.model_manager.toggle_model(model_id)

    def delete_model(self, model_id: int):
        """Удалить модель."""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить модель?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.model_manager.delete_model(model_id)
            self.load_models()

    def get_selected_model(self) -> dict:
        """Получить выбранную модель."""
        selected = self.models_table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        if row < len(self.models_cache):
            return self.models_cache[row]
        return None

    def view_model(self):
        """Просмотр выбранной модели."""
        model = self.get_selected_model()
        if not model:
            QMessageBox.warning(self, "Ошибка", "Выберите модель")
            return
        info = f"""**Название:** {model['name']}

**Провайдер:** {model['provider']}

**API URL:** {model['api_url']}

**API ключ:** {model['api_key_env']}

**Model ID:** {model['model_id']}

**Активна:** {'Да' if model['is_active'] else 'Нет'}
"""
        dialog = MarkdownViewerDialog(model['name'], info, self)
        dialog.exec_()

    def edit_model(self):
        """Редактировать выбранную модель."""
        model = self.get_selected_model()
        if not model:
            QMessageBox.warning(self, "Ошибка", "Выберите модель")
            return
        # Заполнить форму
        self.name_edit.setText(model['name'])
        self.provider_combo.setCurrentText(model['provider'])
        self.url_edit.setText(model['api_url'])
        self.api_key_edit.setText(model['api_key_env'])
        self.model_id_edit.setText(model['model_id'])
        # Удалить старую модель
        self.model_manager.delete_model(model['id'])
        self.load_models()
        QMessageBox.information(self, "Редактирование", "Измените данные и нажмите 'Добавить'")

    def delete_selected_model(self):
        """Удалить выбранную модель."""
        model = self.get_selected_model()
        if not model:
            QMessageBox.warning(self, "Ошибка", "Выберите модель")
            return
        self.delete_model(model['id'])

    def add_default_models(self):
        """Добавить модели по умолчанию."""
        self.model_manager.add_default_models()
        self.load_models()
        QMessageBox.information(self, "Готово", "Модели по умолчанию добавлены")


class EditResultDialog(QDialog):
    """Диалог для редактирования результата."""

    def __init__(self, result: dict = None, parent=None):
        super().__init__(parent)
        self.result = result or {}
        self.setWindowTitle("Редактирование записи" if result else "Новая запись")
        self.setMinimumSize(600, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Модель
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Модель:"))
        self.model_edit = QLineEdit()
        self.model_edit.setText(self.result.get("model_name", ""))
        model_layout.addWidget(self.model_edit)
        layout.addLayout(model_layout)

        # Промпт
        layout.addWidget(QLabel("Промпт:"))
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setText(self.result.get("prompt_text", ""))
        self.prompt_edit.setMaximumHeight(100)
        layout.addWidget(self.prompt_edit)

        # Ответ
        layout.addWidget(QLabel("Ответ:"))
        self.response_edit = QTextEdit()
        self.response_edit.setText(self.result.get("response", ""))
        layout.addWidget(self.response_edit)

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Сохранить")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #219a52; }
        """)
        buttons_layout.addWidget(save_btn)
        layout.addLayout(buttons_layout)

    def get_values(self) -> dict:
        return {
            "model_name": self.model_edit.text(),
            "prompt_text": self.prompt_edit.toPlainText(),
            "response": self.response_edit.toPlainText(),
        }


class HistoryTab(QWidget):
    """Вкладка «История» с пагинацией и CRUD."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_page = 1
        self.page_size = 20
        self.total_rows = 0
        self.results_cache = []  # Кэш результатов для доступа по индексу
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Заголовок и поиск
        header_layout = QHBoxLayout()
        title = QLabel("История результатов")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск...")
        self.search_edit.setMaximumWidth(300)
        self.search_edit.returnPressed.connect(self.search_and_reset)
        header_layout.addWidget(self.search_edit)

        refresh_btn = QPushButton("⟳")
        refresh_btn.setFixedWidth(30)
        refresh_btn.clicked.connect(self.load_history)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # CRUD кнопки
        crud_layout = QHBoxLayout()

        self.view_btn = QPushButton("📖 Просмотр")
        self.view_btn.clicked.connect(self.view_result)
        self.view_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        crud_layout.addWidget(self.view_btn)

        self.edit_btn = QPushButton("✏️ Изменить")
        self.edit_btn.clicked.connect(self.edit_result)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        crud_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        crud_layout.addWidget(self.delete_btn)

        crud_layout.addStretch()

        export_md_btn = QPushButton("📄 Markdown")
        export_md_btn.clicked.connect(self.export_markdown)
        crud_layout.addWidget(export_md_btn)

        export_json_btn = QPushButton("📋 JSON")
        export_json_btn.clicked.connect(self.export_json)
        crud_layout.addWidget(export_json_btn)

        layout.addLayout(crud_layout)

        # Таблица истории
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(
            ["Дата", "Модель", "Промпт", "Ответ"]
        )
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSortingEnabled(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.doubleClicked.connect(self.view_result)
        layout.addWidget(self.history_table)

        # Пагинация
        pagination_layout = QHBoxLayout()

        self.first_btn = QPushButton("⏮")
        self.first_btn.setFixedWidth(40)
        self.first_btn.clicked.connect(self.go_first)
        pagination_layout.addWidget(self.first_btn)

        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedWidth(40)
        self.prev_btn.clicked.connect(self.go_prev)
        pagination_layout.addWidget(self.prev_btn)

        self.page_label = QLabel("Страница 1 из 1")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setMinimumWidth(150)
        pagination_layout.addWidget(self.page_label)

        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedWidth(40)
        self.next_btn.clicked.connect(self.go_next)
        pagination_layout.addWidget(self.next_btn)

        self.last_btn = QPushButton("⏭")
        self.last_btn.setFixedWidth(40)
        self.last_btn.clicked.connect(self.go_last)
        pagination_layout.addWidget(self.last_btn)

        pagination_layout.addStretch()

        pagination_layout.addWidget(QLabel("На странице:"))
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["10", "20", "50", "100"])
        self.page_size_combo.setCurrentText("20")
        self.page_size_combo.currentTextChanged.connect(self.change_page_size)
        pagination_layout.addWidget(self.page_size_combo)

        self.total_label = QLabel("Всего: 0")
        pagination_layout.addWidget(self.total_label)

        layout.addLayout(pagination_layout)

    def search_and_reset(self):
        """Сброс на первую страницу при поиске."""
        self.current_page = 1
        self.load_history()

    def load_history(self):
        """Загрузить историю с пагинацией."""
        self.history_table.setRowCount(0)
        search = self.search_edit.text().strip()

        # Получить общее количество
        all_results = self.db.get_results(search=search, limit=10000)
        self.total_rows = len(all_results)

        # Расчёт пагинации
        total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        if self.current_page > total_pages:
            self.current_page = total_pages

        # Получить данные для текущей страницы
        offset = (self.current_page - 1) * self.page_size
        self.results_cache = self.db.get_results(
            search=search, limit=self.page_size, offset=offset
        )

        for result in self.results_cache:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)

            # Дата
            date_item = QTableWidgetItem(result["created_at"])
            self.history_table.setItem(row, 0, date_item)

            # Модель
            self.history_table.setItem(row, 1, QTableWidgetItem(result["model_name"]))

            # Промпт
            prompt_text = result["prompt_text"][:100] + "..." if len(result["prompt_text"]) > 100 else result["prompt_text"]
            prompt_item = QTableWidgetItem(prompt_text)
            prompt_item.setToolTip(result["prompt_text"])
            self.history_table.setItem(row, 2, prompt_item)

            # Ответ
            response_text = result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"]
            response_item = QTableWidgetItem(response_text)
            response_item.setToolTip(result["response"])
            self.history_table.setItem(row, 3, response_item)

        self.history_table.resizeRowsToContents()

        # Обновить метки пагинации
        self.page_label.setText(f"Страница {self.current_page} из {total_pages}")
        self.total_label.setText(f"Всего: {self.total_rows}")

        # Состояние кнопок
        self.first_btn.setEnabled(self.current_page > 1)
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < total_pages)
        self.last_btn.setEnabled(self.current_page < total_pages)

    def go_first(self):
        self.current_page = 1
        self.load_history()

    def go_prev(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_history()

    def go_next(self):
        total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_history()

    def go_last(self):
        self.current_page = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        self.load_history()

    def change_page_size(self, value: str):
        self.page_size = int(value)
        self.current_page = 1
        self.load_history()

    def get_selected_result(self) -> dict:
        """Получить выбранный результат."""
        selected = self.history_table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        if row < len(self.results_cache):
            return self.results_cache[row]
        return None

    def view_result(self):
        """Просмотр результата в Markdown."""
        result = self.get_selected_result()
        if not result:
            QMessageBox.warning(self, "Ошибка", "Выберите запись")
            return
        dialog = MarkdownViewerDialog(result["model_name"], result["response"], self)
        dialog.exec_()

    def edit_result(self):
        """Редактировать результат."""
        result = self.get_selected_result()
        if not result:
            QMessageBox.warning(self, "Ошибка", "Выберите запись")
            return

        dialog = EditResultDialog(result, self)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            # Обновить в базе данных
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                UPDATE results 
                SET model_name = ?, prompt_text = ?, response = ?
                WHERE id = ?
                """,
                (values["model_name"], values["prompt_text"], values["response"], result["id"])
            )
            self.db.connection.commit()
            self.load_history()
            QMessageBox.information(self, "Успех", "Запись обновлена")

    def delete_selected(self):
        """Удалить выбранный результат."""
        result = self.get_selected_result()
        if not result:
            QMessageBox.warning(self, "Ошибка", "Выберите запись")
            return

        reply = QMessageBox.question(
            self, "Подтверждение", "Удалить выбранную запись?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_result(result["id"])
            self.load_history()

    def export_markdown(self):
        """Экспорт в Markdown."""
        search = self.search_edit.text().strip()
        results = self.db.get_results(search=search, limit=1000)

        if not results:
            QMessageBox.warning(self, "Ошибка", "Нет данных для экспорта")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как", "export.md", "Markdown (*.md)"
        )
        if not file_path:
            return

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# История ChatList\n\n")
            for r in results:
                f.write(f"## {r['model_name']} — {r['created_at']}\n\n")
                f.write(f"**Промпт:** {r['prompt_text']}\n\n")
                f.write(f"**Ответ:**\n\n{r['response']}\n\n---\n\n")

        log_export(file_path, "Markdown")
        QMessageBox.information(self, "Успех", f"Экспортировано в {file_path}")

    def export_json(self):
        """Экспорт в JSON."""
        import json

        search = self.search_edit.text().strip()
        results = self.db.get_results(search=search, limit=1000)

        if not results:
            QMessageBox.warning(self, "Ошибка", "Нет данных для экспорта")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как", "export.json", "JSON (*.json)"
        )
        if not file_path:
            return

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        log_export(file_path, "JSON")
        QMessageBox.information(self, "Успех", f"Экспортировано в {file_path}")


class SettingsTab(QWidget):
    """Вкладка «Настройки»."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("Настройки")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # Таймаут
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("Таймаут запроса (сек):")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(60)
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.timeout_spin)
        timeout_layout.addStretch()
        layout.addLayout(timeout_layout)

        # Максимум токенов
        tokens_layout = QHBoxLayout()
        tokens_label = QLabel("Максимум токенов:")
        self.tokens_spin = QSpinBox()
        self.tokens_spin.setRange(100, 16000)
        self.tokens_spin.setValue(4096)
        tokens_layout.addWidget(tokens_label)
        tokens_layout.addWidget(self.tokens_spin)
        tokens_layout.addStretch()
        layout.addLayout(tokens_layout)

        # Кнопка сохранения
        save_btn = QPushButton("💾 Сохранить настройки")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        layout.addWidget(save_btn)

        layout.addStretch()

    def load_settings(self):
        """Загрузить настройки."""
        timeout = self.db.get_setting("request_timeout", "60")
        max_tokens = self.db.get_setting("max_tokens", "4096")

        self.timeout_spin.setValue(int(timeout))
        self.tokens_spin.setValue(int(max_tokens))

    def save_settings(self):
        """Сохранить настройки."""
        self.db.set_setting("request_timeout", str(self.timeout_spin.value()))
        self.db.set_setting("max_tokens", str(self.tokens_spin.value()))
        QMessageBox.information(self, "Успех", "Настройки сохранены")


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatList — Сравнение нейросетей")
        self.setMinimumSize(1000, 700)

        # Инициализация компонентов
        self.db = Database()
        self.model_manager = ModelManager(self.db)
        self.results_store = ResultsStore()
        self.worker = None

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Настройка интерфейса."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background: white;
            }
            QTabBar::tab {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 10px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: none;
            }
        """)

        # Создание вкладок
        self.request_tab = RequestTab(self.db, self.model_manager)
        self.results_tab = ResultsTab(self.db, self.results_store)
        self.models_tab = ModelsTab(self.model_manager)
        self.history_tab = HistoryTab(self.db)
        self.settings_tab = SettingsTab(self.db)

        self.tabs.addTab(self.request_tab, "📝 Запрос")
        self.tabs.addTab(self.results_tab, "📊 Результаты")
        self.tabs.addTab(self.models_tab, "🤖 Модели")
        self.tabs.addTab(self.history_tab, "📚 История")
        self.tabs.addTab(self.settings_tab, "⚙️ Настройки")

        # Переключение вкладок
        self.tabs.currentChanged.connect(self.on_tab_changed)

        layout.addWidget(self.tabs)

    def setup_connections(self):
        """Настройка сигналов и слотов."""
        self.request_tab.request_sent.connect(self.send_requests)

    def on_tab_changed(self, index: int):
        """Обработка переключения вкладок."""
        # Обновление данных при переключении на вкладку История
        if index == 3:  # История
            self.history_tab.load_history()

    def send_requests(self, prompt: str, models: list):
        """Отправить запросы во все модели."""
        # Логирование
        log_request(prompt, models)

        # Показать прогресс
        self.request_tab.progress.setVisible(True)
        self.request_tab.progress.setRange(0, 0)  # Indeterminate
        self.request_tab.send_btn.setEnabled(False)
        self.request_tab.status_label.setText(f"Отправка в {len(models)} моделей...")

        # Получить таймаут из настроек
        timeout = int(self.db.get_setting("request_timeout", "60"))

        # Запуск воркера
        self.worker = RequestWorker(prompt, models, timeout)
        self.worker.finished.connect(self.on_requests_finished)
        self.worker.error.connect(self.on_requests_error)
        self.worker.start()

    def on_requests_finished(self, results: list):
        """Обработка завершения запросов."""
        self.request_tab.progress.setVisible(False)
        self.request_tab.send_btn.setEnabled(True)
        self.request_tab.status_label.setText(f"Получено {len(results)} ответов")

        # Логирование результатов
        for r in results:
            log_response(
                r.get("model_name", "Unknown"),
                r.get("success", False),
                r.get("tokens", 0),
                r.get("error"),
            )

        # Сохранить результаты
        self.results_store.set_results(self.worker.prompt, results)
        self.results_tab.update_results()

        # Переключиться на вкладку результатов
        self.tabs.setCurrentIndex(1)

    def on_requests_error(self, error: str):
        """Обработка ошибки запросов."""
        log_error("Ошибка при отправке запросов", Exception(error))
        self.request_tab.progress.setVisible(False)
        self.request_tab.send_btn.setEnabled(True)
        self.request_tab.status_label.setText(f"Ошибка: {error}")
        QMessageBox.critical(self, "Ошибка", error)

    def closeEvent(self, event):
        """Обработка закрытия окна."""
        log_app_close()
        self.db.close()
        event.accept()


def main():
    """Точка входа."""
    log_app_start()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Шрифт по умолчанию
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
