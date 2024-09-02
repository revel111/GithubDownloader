@echo off

SET SHORTCUT_NAME=auto_updater.lnk
SET STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
SET SHORTCUT_PATH=%STARTUP_FOLDER%\%SHORTCUT_NAME%

IF EXIST "%SHORTCUT_PATH%" (
    DEL "%SHORTCUT_PATH%"
    echo The app has been removed from the startup.
) ELSE (
    echo The app was not found in the startup.
)

pause