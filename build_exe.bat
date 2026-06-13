@echo off
chcp 65001 >nul

echo ========================================
echo   AI-Operating-Wechat 一键打包
echo ========================================
echo.

:: 检查依赖
where pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [1/3] 安装 pyinstaller...
    pip install pyinstaller -q
) else (
    echo [1/3] pyinstaller 已就绪
)

:: 清理旧构建
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /f /q *.spec 2>nul

echo [2/3] 打包中...（约 2-3 分钟）
echo.

pyinstaller --onefile --console ^
    --name "AI-Operating-Wechat" ^
    --add-data "act;act" ^
    --add-data "chat;chat" ^
    --add-data "images;images" ^
    --add-data "voices;voices" ^
    --hidden-import uiautomation ^
    --hidden-import PIL._tkinter_finder ^
    --hidden-import dashscope ^
    --hidden-import sounddevice ^
    --hidden-import numpy ^
    --collect-all dashscope ^
    --collect-all uiautomation ^
    main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 打包失败！查看上方错误信息。
    pause
    exit /b 1
)

echo [3/3] 整理发布包...

:: 创建发布目录
set RELEASE_DIR=AI-Operating-Wechat_v1.0
if exist %RELEASE_DIR% rmdir /s /q %RELEASE_DIR%
mkdir %RELEASE_DIR% >nul 2>&1

:: 移动 exe
move dist\AI-Operating-Wechat.exe %RELEASE_DIR% >nul 2>&1

:: 复制 config（外置，方便修改 API Key）
copy config.py %RELEASE_DIR% >nul 2>&1

:: 清理构建缓存
rd /s /q build 2>nul
rd /s /q dist 2>nul

:: 创建使用说明
> %RELEASE_DIR%\使用说明.txt (
echo AI-Operating-Wechat v1.0 - 微信自动回复工具
echo.
echo === 使用方法 ===
echo 1. 用记事本打开 config.py，填写你的阿里云 API Key
echo 2. 右键 AI-Operating-Wechat.exe - 以管理员身份运行
echo 3. 打开微信聊天窗口，程序会自动检测并回复
echo.
echo === 注意事项 ===
echo - 必须「以管理员身份运行」（操作微信 UI 需要）
echo - config.py 可随时修改，无需重新打包
echo - 首次运行会自动创建 voices/temp 和 images/temp
)

echo.
echo ========================================
echo   ✅ 打包完成！
echo ========================================
echo.
echo 发布包: %RELEASE_DIR%\
echo.
dir /b %RELEASE_DIR%
echo.
echo 把 %RELEASE_DIR% 文件夹拷贝到目标电脑即可运行。
echo.
pause
