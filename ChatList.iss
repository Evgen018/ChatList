; Скрипт Inno Setup для установки ChatList
; Версия берётся из version.py

#define MyAppName "ChatList"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "ChatList Team"
#define MyAppURL "https://github.com/Evgen018/ChatList"
#define MyAppExeName "ChatList-v1.0.0.exe"

[Setup]
; Основная информация о приложении
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

; Архитектура
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Исполняемый файл
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; База данных (если нужно установить с чистой БД)
Source: "chatlist.db"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
; Иконки
Source: "app.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.png"; DestDir: "{app}"; Flags: ignoreversion
; Документация
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Создание ярлыков в меню "Пуск"
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Создание ярлыка на рабочем столе (если выбрано)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Запустить программу после установки
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Удаление логов и настроек при деинсталляции (опционально)
Type: filesandordirs; Name: "{app}\logs"

[Code]
// Проверка наличия .NET Framework или других зависимостей (если нужно)
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

// Сохранение пользовательских данных при деинсталляции
function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  if MsgBox('Вы хотите сохранить базу данных и настройки?', mbConfirmation, MB_YESNO) = IDYES then
  begin
    // Не удаляем базу данных при деинсталляции
    Result := True;
  end
  else
  begin
    // Удаляем всё, включая базу данных
    DelTree(ExpandConstant('{app}\chatlist.db'), True, True, True);
    DelTree(ExpandConstant('{app}\logs'), True, True, True);
    Result := True;
  end;
end;
