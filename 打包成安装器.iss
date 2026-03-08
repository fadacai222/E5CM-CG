#define AppName "E舞成名重构版"
#define AppVersion "1.0.0"
#define AppPublisher "liang"
#define AppExeName "E5CM-CG.exe"

[Setup]
AppId={{9E0B6D5E-6A56-4D7B-BE4C-1F6B2C8A9E11}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=E5CM-CG_Setup
SetupIconFile=icon\自解压安装器.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}
DefaultDirName={userdocs}\{#AppName}
PrivilegesRequired=lowest

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"

[Files]
Source: "编译结果\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "编译结果\songs\*"; DestDir: "{app}\songs"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\卸载 {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "立即启动 {#AppName}"; Flags: nowait postinstall skipifsilent