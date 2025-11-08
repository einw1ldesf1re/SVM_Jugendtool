[Setup]
AppName=SVM Jugend
AppVersion={#AppVer}
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
; Normaler Start nach Installation, nur wenn kein Auto-Update Parameter
Filename: "{app}\SVM-Jugend.exe"; Description: "Programm starten"; Flags: nowait postinstall skipifsilent

[Code]
var
  RunAfterInstall: string;

function InitializeSetup(): Boolean;
begin
  // Prüfen, ob Parameter für Auto-Update übergeben wurde
  RunAfterInstall := ExpandConstant('{param:run-after-install}');
  RunAfterInstall := Trim(RunAfterInstall);

  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ErrorCode: Integer;
begin
  // Automatischer Start der neuen EXE nach Auto-Update
  if (CurStep = ssPostInstall) and (RunAfterInstall <> '') then
  begin
    { Kleine Pause, damit alte EXE sauber beendet wird }
    Sleep(1000);

    { Neue EXE starten }
    ShellExec(
      '',                // Default-Anwendung
      RunAfterInstall,   // Pfad zur neuen EXE
      '',                // Keine Parameter
      '',                // Arbeitsverzeichnis
      SW_SHOWNORMAL,
      ewNoWait,          // Nicht warten
      ErrorCode
    );
  end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;

  // Checkbox "Anwendung starten" nur bei manueller Installation anzeigen
  if (PageID = wpReady) and (RunAfterInstall <> '') then
  begin
    // Auto-Update → Checkbox ausblenden
    Result := True;
  end;
end;


[UninstallDelete]
; Alles in AppData\Local\SVM-Jugend löschen
Type: filesandordirs; Name: "{localappdata}\SVM-Jugend"

; Alles in Program Files\SVM Jugend löschen (das Installationsverzeichnis)
Type: filesandordirs; Name: "{app}"

; optional: leeren Ordner löschen, falls keine Dateien mehr drin
Type: dirifempty; Name: "{localappdata}\SVM-Jugend"