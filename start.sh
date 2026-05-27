#!/bin/bash
# admin-law-review 启动脚本
SCRIPT_DIR=""
cd ""

VENV_DIR="/.venv"
if [ ! -d "" ]; then
    python3 -m venv ""
fi
source "/bin/activate"

pip install -q fastapi uvicorn pydantic python-dotenv loguru 2>/dev/null

echo "[admin-law-review] 启动服务..."
cd /mnt/d/ZYY Project/admin-law-review/backend/app && python3 main.py
