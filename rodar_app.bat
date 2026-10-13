@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

title Tradutor Visual

REM ==========================================
REM Localiza o Python (prefere o launcher "py")
REM ==========================================
set "PYTHON="
where py >nul 2>nul && set "PYTHON=py -3"
if not defined PYTHON (
    where python >nul 2>nul && set "PYTHON=python"
)
if not defined PYTHON (
    echo [ERRO] Python nao encontrado.
    echo Instale em https://www.python.org/downloads/ e marque "Add Python to PATH".
    pause
    exit /b 1
)

REM ==========================================
REM Cria o ambiente virtual na primeira execucao
REM ==========================================
if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    %PYTHON% -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar o ambiente virtual.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"

REM ==========================================
REM Instala dependencias (so na primeira vez
REM ou quando o requirements.txt mudar)
REM ==========================================
set "MARCADOR=.venv\.instalado"
set "PRECISA_INSTALAR="
if not exist "%MARCADOR%" set "PRECISA_INSTALAR=1"
if exist "%MARCADOR%" (
    fc /b requirements.txt "%MARCADOR%" >nul 2>nul || set "PRECISA_INSTALAR=1"
)

if defined PRECISA_INSTALAR (
    echo Instalando dependencias - pode demorar alguns minutos na primeira vez...
    python -m pip install --upgrade pip
    REM PyTorch versao CPU: bem menor que a versao com CUDA
    python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    if errorlevel 1 goto :erro_instalacao
    python -m pip install -r requirements.txt
    if errorlevel 1 goto :erro_instalacao
    copy /y requirements.txt "%MARCADOR%" >nul
)

REM ==========================================
REM Inicia o app (abre o navegador sozinho)
REM ==========================================
echo.
echo Iniciando o app em http://localhost:8501
echo Para encerrar, feche esta janela ou pressione Ctrl+C.
echo.
python -m streamlit run app_image_translator.py
pause
exit /b 0

:erro_instalacao
echo [ERRO] Falha ao instalar as dependencias. Verifique sua conexao com a internet.
pause
exit /b 1
