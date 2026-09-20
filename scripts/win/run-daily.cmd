@echo off
rem ============================================================================
rem  Worker for the "create one WeChat draft" scheduled task.
rem
rem  Runs `python main.py daily`, which executes src/scheduler.run_once():
rem  fetch news -> generate article -> gradient cover -> create WeChat DRAFT.
rem
rem  HARD RULE (AGENTS.md): drafts only. publish_draft() (mass send) is never
rem  called from here. The operator reviews and sends manually if at all.
rem
rem  Why a wrapper is needed:
rem    1. Task Scheduler has no "start in" option -- cd explicitly, otherwise
rem       .env / config.yaml cannot be found.
rem    2. Task Scheduler does not inherit the interactive PATH -- locate the
rem       interpreter by absolute path instead of trusting "python".
rem    3. Output must go to a file, or a failure leaves no trace at all.
rem
rem  Usage:  run-daily.cmd            -> python main.py daily   (draft creation)
rem          run-daily.cmd config     -> python main.py config (smoke test)
rem  Exit codes: 0 ok / 1 pipeline failed / 127 environment error
rem
rem  NOTE: kept ASCII-only on purpose. cmd.exe re-reads batch files by byte
rem        offset, so multi-byte characters break depending on the code page.
rem ============================================================================
setlocal EnableExtensions

rem Project root = two levels above scripts\win\ (%~dp0 already ends with a slash)
for %%I in ("%~dp0..\..") do set "PROJECT_DIR=%%~fI"

set "LOG_DIR=%PROJECT_DIR%\logs"
set "LOG_FILE=%LOG_DIR%\daily-publish.log"
set "MAX_LOG_BYTES=1048576"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" 2>nul

rem --- Log rotation: archive once past 1MB so it cannot grow forever ---
if exist "%LOG_FILE%" (
  for %%A in ("%LOG_FILE%") do if %%~zA GTR %MAX_LOG_BYTES% (
    if exist "%LOG_FILE%.1" del /q "%LOG_FILE%.1" 2>nul
    move /y "%LOG_FILE%" "%LOG_FILE%.1" >nul 2>&1
  )
)

rem --- Locate python ---
rem Order matters: real installs are probed FIRST. "where python" alone is not
rem reliable because on this machine it resolves to the Microsoft Store alias
rem (%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe), which is a 0-byte stub
rem that exits with code 9009 instead of running Python.
if not defined PYTHON_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if not defined PYTHON_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not defined PYTHON_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PYTHON_EXE if exist "%ProgramFiles%\Python311\python.exe" set "PYTHON_EXE=%ProgramFiles%\Python311\python.exe"
if not defined PYTHON_EXE (
  for /f "delims=" %%I in ('where python 2^>nul') do (
    echo %%I | find /i "WindowsApps" >nul || if not defined PYTHON_EXE set "PYTHON_EXE=%%I"
  )
)

if not defined PYTHON_EXE (
  >>"%LOG_FILE%" echo [unknown-time] ERROR: python.exe not found. Set PYTHON_EXE for this task.
  endlocal & exit /b 127
)

if not exist "%PROJECT_DIR%\main.py" (
  >>"%LOG_FILE%" echo [unknown-time] ERROR: %PROJECT_DIR%\main.py not found.
  endlocal & exit /b 127
)

rem --- Locale-independent ASCII timestamp (%%DATE%% is GBK on Chinese Windows) ---
set "TS="
for /f "delims=" %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH:mm:ss" 2^>nul') do set "TS=%%I"
if not defined TS set "TS=unknown-time"

rem Optional subcommand passthrough, defaults to the draft pipeline
set "ARGS=%*"
if not defined ARGS set "ARGS=daily"

rem The cd is essential -- without it .env / config.yaml cannot be read
cd /d "%PROJECT_DIR%"

>>"%LOG_FILE%" echo.
>>"%LOG_FILE%" echo ============================================================
>>"%LOG_FILE%" echo [%TS%] python main.py %ARGS%  (python: %PYTHON_EXE%)

"%PYTHON_EXE%" main.py %ARGS% >>"%LOG_FILE%" 2>&1
set "RC=%ERRORLEVEL%"

>>"%LOG_FILE%" echo [%TS%] finished, exit code %RC%
if "%RC%"=="0" >>"%LOG_FILE%" echo status: OK (draft created, or nothing to do)
if "%RC%"=="1" >>"%LOG_FILE%" echo status: FAILED - see details above
if "%RC%"=="127" >>"%LOG_FILE%" echo status: ENVIRONMENT ERROR - python or main.py not found

endlocal & exit /b %RC%
