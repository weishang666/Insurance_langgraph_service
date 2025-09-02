@echo off

echo 保险业务智能问答服务启动脚本

:: 检查Python是否已安装
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python。请先安装Python并确保已添加到系统PATH中。
    pause
    exit /b 1
)

:: 启动服务
echo 启动保险业务智能问答服务...
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

:: 如果服务意外终止
echo 服务已停止。
pause