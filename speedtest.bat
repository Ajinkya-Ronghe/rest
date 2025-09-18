@echo off
setlocal enabledelayedexpansion

:: ======= SETTINGS =======
set "PING_COUNT=10"      :: how many echo requests per host
set "PACKET_SIZE=32"     :: bytes per ping (default 32)
:: ========================

set "HOSTS=8.8.8.8 1.1.1.1 8.8.4.4"

echo =========================================
echo      PING-BASED SPEED ESTIMATOR (CMD)
echo =========================================
echo Pings per host : %PING_COUNT%
echo Packet size    : %PACKET_SIZE% bytes
echo Hosts          : %HOSTS%
echo.

set /a totalAvgMs=0, hostCount=0, bestKbpsScaled=0
set "bestHost="

for %%H in (%HOSTS%) do (
  echo --- Testing %%H ---
  for /f "delims=" %%L in ('ping -n %PING_COUNT% -l %PACKET_SIZE% %%H ^| find "Average"') do set "line=%%L"

  if not defined line (
    echo   No summary found (host unreachable or blocked).
    echo.
    set "line="
    rem continue to next host
    goto :continueHost
  )

  rem Extract the "Average = Xms" segment from the summary line
  for /f "tokens=3 delims=," %%A in ("!line!") do set "seg=%%A"
  for /f "tokens=2 delims==" %%B in ("!seg!") do set "avgRaw=%%B"

  rem Clean up: remove spaces and "ms"
  set "avg=!avgRaw: =!"
  set "avg=!avg:ms=!"

  if "!avg!"=="" (
    echo   Could not parse average latency.
    echo.
    set "line="
    goto :continueHost
  )

  rem Compute rough throughput (kbps) from ping:
  rem Speed_kbps ≈ (PACKET_SIZE * 8) / avg_ms
  rem We'll keep 2 decimals by scaling *100
  set /a kbpsScaled=(%PACKET_SIZE%*800)/!avg!

  set /a whole=!kbpsScaled!/100
  set /a frac=!kbpsScaled!%%100
  if !frac! LSS 10 set "frac=0!frac!"

  echo   Average latency : !avg! ms
  echo   Est. throughput : !whole!.!frac! kbps  (ping-based)
  echo.

  set /a totalAvgMs+=avg
  set /a hostCount+=1

  if !kbpsScaled! GTR !bestKbpsScaled! (
    set "bestKbpsScaled=!kbpsScaled!"
    set "bestHost=%%H"
  )

  :continueHost
  set "line="
)

echo =========================================
if %hostCount% GTR 0 (
  set /a overallAvgMs=totalAvgMs/hostCount
  set /a bestWhole=bestKbpsScaled/100
  set /a bestFrac=bestKbpsScaled%%100
  if !bestFrac! LSS 10 set "bestFrac=0!bestFrac!"

  echo Overall avg latency across %hostCount% host(s): !overallAvgMs! ms
  echo Best host by est. throughput               : %bestHost%  (!bestWhole!.!bestFrac! kbps)
) else (
  echo No successful ping summaries to compute results.
)
echo =========================================
echo Note: This estimates throughput from ICMP latency only.
echo       It is NOT a real bandwidth test.
echo =========================================

pause
