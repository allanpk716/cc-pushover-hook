@echo off
REM Test CLAUDE_PROJECT_DIR environment variable
REM This script validates that the hook path configuration works correctly

echo ========================================
echo Testing CLAUDE_PROJECT_DIR
echo ========================================

if "%CLAUDE_PROJECT_DIR%"=="" (
    echo [ERROR] CLAUDE_PROJECT_DIR is not set
    echo This means the script is not running from a Claude Code hook
    goto :manual_test
)

echo [OK] CLAUDE_PROJECT_DIR = %CLAUDE_PROJECT_DIR%

if not exist "%CLAUDE_PROJECT_DIR%" (
    echo [ERROR] Project directory does not exist: %CLAUDE_PROJECT_DIR%
    exit /b 1
)

echo [OK] Project directory exists

set HOOK_SCRIPT=%CLAUDE_PROJECT_DIR%\.claude\hooks\pushover-hook\pushover-notify.py

if not exist "%HOOK_SCRIPT%" (
    echo [ERROR] Hook script not found: %HOOK_SCRIPT%
    exit /b 1
)

echo [OK] Hook script exists: %HOOK_SCRIPT%
echo ========================================
echo [SUCCESS] All tests passed!
echo ========================================
exit /b 0

:manual_test
echo ========================================
echo Manual Test Mode
echo ========================================
echo Current directory: %CD%

REM Check if we're in the project directory
if not exist ".claude\settings.json" (
    echo [ERROR] .claude\settings.json not found in current directory
    echo Please run this script from the project root
    exit /b 1
)

echo [OK] Found .claude\settings.json in current directory

REM Set CLAUDE_PROJECT_DIR to current directory for testing
set CLAUDE_PROJECT_DIR=%CD%

echo [INFO] Set CLAUDE_PROJECT_DIR = %CLAUDE_PROJECT_DIR%

set HOOK_SCRIPT=%CLAUDE_PROJECT_DIR%\.claude\hooks\pushover-hook\pushover-notify.py

if not exist "%HOOK_SCRIPT%" (
    echo [ERROR] Hook script not found: %HOOK_SCRIPT%
    exit /b 1
)

echo [OK] Hook script exists: %HOOK_SCRIPT%
echo ========================================
echo [SUCCESS] Manual test passed!
echo The hook path configuration is correct
echo ========================================
exit /b 0
