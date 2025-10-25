import sys
from PyQt6.QtWidgets import QApplication
from db import init_db
from ui.main_window import MainWindow

def main():
    init_db()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()