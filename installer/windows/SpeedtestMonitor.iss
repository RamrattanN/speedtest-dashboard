#define AppName "Speedtest Monitor"
#define AppVersion "0.2.0-windows-pilot.1"
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
OutputBaseFilename=Speedtest-Monitor-Windows-x64-pilot-1
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
