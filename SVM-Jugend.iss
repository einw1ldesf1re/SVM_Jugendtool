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

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\SVM-Jugend"
Type: filesandordirs; Name: "{app}"
Type: dirifempty; Name: "{localappdata}\SVM-Jugend"

[Code]
var
  ResultCode: Integer;
  RunAfterInstall: String;
  IsAutoUpdate: Boolean;

function InitializeSetup(): Boolean;
begin
  // Prüfen, ob Parameter --run-after-install übergeben wurde
  RunAfterInstall := ExpandConstant('{param:run-after-install}');
  IsAutoUpdate := RunAfterInstall <> '';
  Result := True;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  // Wenn es ein Auto-Update ist, RunList komplett verstecken
  if IsAutoUpdate and (CurPageID = wpFinished) then
    WizardForm.RunList.Visible := False;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;

  // Nach Installation: Anwendung automatisch starten
  // (nur, wenn kein Neustart angefordert ist)
  if (CurPageID = wpFinished) and
     ((not WizardForm.YesRadio.Visible) or (not WizardForm.YesRadio.Checked)) then
  begin
    if IsAutoUpdate then
      ExecAsOriginalUser(RunAfterInstall, '', '', SW_SHOWNORMAL, ewNoWait, ResultCode)
    else
      ExecAsOriginalUser(ExpandConstant('{app}\SVM-Jugend.exe'), '', '', SW_SHOWNORMAL, ewNoWait, ResultCode);
  end;
end;
