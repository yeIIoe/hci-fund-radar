@echo off
REM =====================================================================
REM HCI FUND Radar — atualizacao diaria dos dados.
REM
REM Ate 24/ago/2026 NADA atualizava este site sozinho. O manter_radar.bat
REM mantinha o SERVIDOR de pe, mas o dado so era refeito quando alguem
REM rodava na mao. Resultado: calendario parado em 23/08, yields parados
REM em 21/08 e projecao parada em 20/08.
REM
REM Ordem importa:
REM   1. update_yields    busca os 2y soberanos novos
REM   2. update_fund      recalcula FUND, ranking e calendario
REM   3. projection_history  grava a projecao por dia nos calendarios
REM   4. update_setups    remapeia BO/ZOI dos candidatos do pre-FUND
REM
REM Idempotente: rodar duas vezes no mesmo dia nao estraga nada.
REM =====================================================================
cd /d "%~dp0"
set "PY=C:\Users\eduar\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if not exist "%PY%" set "PY=python.exe"
set "LOG=%~dp0out_atualiza.log"

echo. >> "%LOG%"
echo ================== %DATE% %TIME% ================== >> "%LOG%"

echo [0/5] tv_yields_nowcast (yield de HOJE via TradingView) >> "%LOG%"
"%PY%" tv_yields_nowcast.py >> "%LOG%" 2>&1
if errorlevel 1 echo    ^>^> FALHOU nowcast (segue com oficial) >> "%LOG%"

REM update_yields e OU/OU: sem flag ele BUSCA e grava yields.json; com
REM --calendario ele so faz o backfill por dia. Precisa dos DOIS, nesta ordem.
echo [1a/5] update_yields (busca) >> "%LOG%"
"%PY%" update_yields.py >> "%LOG%" 2>&1
if errorlevel 1 echo    ^>^> FALHOU update_yields busca >> "%LOG%"

echo [1b/5] update_yields --calendario (backfill) >> "%LOG%"
"%PY%" update_yields.py --calendario >> "%LOG%" 2>&1
if errorlevel 1 echo    ^>^> FALHOU update_yields calendario >> "%LOG%"

echo [2/5] update_fund >> "%LOG%"
"%PY%" update_fund.py >> "%LOG%" 2>&1
if errorlevel 1 echo    ^>^> FALHOU update_fund >> "%LOG%"

echo [3/5] projection_history >> "%LOG%"
"%PY%" projection_history.py >> "%LOG%" 2>&1
if errorlevel 1 echo    ^>^> FALHOU projection_history >> "%LOG%"

echo [4/5] update_setups >> "%LOG%"
"%PY%" update_setups.py >> "%LOG%" 2>&1
if errorlevel 1 echo    ^>^> FALHOU update_setups >> "%LOG%"

echo FIM %DATE% %TIME% >> "%LOG%"
