@echo off
title Consulta de Veiculos - DetranRS
cd /d "%~dp0"

echo =======================================================
echo     Iniciando Consulta de Veiculos - DetranRS
echo =======================================================
echo.
echo Aguarde... Abrindo aplicacao no navegador (Porta 8503).
echo Para fechar a aplicacao, basta fechar esta janela.
echo.

py -m streamlit run app.py --server.port 8503
if %errorlevel% equ 0 goto fim

"%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" -m streamlit run app.py --server.port 8503
if %errorlevel% equ 0 goto fim

python -m streamlit run app.py --server.port 8503
if %errorlevel% equ 0 goto fim

echo.
echo =======================================================
echo [ERRO] Nao foi possivel iniciar a aplicacao.
echo =======================================================
echo.
pause

:fim
