@echo off
REM Simulate Claude Code hook execution with CLAUDE_PROJECT_DIR
REM This validates that the actual hook command will work

setlocal

REM Set the project directory (Claude Code will set this automatically)
set CLAUDE_PROJECT_DIR=C:\WorkSpace\cc-pushover-hook

echo ========================================
echo Simulating Claude Code Hook Execution
echo ========================================
echo CLAUDE_PROJECT_DIR = %CLAUDE_PROJECT_DIR%
echo.

REM Set encoding and run the Python script
set PYTHONIOENCODING=utf-8
py "%CLAUDE_PROJECT_DIR%\.claude\hooks\pushover-hook\pushover-notify.py"

echo.
echo ========================================
echo Hook command executed with exit code: %ERRORLEVEL%
echo ========================================

endlocal
