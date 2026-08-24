@echo off
REM Refresh LEVE de hora em hora: so o nowcast do TradingView + o painel de
REM yields do site. A cadeia PESADA (FUND, calendarios, projecao, setups)
REM continua 2x/dia na HCI_FUND_Radar_Update — recalcular ranking de 25 anos
REM de hora em hora seria desperdicio; o que precisa ser fresco a todo momento
REM e o JURO, e e isso que este passo entrega.
cd /d "%~dp0"
set "PY=C:\Users\eduar\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if not exist "%PY%" set "PY=python.exe"
"%PY%" tv_yields_nowcast.py >> "%~dp0out_nowcast_leve.log" 2>&1
"%PY%" update_yields.py >> "%~dp0out_nowcast_leve.log" 2>&1
