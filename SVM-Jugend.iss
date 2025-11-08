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

[Run]
Filename: "{app}\SVM-Jugend.exe"; Flags: postinstall nowait

[Code]
var
  IsAutoUpdate: Boolean;

function InitializeSetup(): Boolean;
begin
  IsAutoUpdate := ParamCount() > 0;
  Result := True;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if IsAutoUpdate and (CurPageID = wpFinished) then
    WizardForm.RunList.Visible := False;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  if CurPageID = wpFinished then
  begin
    // Starte EXE aus Installationsordner, egal ob Auto-Update
    ExecAsOriginalUser(ExpandConstant('{app}\SVM-Jugend.exe'), '', '', SW_SHOWNORMAL, ewNoWait, ResultCode);
  end;
end;
