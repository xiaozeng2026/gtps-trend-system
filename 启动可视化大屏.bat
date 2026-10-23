@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
echo ====================================================================
echo        全球社会趋势预判系统 · Web 态势感知与推演大屏
echo ====================================================================
echo 正在启动 Web 服务并唤起浏览器 (http://localhost:8501)...
echo.
python -m streamlit run app.py
pause
