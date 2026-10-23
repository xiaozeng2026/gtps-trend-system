@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
echo 正在启动人类社会趋势预判系统 (GTPS)...
echo --------------------------------------------------
python run_demo.py
echo.
pause
