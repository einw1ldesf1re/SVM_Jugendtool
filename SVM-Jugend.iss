[Setup]
AppName=SVM Jugend
AppVersion=1.0.0
DefaultDirName={autopf}\SVM Jugend
DefaultGroupName=SVM Jugend
OutputBaseFilename=SVM-Jugend-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile={#MyIconPath}
WizardImageFile={#MyBannerPath}
WizardSmallImageFile={#MySmallPath}

[Files]
Source: "{#MyExePath}"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: recursesubdirs ignoreversion
Source: "version.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SVM Jugend"; Filename: "{app}\SVM-Jugend.exe"; IconFilename: "{app}\assets\icons\icon_512x512.ico"
Name: "{commondesktop}\SVM Jugend"; Filename: "{app}\SVM-Jugend.exe"; IconFilename: "{app}\assets\icons\icon_512x512.ico"

[Run]
Filename: "{app}\SVM-Jugend.exe"; Description: "Programm starten"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; komplette DB-Datei löschen
Type: files; Name: "{localappdata}\SVM-Jugend\training_manager.db"

; optional: leeren Ordner löschen, falls keine Dateien mehr drin
Type: dirifempty; Name: "{localappdata}\SVM-Jugend"