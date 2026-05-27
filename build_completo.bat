@echo off
echo ============================================================
echo  Gestion de Obras - Construyendo distribucion completa
echo ============================================================
echo.

echo [1/5] Instalando dependencias de empaquetado...
pip install streamlit pandas altair pyinstaller ^
    --trusted-host pypi.org ^
    --trusted-host files.pythonhosted.org ^
    -q
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias.
    pause & exit /b 1
)

echo.
echo [2/5] Compilando con PyInstaller (puede tardar 5-10 minutos)...
echo       Por favor espera, no cierres esta ventana...
echo.
pyinstaller GestionObras.spec --noconfirm --clean
if errorlevel 1 (
    python -m PyInstaller GestionObras.spec --noconfirm --clean
    if errorlevel 1 (
        echo ERROR: Fallo la compilacion. Revisa los mensajes de arriba.
        pause & exit /b 1
    )
)

echo.
echo [3/5] Limpiando archivos temporales de compilacion...
rmdir /s /q build 2>nul

echo.
echo [4/5] Copiando base de datos con datos actuales...
if exist gestion_obras.db (
    if not exist "dist\GestionObras\datos" mkdir "dist\GestionObras\datos"
    copy /y gestion_obras.db "dist\GestionObras\datos\gestion_obras.db" >nul
    echo       OK - Base de datos copiada con todos los consorcios cargados.
) else (
    echo       AVISO: No se encontro gestion_obras.db.
    echo       Se creara una nueva base de datos al iniciar la app.
)

echo.
echo [5/5] Creando archivo de instrucciones...
(
echo =====================================================
echo  GESTION DE OBRAS - Sistema de Presupuestos y Facturas
echo =====================================================
echo.
echo  COMO USAR:
echo  1. Hacer doble clic en GestionObras.exe
echo  2. Esperar unos segundos hasta que abra el navegador
echo  3. Trabajar normalmente en el navegador
echo.
echo  PARA CERRAR:
echo  - Usar el boton rojo "Cerrar aplicacion" dentro del sistema
echo.
echo  IMPORTANTE:
echo  - No eliminar ninguna carpeta de este directorio
echo  - Los datos se guardan en la carpeta "datos/"
echo  - Hacer backup periodico de la carpeta "datos/"
echo.
echo  Si la app no abre automaticamente, ir a:
echo  http://localhost:8501
echo =====================================================
) > "dist\GestionObras\LEAME.txt"

echo.
echo ============================================================
echo  LISTO!
echo.
echo  Distribucion generada en: dist\GestionObras\
echo.
echo  Para entregar: comprimir TODA la carpeta dist\GestionObras\
echo  en un ZIP y enviarla. El destinatario solo necesita:
echo    1. Descomprimir el ZIP
echo    2. Doble clic en GestionObras.exe
echo.
echo  Peso aproximado: 300-500 MB (normal para una app Python completa)
echo ============================================================
echo.
pause
