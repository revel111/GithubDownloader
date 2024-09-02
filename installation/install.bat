@echo off

pip3 install -r requirements.txt

SET SCRIPT_NAME=auto_updater.pyw
SET SCRIPT_PATH=%~dp0..\%SCRIPT_NAME%
SET SHORTCUT_NAME=auto_updater.lnk
SET STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
SET SHORTCUT_PATH=%STARTUP_FOLDER%\%SHORTCUT_NAME%

powershell -command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath='%SCRIPT_PATH%'; $s.Save()"

echo The installation is successful.

pause