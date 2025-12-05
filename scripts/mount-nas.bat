@echo off
REM Mount NAS share as Z: drive
REM Run as Administrator if needed

echo Mounting NAS share...
net use Z: \\10.10.100.122\docker\GGPNAs\ARCHIVE /user:GGP "!@QW12qw" /persistent:yes

if %ERRORLEVEL% EQU 0 (
    echo NAS mounted successfully as Z: drive
    dir Z:\
) else (
    echo Failed to mount NAS. Error code: %ERRORLEVEL%
    echo Try running this script as Administrator
)

pause
