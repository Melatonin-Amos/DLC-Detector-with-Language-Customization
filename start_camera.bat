@echo off
chcp 65001 >nul
echo ========================================
echo   USB摄像头录制程序
echo ========================================
echo.
cd /d "d:\desktop\工程学导论\DLC-Detector-with-Language-Customization"
python scripts/test_camera.py
echo.
echo 程序已退出
pause
