@echo off
REM 微信消息自动化批处理文件
REM 用法: send_message.bat "用微信给可乐煮鸡发今天不吃饭"

setlocal enabledelayedexpansion

echo ============================================
echo 微信消息自动化工具 - Python版本
echo ============================================

REM 检查是否提供了参数
if "%~1"=="" (
    echo 错误: 请提供要发送的消息
    echo 用法: %~nx0 "用微信给用户名发消息内容"
    echo 示例: %~nx0 "用微信给可乐煮鸡发今天不吃饭"
    pause
    exit /b 1
)

REM 提取参数
set "message=%~1"
echo 消息内容: %message%

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

REM 检查是否安装了必要的包
echo 检查Python依赖包...
python -c "import pyautogui" >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到pyautogui库
    echo 请运行: pip install pyautogui
    pause
    exit /b 1
)

python -c "from PIL import Image" >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Pillow库
    echo 请运行: pip install pillow
    pause
    exit /b 1
)

python -c "import pyperclip" >nul 2>&1
if errorlevel 1 (
    echo 警告: 未找到pyperclip库，将尝试其他剪贴板方法
)

REM 准备警告信息
echo.
echo ============================================
echo 注意: 即将执行真实微信操作
echo 请确保:
echo 1. 微信桌面客户端已打开并登录
echo 2. 已准备好要发送的消息
echo 3. 微信窗口未被最小化
echo ============================================
echo.
echo 系统将在5秒后开始执行...
echo 按Ctrl+C可以取消操作

REM 等待5秒
timeout /t 5 /nobreak >nul

REM 运行Python脚本
echo.
echo 开始执行微信消息发送...
python wechat_auto_message.py --user "%message%" --debug

REM 根据退出代码显示结果
if errorlevel 0 (
    echo.
    echo ============================================
    echo 微信消息发送流程已成功执行！
    echo ============================================
) else (
    echo.
    echo ============================================
    echo 微信消息发送流程执行失败！
    echo 请检查错误信息并重试。
    echo ============================================
)

echo.
pause