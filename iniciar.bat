@echo off
REM ============================================================
REM  Gambiarra-Infinite  -  launcher Windows
REM  Toda a logica fica em iniciar.py (igual em todos os SO).
REM  Aqui so: tela cheia, codepage e chamar o Python.
REM ============================================================
setlocal

REM fonte menor + janela maximizada (persistente no perfil do usuario)
for %%K in ("HKCU\Console\%%SystemRoot%%_system32_cmd.exe" "HKCU\Console\Gambiarra-Infinite") do (
    reg add %%~K /v FaceName /t REG_SZ /d "Consolas" /f >nul 2>nul
    reg add %%~K /v FontSize /t REG_DWORD /d 0x000C0000 /f >nul 2>nul
    reg add %%~K /v FontFamily /t REG_DWORD /d 54 /f >nul 2>nul
    reg add %%~K /v ScreenBufferSize /t REG_DWORD /d 0x003C00C8 /f >nul 2>nul
    reg add %%~K /v WindowSize /t REG_DWORD /d 0x003600C8 /f >nul 2>nul
    REM QuickEdit ligado: permite SELECIONAR com o mouse e Ctrl+C.
    REM O app pausa o desenho quando o console entra em modo selecao.
    reg add %%~K /v QuickEdit /t REG_DWORD /d 1 /f >nul 2>nul
)

REM primeira execucao: reabre maximizado para pegar a fonte nova
if /i not "%~1"=="__READY__" (
    start "Gambiarra-Infinite" /MAX cmd /c ""%~f0" __READY__"
    exit /b 0
)

chcp 65001 >nul
title Gambiarra-Infinite
cd /d "%~dp0"

REM ---- dimensiona o console ----
REM O buffer e a janela precisam ser grandes; o iniciar.py mede a
REM largura REAL depois de maximizar e ajusta sozinho. Fixar 118 aqui
REM deixava o app desenhando no canto esquerdo em telas grandes.
mode con cols=200 lines=60 >nul 2>nul

REM ---- acha o Python (iniciar.py cuida do resto) ----
set "PY="
for %%V in (313 312 311 310 39) do (
    if not defined PY (
        py -%%V -c "import sys" >nul 2>nul && set "PY=py -%%V"
    )
)
if not defined PY (
    python -c "import sys" >nul 2>nul && set "PY=python"
)
if not defined PY (
    python3 -c "import sys" >nul 2>nul && set "PY=python3"
)
if not defined PY (
    echo.
    echo   Python 3.9+ nao encontrado.
    echo   Instale em https://python.org/downloads
    echo   e marque "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)

%PY% -u -X utf8 "iniciar.py" %*
if errorlevel 1 pause
endlocal
