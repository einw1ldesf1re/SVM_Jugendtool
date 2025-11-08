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
  if IsAutoUpdate and (WizardForm.RunList <> nil) then
    WizardForm.RunList.Visible := False;

  Result := True;
end;

// Hilfsfunktion: Prozess beenden, falls er läuft
procedure KillProcessIfRunning(const exeName: string);
var
  ResultCode: Integer;
begin
  Exec('taskkill', '/F /IM ' + exeName, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if IsAutoUpdate then
    begin
      // Vor dem Start prüfen, ob alte Version noch läuft
      KillProcessIfRunning('SVM-Jugend.exe');

      // Auto-Update: alle Dateien installiert, App sauber starten
      if FileExists(RunAfterInstall) then
        ShellExec('', RunAfterInstall, '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode)
      else
        MsgBox('Fehler: Die zu startende Datei wurde nicht gefunden: ' + RunAfterInstall, mbError, MB_OK);
    end
    else
    begin
      // Manuelle Installation: nur starten, wenn Checkbox gesetzt ist
      if (WizardForm.RunList <> nil) and (WizardForm.RunList.Count > 0) then
      begin
        if WizardForm.RunList.Checked[0] then
        begin
          if FileExists(ExpandConstant('{app}\SVM-Jugend.exe')) then
            ShellExec('', ExpandConstant('{app}\SVM-Jugend.exe'), '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode)
          else
            MsgBox('Fehler: Die zu startende Datei wurde nicht gefunden!', mbError, MB_OK);
        end;
      end;
    end;
  end;
end;


[UninstallDelete]
; Alles in AppData\Local\SVM-Jugend löschen
Type: filesandordirs; Name: "{localappdata}\SVM-Jugend"

; Alles in Program Files\SVM Jugend löschen (das Installationsverzeichnis)
Type: filesandordirs; Name: "{app}"

; optional: leeren Ordner löschen, falls keine Dateien mehr drin
Type: dirifempty; Name: "{localappdata}\SVM-Jugend"