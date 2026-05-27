@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ================================================
echo 行政执法案卷合规评查与裁量偏差风险控制系统 V1.0
echo ================================================
echo.
echo 正在启动后端服务...
echo.

pip install -r requirements.txt > nul 2>&1

python -m uvicorn app.main:app --host 0.0.0.0 --port 8015 --reload

pause
