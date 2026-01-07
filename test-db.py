"""
Тестовая программа для работы с SQLite базами данных.
Отображает список таблиц и позволяет выполнять CRUD операции.
"""

import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QDialog,
    QLineEdit,
    QFormLayout,
    QDialogButtonBox,
    QSplitter,
    QFrame,
    QComboBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class EditDialog(QDialog):
    """Диалог для редактирования/создания записи."""

    def __init__(self, columns: list, values: dict = None, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.values = values or {}
        self.inputs = {}
        self.setWindowTitle("Редактирование записи" if values else "Новая запись")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Форма
        form_layout = QFormLayout()
        for col in self.columns:
            line_edit = QLineEdit()
            line_edit.setText(str(self.values.get(col, "")))
            # ID обычно не редактируется
            if col.lower() == "id" and self.values:
                line_edit.setEnabled(False)
            self.inputs[col] = line_edit
            form_layout.addRow(f"{col}:", line_edit)
        layout.addLayout(form_layout)

        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self) -> dict:
        """Получить введённые значения."""
        return {col: self.inputs[col].text() for col in self.columns}


class TableViewWidget(QWidget):
    """Виджет для отображения таблицы с пагинацией и CRUD."""

    def __init__(self, db_path: str, table_name: str, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.table_name = table_name
        self.current_page = 1
        self.page_size = 20
        self.total_rows = 0
        self.columns = []
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        header_layout = QHBoxLayout()
        title = QLabel(f"Таблица: {self.table_name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # CRUD кнопки
        self.add_btn = QPushButton("➕ Добавить")
        self.add_btn.clicked.connect(self.add_record)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #219a52; }
        """)
        header_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("✏️ Изменить")
        self.edit_btn.clicked.connect(self.edit_record)
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
        header_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.clicked.connect(self.delete_record)
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
        header_layout.addWidget(self.delete_btn)

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self.load_data)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        header_layout.addWidget(self.refresh_btn)

        layout.addLayout(header_layout)

        # Таблица данных
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 8px;
            }
        """)
        layout.addWidget(self.data_table)

        # Пагинация
        pagination_layout = QHBoxLayout()

        self.first_btn = QPushButton("⏮ Начало")
        self.first_btn.clicked.connect(self.go_first)
        pagination_layout.addWidget(self.first_btn)

        self.prev_btn = QPushButton("◀ Назад")
        self.prev_btn.clicked.connect(self.go_prev)
        pagination_layout.addWidget(self.prev_btn)

        self.page_label = QLabel("Страница 1 из 1")
        self.page_label.setAlignment(Qt.AlignCenter)
        pagination_layout.addWidget(self.page_label)

        self.next_btn = QPushButton("Вперёд ▶")
        self.next_btn.clicked.connect(self.go_next)
        pagination_layout.addWidget(self.next_btn)

        self.last_btn = QPushButton("Конец ⏭")
        self.last_btn.clicked.connect(self.go_last)
        pagination_layout.addWidget(self.last_btn)

        pagination_layout.addStretch()

        pagination_layout.addWidget(QLabel("Записей на странице:"))
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(5, 100)
        self.page_size_spin.setValue(self.page_size)
        self.page_size_spin.valueChanged.connect(self.change_page_size)
        pagination_layout.addWidget(self.page_size_spin)

        self.total_label = QLabel("Всего: 0")
        pagination_layout.addWidget(self.total_label)

        layout.addLayout(pagination_layout)

    def get_connection(self):
        """Получить соединение с БД."""
        return sqlite3.connect(self.db_path)

    def load_data(self):
        """Загрузить данные из таблицы."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Получить количество записей
        cursor.execute(f"SELECT COUNT(*) FROM [{self.table_name}]")
        self.total_rows = cursor.fetchone()[0]

        # Получить названия колонок
        cursor.execute(f"PRAGMA table_info([{self.table_name}])")
        self.columns = [row[1] for row in cursor.fetchall()]

        # Расчёт пагинации
        total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        if self.current_page > total_pages:
            self.current_page = total_pages

        offset = (self.current_page - 1) * self.page_size

        # Получить данные
        cursor.execute(
            f"SELECT * FROM [{self.table_name}] LIMIT ? OFFSET ?",
            (self.page_size, offset)
        )
        rows = cursor.fetchall()
        conn.close()

        # Заполнить таблицу
        self.data_table.setColumnCount(len(self.columns))
        self.data_table.setHorizontalHeaderLabels(self.columns)
        self.data_table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value) if value is not None else "")
                self.data_table.setItem(row_idx, col_idx, item)

        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        if self.columns:
            self.data_table.horizontalHeader().setSectionResizeMode(
                len(self.columns) - 1, QHeaderView.Stretch
            )

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
        self.load_data()

    def go_prev(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def go_next(self):
        total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_data()

    def go_last(self):
        self.current_page = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        self.load_data()

    def change_page_size(self, value):
        self.page_size = value
        self.current_page = 1
        self.load_data()

    def get_selected_row_data(self) -> dict:
        """Получить данные выбранной строки."""
        selected = self.data_table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        return {
            self.columns[col]: self.data_table.item(row, col).text()
            for col in range(len(self.columns))
        }

    def add_record(self):
        """Добавить новую запись."""
        # Исключаем ID из редактирования при добавлении
        edit_columns = [c for c in self.columns if c.lower() != "id"]
        dialog = EditDialog(edit_columns, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            columns_str = ", ".join([f"[{c}]" for c in values.keys()])
            placeholders = ", ".join(["?" for _ in values])
            query = f"INSERT INTO [{self.table_name}] ({columns_str}) VALUES ({placeholders})"

            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(query, list(values.values()))
                conn.commit()
                conn.close()
                self.load_data()
                QMessageBox.information(self, "Успех", "Запись добавлена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def edit_record(self):
        """Редактировать выбранную запись."""
        data = self.get_selected_row_data()
        if not data:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования")
            return

        dialog = EditDialog(self.columns, data, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            # Найти первичный ключ (обычно id)
            pk_column = self.columns[0]
            pk_value = data[pk_column]

            set_clause = ", ".join([f"[{c}] = ?" for c in values.keys() if c != pk_column])
            update_values = [v for c, v in values.items() if c != pk_column]
            update_values.append(pk_value)

            query = f"UPDATE [{self.table_name}] SET {set_clause} WHERE [{pk_column}] = ?"

            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(query, update_values)
                conn.commit()
                conn.close()
                self.load_data()
                QMessageBox.information(self, "Успех", "Запись обновлена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def delete_record(self):
        """Удалить выбранную запись."""
        data = self.get_selected_row_data()
        if not data:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления")
            return

        reply = QMessageBox.question(
            self, "Подтверждение", "Удалить выбранную запись?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            pk_column = self.columns[0]
            pk_value = data[pk_column]

            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    f"DELETE FROM [{self.table_name}] WHERE [{pk_column}] = ?",
                    (pk_value,)
                )
                conn.commit()
                conn.close()
                self.load_data()
                QMessageBox.information(self, "Успех", "Запись удалена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()
        self.db_path = None
        self.setWindowTitle("SQLite Database Viewer")
        self.setMinimumSize(1000, 700)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Панель выбора файла
        file_layout = QHBoxLayout()
        self.file_label = QLabel("База данных не выбрана")
        self.file_label.setStyleSheet("color: #7f8c8d;")
        file_layout.addWidget(self.file_label)
        file_layout.addStretch()

        open_file_btn = QPushButton("📂 Открыть базу данных")
        open_file_btn.clicked.connect(self.open_database)
        open_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        file_layout.addWidget(open_file_btn)
        layout.addLayout(file_layout)

        # Разделитель
        splitter = QSplitter(Qt.Horizontal)

        # Левая панель — список таблиц
        left_frame = QFrame()
        left_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 5px;
            }
        """)
        left_layout = QVBoxLayout(left_frame)

        tables_label = QLabel("Таблицы")
        tables_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        left_layout.addWidget(tables_label)

        self.tables_list = QListWidget()
        self.tables_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #dee2e6;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        left_layout.addWidget(self.tables_list)

        open_table_btn = QPushButton("📖 Открыть таблицу")
        open_table_btn.clicked.connect(self.open_table)
        open_table_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        left_layout.addWidget(open_table_btn)

        splitter.addWidget(left_frame)

        # Правая панель — содержимое таблицы
        self.right_frame = QFrame()
        self.right_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 5px;
            }
        """)
        self.right_layout = QVBoxLayout(self.right_frame)

        placeholder = QLabel("Выберите таблицу для просмотра")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #bdc3c7; font-size: 18px;")
        self.right_layout.addWidget(placeholder)

        splitter.addWidget(self.right_frame)
        splitter.setSizes([250, 750])

        layout.addWidget(splitter)

    def open_database(self):
        """Открыть файл базы данных."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть базу данных",
            "", "SQLite Database (*.db *.sqlite *.sqlite3);;All Files (*)"
        )
        if file_path:
            self.db_path = file_path
            self.file_label.setText(f"📁 {file_path}")
            self.file_label.setStyleSheet("color: #2c3e50;")
            self.load_tables()

    def load_tables(self):
        """Загрузить список таблиц."""
        self.tables_list.clear()
        if not self.db_path:
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()
            conn.close()

            for table in tables:
                item = QListWidgetItem(f"📋 {table[0]}")
                item.setData(Qt.UserRole, table[0])
                self.tables_list.addItem(item)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть базу данных:\n{e}")

    def open_table(self):
        """Открыть выбранную таблицу."""
        selected = self.tables_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу")
            return

        table_name = selected.data(Qt.UserRole)

        # Очистить правую панель
        while self.right_layout.count():
            child = self.right_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Добавить виджет таблицы
        table_view = TableViewWidget(self.db_path, table_name, self)
        self.right_layout.addWidget(table_view)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

