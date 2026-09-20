#define AppName "Speedtest Monitor"
#define AppVersion "0.2.0-windows-pilot.2"
#define AppExeName "Speedtest Monitor.exe"

[Setup]
AppId={{A46EA70B-0898-40CD-A611-01C973787737}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Ramrattan Network Tools
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist
OutputBaseFilename=Speedtest-Monitor-Windows-x64-pilot-2
SetupIconFile=..\..\build\windows-icon\SpeedtestMonitor.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExeName}
CloseApplications=yes

[Files]
Source: "..\..\dist\Speedtest Monitor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\Ramrattan Speedtest Monitor"

[Code]
function ShowMaintenanceChoice(): Integer;
var
  MaintenanceForm: TSetupForm;
  HeadingLabel: TNewStaticText;
  DetailLabel: TNewStaticText;
  RepairButton: TNewButton;
  UninstallButton: TNewButton;
  CancelButton: TNewButton;
begin
  MaintenanceForm := CreateCustomForm(
    ScaleX(440), ScaleY(190), True, True);
  try
    MaintenanceForm.Caption := '{#AppName} Maintenance';
    MaintenanceForm.Position := poScreenCenter;

    HeadingLabel := TNewStaticText.Create(MaintenanceForm);
    HeadingLabel.Parent := MaintenanceForm;
    HeadingLabel.Caption := '{#AppName} is already installed.';
    HeadingLabel.Font.Style := [fsBold];
    HeadingLabel.Left := ScaleX(24);
    HeadingLabel.Top := ScaleY(22);
    HeadingLabel.AutoSize := True;

    DetailLabel := TNewStaticText.Create(MaintenanceForm);
    DetailLabel.Parent := MaintenanceForm;
    DetailLabel.Caption :=
      'Repair reinstalls all application files.  Uninstall completely removes ' +
      'the application, shortcuts, and logs while preserving speed-test history.';
    DetailLabel.Left := ScaleX(24);
    DetailLabel.Top := ScaleY(52);
    DetailLabel.Width := ScaleX(392);
    DetailLabel.Height := ScaleY(52);
    DetailLabel.WordWrap := True;

    RepairButton := TNewButton.Create(MaintenanceForm);
    RepairButton.Parent := MaintenanceForm;
    RepairButton.Caption := '&Repair';
    RepairButton.ModalResult := mrYes;
    RepairButton.Left := ScaleX(24);
    RepairButton.Top := ScaleY(128);
    RepairButton.Width := ScaleX(120);
    RepairButton.Height := ScaleY(32);
    RepairButton.Default := True;

    UninstallButton := TNewButton.Create(MaintenanceForm);
    UninstallButton.Parent := MaintenanceForm;
    UninstallButton.Caption := '&Uninstall completely';
    UninstallButton.ModalResult := mrNo;
    UninstallButton.Left := ScaleX(154);
    UninstallButton.Top := ScaleY(128);
    UninstallButton.Width := ScaleX(160);
    UninstallButton.Height := ScaleY(32);

    CancelButton := TNewButton.Create(MaintenanceForm);
    CancelButton.Parent := MaintenanceForm;
    CancelButton.Caption := 'Cancel';
    CancelButton.ModalResult := mrCancel;
    CancelButton.Left := ScaleX(324);
    CancelButton.Top := ScaleY(128);
    CancelButton.Width := ScaleX(92);
    CancelButton.Height := ScaleY(32);
    CancelButton.Cancel := True;

    Result := MaintenanceForm.ShowModal;
  finally
    MaintenanceForm.Free;
  end;
end;

function FindExistingUninstaller(var UninstallerPath: String): Boolean;
begin
  Result := RegQueryStringValue(
    HKCU,
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{A46EA70B-0898-40CD-A611-01C973787737}_is1',
    'UninstallString',
    UninstallerPath);
  if Result then
    UninstallerPath := RemoveQuotes(UninstallerPath)
  else begin
    UninstallerPath := ExpandConstant(
      '{localappdata}\Programs\{#AppName}\unins000.exe');
    Result := FileExists(UninstallerPath);
  end;
end;

function InitializeSetup(): Boolean;
var
  Choice: Integer;
  ExistingUninstaller: String;
  MaintenanceMode: String;
  ResultCode: Integer;
  UninstallArguments: String;
begin
  Result := True;
  if not FindExistingUninstaller(ExistingUninstaller) then
    exit;

  MaintenanceMode := Lowercase(ExpandConstant('{param:MAINTENANCE|}'));
  if MaintenanceMode = 'repair' then
    Choice := mrYes
  else if MaintenanceMode = 'uninstall' then
    Choice := mrNo
  else if WizardSilent then
    Choice := mrYes
  else
    Choice := ShowMaintenanceChoice();

  if Choice = mrYes then
    exit;

  Result := False;
  if Choice <> mrNo then
    exit;

  UninstallArguments := '/SUPPRESSMSGBOXES /NORESTART';
  if MaintenanceMode = 'uninstall' then
    UninstallArguments := UninstallArguments + ' /VERYSILENT';
  if not Exec(
    ExistingUninstaller,
    UninstallArguments,
    '',
    SW_SHOWNORMAL,
    ewWaitUntilTerminated,
    ResultCode) then
    MsgBox(
      'Windows could not start the existing {#AppName} uninstaller.',
      mbError,
      MB_OK);
end;
