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
Filename: "{app}\SVM-Jugend.exe"; Description: "Programm starten"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\SVM-Jugend"
Type: filesandordirs; Name: "{app}"
Type: dirifempty; Name: "{localappdata}\SVM-Jugend"

[Code]
var
  RunAfterInstall: string;
  ErrorCode: Integer;
  IsAutoUpdate: Boolean;

function InitializeSetup(): Boolean;
begin
  RunAfterInstall := ExpandConstant('{param:run-after-install}');
  IsAutoUpdate := RunAfterInstall <> '';
  Result := True;
end;

procedure InitializeWizard();
begin
  // Wenn Auto-Update: RunList ausblenden UND Checkbox auf "Fertigstellen"-Seite verstecken
  if IsAutoUpdate then
  begin
    WizardForm.RunList.Visible := False;
    WizardForm.RunListLabel.Visible := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  // Nach Installation automatisch starten, wenn Auto-Update
  if (CurStep = ssPostInstall) and IsAutoUpdate then
  begin
    ShellExec('', RunAfterInstall, '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
  end;
end;
