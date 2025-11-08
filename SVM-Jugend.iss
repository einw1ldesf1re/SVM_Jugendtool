;----------------------------------
; SVM-Jugend Installer
;----------------------------------

[Setup]
AppName=SVM-Jugend
AppVersion={#MyAppVer}
DefaultDirName={pf}\SVM Jugend
DefaultGroupName=SVM-Jugend
OutputDir=Output
OutputBaseFilename=SVM-Jugend-Setup
Compression=lzma
SolidCompression=yes
AllowNoIcons=yes
DisableDirPage=no
DisableProgramGroupPage=no
UninstallDisplayIcon={app}\SVM-Jugend.exe
UninstallFilesDir={app}
WizardImageFile=assets\installer_banner.bmp
WizardSmallImageFile=assets\installer_small.bmp
LicenseFile=LICENSE.txt

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Files]
Source: "{#MyExePath}"; DestDir: "{app}"; Flags: ignoreversion
Source: "docs\version.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SVM-Jugend"; Filename: "{app}\SVM-Jugend.exe"
Name: "{commondesktop}\SVM-Jugend"; Filename: "{app}\SVM-Jugend.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Desktop-Icon erstellen"; GroupDescription: "Optionale Aufgaben:"

[Code]
var
  AutoUpdate: Boolean;
  RunAfterInstall: string;
  ErrorCode: Integer;

function InitializeSetup(): Boolean;
begin
  // Prüfen ob der Parameter --run-after-install übergeben wurde
  AutoUpdate := False;
  RunAfterInstall := ExpandConstant('{param:run-after-install}');
  if RunAfterInstall <> '' then
    AutoUpdate := True;
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and (AutoUpdate) then
  begin
    // Alte Version beenden
    if FileExists(RunAfterInstall) then
      Exec(RunAfterInstall, '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);

    // Checkbox "Anwendung starten" wird nicht angezeigt bei Auto-Update
  end;
end;

[Run]
; Checkbox nur anzeigen, wenn es keine Auto-Update-Installation ist
Filename: "{app}\SVM-Jugend.exe"; Description: "{cm:LaunchProgram, SVM-Jugend}"; Flags: nowait postinstall skipifsilent; Check: not AutoUpdate
