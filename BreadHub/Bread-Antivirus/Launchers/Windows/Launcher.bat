@echo off
title BreadAv Launcher

:: Optional ASCII logo
echo  /$$$$$$$                                      /$$  /$$$$$$
echo | $$__  $$                                    | $$ /$$__  $$
echo | $$  \ $$  /$$$$$$   /$$$$$$   /$$$$$$   /$$$$$$$| $$  \ $$ /$$    /$$
echo | $$$$$$$  /$$__  $$ /$$__  $$ |____  $$ /$$__  $$| $$$$$$$$|  $$  /$$/
echo | $$__  $$| $$  \__/| $$$$$$$$  /$$$$$$$| $$  | $$| $$__  $$ \  $$/$$/
echo | $$  \ $$| $$      | $$_____/ /$$__  $$| $$  | $$| $$  | $$  \  $$$/
echo | $$$$$$$/| $$      |  $$$$$$$|  $$$$$$$|  $$$$$$$| $$  | $$   \  $/
echo |_______/ |__/       \_______/ \_______/ \_______/|__/  |__/    \_/
echo.

:menu
set /p cmd="Type /start or /quit: "
if /i "%cmd%"=="/start" (
    python "C:\Users\%USERNAME%\Desktop\Bread-Antivirus\BreadAv-v0.9.9.py"
    goto menu
) else if /i "%cmd%"=="/quit" (
    echo Exiting...
    pause >nul
    exit
) else (
    echo Unknown command. Use /start or /quit.
    goto menu
)
