; Inno Setup Script for ChatList Installation
; Version is taken from version.py

#define MyAppName "ChatList"
#define MyAppVersion "1.0.2"
#define MyAppPublisher "ChatList Team"
#define MyAppURL "https://github.com/Evgen018/ChatList"
#define MyAppExeName "ChatList-v1.0.2.exe"

[Setup]
; Application Information
AppId={{8B3A4D2E-5C9F-4A1B-9E7D-6F2C8B4A3D1E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE
OutputDir=dist
OutputBaseFilename=ChatList-v{#MyAppVersion}-Setup
SetupIconFile=app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}

; Architecture
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Executable file
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Database (install only if doesn't exist)
Source: "chatlist.db"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
; Icons
Source: "app.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.png"; DestDir: "{app}"; Flags: ignoreversion
; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Desktop shortcut (if selected)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Launch program after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Delete logs on uninstall (optional)
Type: filesandordirs; Name: "{app}\logs"

[Code]
// Check for dependencies (if needed)
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

// Save user data during uninstallation
function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  if MsgBox('Do you want to keep the database and settings?', mbConfirmation, MB_YESNO) = IDYES then
  begin
    // Don't delete database on uninstall
    Result := True;
  end
  else
  begin
    // Delete everything including database
    DelTree(ExpandConstant('{app}\chatlist.db'), True, True, True);
    DelTree(ExpandConstant('{app}\logs'), True, True, True);
    Result := True;
  end;
end;
