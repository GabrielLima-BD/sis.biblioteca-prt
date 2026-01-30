@echo off
REM Script para rodar API e App juntos
REM Inicia os dois serviços em paralelo

echo.
echo ================================================================
echo  SISTEMA DE BIBLIOTECA - Iniciando API + APP
echo ================================================================
echo.

REM Definir caminhos relativos ao local deste .bat
set ROOT=%~dp0
set API_PATH=%ROOT%Biblioteca\API
set APP_PATH=%ROOT%Biblioteca\Python

REM Iniciar API em uma nova janela
echo [1/2] Iniciando API Node.js na porta 3000...
start "API - Biblioteca" cmd /k "cd /d ""%API_PATH%"" & node server.js"

REM Aguardar um pouco para a API iniciar
timeout /t 3 /nobreak

REM Iniciar App em outra janela
echo [2/2] Iniciando Launcher (App Python)...
start "APP - Biblioteca" cmd /k "cd /d ""%APP_PATH%"" & python app.py"

echo.
echo ================================================================
echo  SERVICOS INICIADOS!
echo ================================================================
echo.
echo  API: http://localhost:3000
echo  APP: Interface gráfica (janela separada)
echo.
echo  Feche esta janela quando quiser encerrar
echo ================================================================
echo.

pause
