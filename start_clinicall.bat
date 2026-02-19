@echo off
echo Starting CliniCall...

:: Start Uvicorn Server in a new window (Using absolute path)
start "CliniCall Server" powershell -NoExit -Command "uvicorn app.main:app --host 127.0.0.1 --port 8000"

:: Wait for server to initialize
timeout /t 5

:: Start Ngrok Tunnel in a new window (Using absolute path found in WinGet cache)
:: Note: This path is specific to your current installation. If you reinstall ngrok, please update this path.
start "CliniCall Tunnel" powershell -NoExit -Command "ngrok http --url=genevive-noncultured-unexpansively.ngrok-free.dev 8000"

echo.
echo Application started! 
echo Check the new windows for status.
echo.
pause
