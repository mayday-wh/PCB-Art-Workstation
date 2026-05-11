@echo off
setlocal
:: 强制设置 CMD 窗口为 UTF-8 编码，防止中文显示乱码
chcp 65001 >nul

:: 切换到脚本所在目录，确保路径正确
cd /d "%~dp0"

set APP_NAME=PCB_Art_Assistant_v4.0
set ENTRY=main.py
set ICON=logo.ico
set DATA_FILE=colors.json
set UV_CACHE_DIR=%~dp0.uv-build-cache
set UV_PYTHON_INSTALL_DIR=%~dp0.uv-python

title PCB 艺术助手打包工具

echo ======================================================
echo           PCB 艺术助手 自动化打包程序
echo ======================================================
echo.

if not exist "%ENTRY%" (
    echo ❌ 未找到入口文件：%ENTRY%
    echo.
    pause
    exit /b 1
)

if not exist "%ICON%" (
    echo ❌ 未找到图标文件：%ICON%
    echo 请把 logo.ico 放到当前目录后再打包。
    echo.
    pause
    exit /b 1
)

echo [状态] 正在清理旧的构建缓存...
if exist build rd /s /q build
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"

echo [状态] 正在启动 PyInstaller (通过 uv)...
echo.

:: 通过 build 额外依赖运行 PyInstaller，避免脚本入口路径解析失败
uv run --extra build python -m PyInstaller --clean --noconsole --onefile --icon="%ICON%" --name "%APP_NAME%" "%ENTRY%"

echo.
if %errorlevel% neq 0 (
    echo ❌ 打包失败，请检查上方报错信息。
    echo.
    pause
    exit /b 1
) else (
    if exist "%DATA_FILE%" (
        copy /Y "%DATA_FILE%" "dist\%DATA_FILE%" >nul
        echo [状态] 已复制色卡数据库到 dist\%DATA_FILE%
    ) else (
        echo [提醒] 未找到 %DATA_FILE%，发布时请手动携带色卡数据库。
    )
    echo ✅ 打包成功！程序已生成：dist\%APP_NAME%.exe
)

echo.
pause
