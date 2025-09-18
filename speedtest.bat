@echo off
setlocal enabledelayedexpansion

echo =====================================
echo      CMD SPEED ESTIMATION (PING)
echo =====================================
echo.

:: Get average ping value from ping command
for /f "tokens=6 delims== " %%a in ('ping 8.8.8.8 -n 5 ^| find "Average"') do set avg=%%a

:: Remove "ms" from avg value
set avg=%avg:ms=%

echo Average ping to 8.8.8.8: %avg% ms
echo.

:: --- Calculate approximate throughput ---
:: Ping sends 32 bytes (256 bits) per packet
:: Total bits = 5 pings * 256 bits = 1280 bits
set /a total_bits=256*5
set /a total_time_ms=%avg%*5

:: Use PowerShell to compute bits/sec and convert to kbps
for /f %%r in ('powershell -Command "[math]::Round(%total_bits% / (%total_time_ms%/1000),2)"') do set speed_bps=%%r
for /f %%k in ('powershell -Command "[math]::Round(%speed_bps% / 1000,2)"') do set speed_kbps=%%k

echo Approximate network throughput: %speed_kbps% kbps (based on ping packets)
echo.
echo (Very rough estimate – real download speed may differ.)
echo =====================================
pause
