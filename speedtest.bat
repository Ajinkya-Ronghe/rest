@echo off
setlocal enabledelayedexpansion

echo =====================================
echo      CMD SPEED ESTIMATION (PING)
echo =====================================
echo.

:: Ping Google DNS and capture average time
for /f "tokens=6 delims== " %%a in ('ping 8.8.8.8 -n 5 ^| find "Average"') do set avg=%%a

echo Average ping to 8.8.8.8: %avg%
echo.

:: Calculate approximate speed:
:: Ping sends 32 bytes -> 256 bits per packet.
:: 5 pings = 1280 bits total.
:: Time = avg ms per ping * 5 pings.
:: Speed (bps) = total_bits / total_time_seconds.

set /a total_bits=256*5
set /a total_time_ms=%avg%*5
:: Convert ms to seconds using PowerShell
for /f %%s in ('powershell -Command "%total_time_ms% / 1000"') do set total_time_sec=%%s

for /f %%r in ('powershell -Command "[math]::Round(%total_bits% / %total_time_sec%,2)"') do set speed_bps=%%r

:: Convert bps to kbps
for /f %%k in ('powershell -Command "[math]::Round(%speed_bps% / 1000,2)"') do set speed_kbps=%%k

echo Approximate network throughput: %speed_kbps% kbps (based on ping packets)
echo.
echo (This is a very rough estimate — real download speed will differ.)
echo =====================================
pause
