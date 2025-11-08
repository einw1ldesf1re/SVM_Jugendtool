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
; Nur bei manueller Installation: Normaler Start nach Installation
Filename: "{app}\SVM-Jugend.exe"; Description: "Programm starten"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Alles in AppData\Local\SVM-Jugend löschen
Type: filesandordirs; Name: "{localappdata}\SVM-Jugend"

; Alles in Program Files\SVM Jugend löschen (Installationsverzeichnis)
Type: filesandordirs; Name: "{app}"

; Optional: leeren Ordner löschen, falls keine Dateien mehr drin
Type: dirifempty; Name: "{localappdata}\SVM-Jugend"

[Code]
var
  RunAfterInstall: string;
  ErrorCode: Integer;

function InitializeSetup(): Boolean;
begin
  // Prüfen, ob Parameter --run-after-install übergeben wurde
  RunAfterInstall := ExpandConstant('{param:run-after-install}');
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  // Automatisches Starten der alten Version nach Auto-Update
  if (CurStep = ssPostInstall) and (RunAfterInstall <> '') then
  begin
    ShellExec('', RunAfterInstall, '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
  end;
end;

// Checkbox-Seite überspringen, wenn Auto-Update
function ShouldSkipRunPage(PageID: Integer): Boolean;
begin
  if (RunAfterInstall <> '') and (PageID = wpFinished) then
    Result := True
  else
    Result := False;
end;
