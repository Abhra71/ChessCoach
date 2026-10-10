; Inno Setup script: the Chess Coach installer (Next, Next, Finish; no admin rights needed).
; Build:  "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer\ChessCoach.iss
; Needs dist\ChessCoach from:  python -m PyInstaller installer\ChessCoach.spec --noconfirm

#define AppVersion "0.3.0"

[Setup]
AppId={{6F2C8E3A-4B1D-4C7E-9A35-2D8B7F1E0C64}
AppName=Chess Coach
AppVersion={#AppVersion}
AppVerName=Chess Coach {#AppVersion} (beta)
AppPublisher=Chess Coach (open source)
AppPublisherURL=https://github.com/Abhra71/ChessCoach
AppSupportURL=https://github.com/Abhra71/ChessCoach/issues
DefaultDirName={localappdata}\Programs\ChessCoach
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=ChessCoach-Setup-{#AppVersion}
SetupIconFile=ChessCoach.ico
UninstallDisplayIcon={app}\ChessCoach.exe
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
CloseApplications=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "autostart"; Description: "Start Chess Coach with Windows (recommended: it checks each new game by itself)"
Name: "desktopicon"; Description: "Desktop shortcut"; Flags: unchecked

[Files]
Source: "..\dist\ChessCoach\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\extension\*"; DestDir: "{app}\extension"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\Chess Coach"; Filename: "{app}\ChessCoach.exe"; AppUserModelID: "Abhra71.ChessCoach"
Name: "{userdesktop}\Chess Coach"; Filename: "{app}\ChessCoach.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "ChessCoach"; \
  ValueData: """{app}\ChessCoach.exe"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\ChessCoach.exe"; Description: "Start Chess Coach now"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/IM ChessCoach.exe /F"; Flags: runhidden; RunOnceId: "StopCoach"

[Messages]
WelcomeLabel2=This will install Chess Coach {#AppVersion} (beta).%n%nIt looks at your finished chess.com games, finds the habits that cost you games, and trains you out of them.%n%nFair play: it is never active during a game against a real person.
FinishedLabel=Chess Coach is installed. It lives as an icon by the clock and opens a welcome page where you enter your chess.com username.
