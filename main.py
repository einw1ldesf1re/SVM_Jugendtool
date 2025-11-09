import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
# from db import init_db
from ui.main_window import MainWindow

from utils.updater import check_for_update
from utils.init_database import init_database

def main():
    # init_db()
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/icons/icon_512x512.ico"))

    
    check_for_update()
    db_path = init_database()


    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()