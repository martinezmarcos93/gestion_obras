@echo off
echo ========================================
echo  Gestion de Obras - Iniciando sistema...
echo ========================================

REM Instalar dependencias si no están
pip install -r requirements.txt --quiet

REM Iniciar la aplicacion
streamlit run app.py

pause
