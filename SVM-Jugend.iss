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
  ErrorCode: Integer;
  IsAutoUpdate: Boolean;

function InitializeSetup(): Boolean;
begin
  // Prüfen, ob es sich um Auto-Update handelt
  RunAfterInstall := ExpandConstant('{param:run-after-install}');
  IsAutoUpdate := RunAfterInstall <> '';

  // Checkbox nur sichtbar machen, wenn es keine Auto-Update Installation ist
  if IsAutoUpdate and Assigned(WizardForm) and Assigned(WizardForm.RunList) then
  begin
    WizardForm.RunList.Visible := False; // Liste ausblenden
    WizardForm.RunList.Clear;            // Inhalte leeren, damit keine Count-Fehler
  end;

  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and IsAutoUpdate then
  begin
    // Alte App beenden, falls sie noch läuft
    Exec('taskkill', '/F /IM SVM-Jugend.exe', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);

    // Neue Version starten
    if FileExists(RunAfterInstall) then
      ShellExec('', RunAfterInstall, '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode)
    else
      MsgBox('Fehler: Datei zum Starten nicht gefunden: ' + RunAfterInstall, mbError, MB_OK);
  end;
end;


[UninstallDelete]
; Alles in AppData\Local\SVM-Jugend löschen
Type: filesandordirs; Name: "{localappdata}\SVM-Jugend"

; Alles in Program Files\SVM Jugend löschen (das Installationsverzeichnis)
Type: filesandordirs; Name: "{app}"

; optional: leeren Ordner löschen, falls keine Dateien mehr drin
Type: dirifempty; Name: "{localappdata}\SVM-Jugend"