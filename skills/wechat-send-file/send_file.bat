@echo off
chcp 65001 >nul
echo 微信文件发送自动化脚本
echo ========================

if "%~1"=="" (
    echo 用法: %~n0 "把[文件路径]的文件用微信给[用户名]"
    echo 示例: %~n0 "把C:\Users\Administrator\Desktop\report.docx的文件用微信给可乐煮鸡"
    echo 示例: %~n0 "用微信给张三发送D:\work\project.pdf的文件"
    pause
    exit /b 1
)

set "MESSAGE=%~1"

echo 正在执行: %MESSAGE%
echo.

rem 检查Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

rem 检查依赖
python -c "import pyautogui, pyperclip, PIL" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  缺少Python依赖，正在安装...
    pip install pyautogui pillow pyperclip
    echo.
)

rem 执行脚本
python wechat_send_file.py --message "%MESSAGE%" --debug

echo.
echo 脚本执行完成
if %errorlevel% equ 0 (
    echo ✅ 成功
) else (
    echo ❌ 失败
)

pause