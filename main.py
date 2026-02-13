import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer
from threading import Thread
# from db import init_db
from ui.main_window import MainWindow

from utils.updater import check_for_update
from utils.init_database import init_database

def main():
    # init_db()
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/icons/icon_512x512.ico"))

    db_path = init_database()

    win = MainWindow()
    win.show()
    
    # Update-Check im Hintergrund (nicht-blockierend)
    def check_update_async():
        check_for_update()
    
    update_thread = Thread(target=check_update_async, daemon=True)
    update_thread.start()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()