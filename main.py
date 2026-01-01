import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Моё первое PyQt приложение")
        self.setGeometry(100, 100, 400, 300)
        
        # Создаём центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Создаём layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Добавляем метку
        self.label = QLabel("Привет, мир!")
        self.label.setStyleSheet("font-size: 18px; padding: 20px;")
        layout.addWidget(self.label)
        
        # Добавляем кнопку
        self.button = QPushButton("Нажми меня")
        self.button.clicked.connect(self.on_button_click)
        layout.addWidget(self.button)
        
        self.click_count = 0
    
    def on_button_click(self):
        self.click_count += 1
        self.label.setText(f"Кнопка нажата {self.click_count} раз!")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

