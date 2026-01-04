"""
Минимальное приложение на PyQt5
"""

import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import Qt


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Приложение")
        self.setMinimumSize(400, 300)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Компоновка
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)

        # Метка
        self.label = QLabel("Привет, мир!")
        self.label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Кнопка
        self.button = QPushButton("Нажми меня")
        self.button.setFixedSize(150, 40)
        self.button.clicked.connect(self.on_button_click)
        layout.addWidget(self.button)

        self.click_count = 0

    def on_button_click(self):
        """Обработчик нажатия кнопки."""
        self.click_count += 1
        self.label.setText(f"Нажатий: {self.click_count}")


def main():
    """Точка входа в приложение."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

