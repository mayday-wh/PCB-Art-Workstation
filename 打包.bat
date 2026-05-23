@echo off
setlocal

cd /d "%~dp0"

set "APP_NAME=PCB_Art_Assistant_v4.1"
set "ENTRY=main.py"
set "ICON_DIR=logo"
set "ICON="
set "DATA_FILE=colors.json"
set "UV_CACHE_DIR=%~dp0.uv-build-cache"
set "UV_PYTHON_INSTALL_DIR=%~dp0.uv-python"

title PCB Art Assistant Build

echo ======================================================
echo           PCB Art Assistant Build Tool
echo ======================================================
echo.

if not exist "%ENTRY%" (
    echo [ERROR] Entry file not found: %ENTRY%
    echo.
    pause
    exit /b 1
)

if not exist "%ICON_DIR%\" (
    echo [ERROR] Icon folder not found: %ICON_DIR%
    echo Put any .ico file into the logo folder and run this script again.
    echo.
    pause
    exit /b 1
)

for %%I in (%ICON_DIR%\*.ico) do (
    set "ICON=%%~fI"
    goto :ICON_FOUND
)

echo [ERROR] No .ico file found in the %ICON_DIR% folder.
echo Put any .ico file into the logo folder and run this script again.
echo.
pause
exit /b 1

:ICON_FOUND
echo [INFO] Icon: %ICON%

echo [INFO] Cleaning old build files...
if exist build rd /s /q build
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"

echo [INFO] Starting PyInstaller via uv...
echo.

uv run --extra build python -m PyInstaller --clean --noconsole --onefile --icon="%ICON%" --name "%APP_NAME%" "%ENTRY%"

echo.
if %errorlevel% neq 0 (
    echo [ERROR] Build failed. Check the output above.
    echo.
    pause
    exit /b 1
) else (
    if exist "%DATA_FILE%" (
        copy /Y "%DATA_FILE%" "dist\%DATA_FILE%" >nul
        echo [INFO] Copied %DATA_FILE% to dist.
    ) else (
        echo [WARN] %DATA_FILE% not found. Include it manually when publishing.
    )
    echo [DONE] Build succeeded: dist\%APP_NAME%.exe
)

echo.
pause
