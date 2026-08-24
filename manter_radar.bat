@echo off
REM HCI FUND Radar — mantem o painel de pe.
REM
REM Instancia unica pela trava de arquivo: o handle 9 fica ABERTO enquanto o laco
REM roda, entao uma segunda copia nao consegue abrir o mesmo arquivo e desiste.
REM
REM BUG QUE DERRUBAVA O PAINEL (22/ago/2026): a linha da trava usava "2>/dev/null".
REM No Windows o dispositivo nulo e "nul"; "/dev/null" faz o cmd tentar criar a
REM pasta \dev, falhar, e o "|| exit /b 1" matava o script na PRIMEIRA linha.
REM O painel nunca chegava a subir no logon.
cd /d "%~dp0"
set "TRAVA=%TEMP%\hci_radar.lock"
2>nul ( 9>"%TRAVA%" ( call :principal ) ) || ( exit /b 1 )
exit /b

:principal
set "PY=C:\Users\eduar\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe"
if not exist "%PY%" set "PY=pythonw.exe"
:loop
netstat -ano | findstr /C:"127.0.0.1:8765" | findstr /C:"LISTENING" >nul
if errorlevel 1 (
    start "" "%PY%" "%~dp0serve_fund.py" --no-browser
    REM ping em vez de timeout: timeout morre quando o console esta oculto
    ping -n 11 127.0.0.1 >nul
) else (
    ping -n 31 127.0.0.1 >nul
)
goto loop
