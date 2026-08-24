@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "HCI_PYTHON=C:\Users\eduar\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if exist "%HCI_PYTHON%" goto run
where py >nul 2>nul
if errorlevel 1 goto missing
py -3 serve_fund.py
goto end
:run
"%HCI_PYTHON%" serve_fund.py
goto end
:missing
echo Python nao encontrado. Avise o Codex para corrigir o atalho.
:end
pause
