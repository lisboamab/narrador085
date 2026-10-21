@echo off
rem Atalho: narrar gerar posts\  ==  .venv\Scripts\python.exe narrar.py gerar posts\
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Ambiente nao instalado. Rode primeiro: powershell -ExecutionPolicy Bypass -File instalar.ps1 1>&2
    exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0narrar.py" %*
