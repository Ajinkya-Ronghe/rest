@echo off
echo =====================================
echo         CMD SPEED TEST (Download Only)
echo =====================================
echo.

:: 1. Ping Test
echo Checking latency...
ping 8.8.8.8 -n 5
echo.

:: 2. Download Speed Test (1 MB file)
echo Testing download speed...
powershell -Command ^
    "$url='http://speedtest.tele2.net/1MB.zip';" ^
    "$wc=New-Object System.Net.WebClient;" ^
    "$start=Get-Date;" ^
    "$null=$wc.DownloadData($url);" ^
    "$end=Get-Date;" ^
    "$duration=($end - $start).TotalSeconds;" ^
    "$speed = (8 / $duration);" ^
    "Write-Host ('Download Speed: {0:N2} Mbps' -f $speed)"

echo.
echo Test Complete!
pause
