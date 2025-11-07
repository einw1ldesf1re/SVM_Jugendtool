1. Exe erstellen!
    py -m PyInstaller --onefile --windowed --icon=assets/icons/icon_512x512.ico --name SVM-Jugend --add-data "assets;assets" main.py
1. insteller erstellen!
    & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "SVM-Jugend.iss"