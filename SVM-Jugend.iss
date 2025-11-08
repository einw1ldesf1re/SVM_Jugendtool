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
; Checkbox nur für manuelle Installation
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
  // Prüfen, ob Parameter --run-after-install übergeben wurde
  RunAfterInstall := ExpandConstant('{param:run-after-install}');
  IsAutoUpdate := RunAfterInstall <> '';
  Result := True;
end;

procedure InitializeWizard();
begin
  // Auto-Update: Checkbox und Label auf Fertigstellen-Seite ausblenden
  if IsAutoUpdate then
  begin
    try
      WizardForm.RunList.Visible := False;
    except
    end;

    try
      WizardForm.RunListLabel.Visible := False;
    except
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  // Auto-Update: alte Version automatisch starten
  if (CurStep = ssPostInstall) and IsAutoUpdate then
  begin
    ShellExec('', RunAfterInstall, '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
  end;
end;

function ShouldSkipRunPage(PageID: Integer): Boolean;
begin
  // Fertigstellen-Seite überspringen, falls Auto-Update
  if IsAutoUpdate and (PageID = wpFinished) then
    Result := True
  else
    Result := False;
end;
