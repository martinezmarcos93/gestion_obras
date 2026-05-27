@echo off
echo ============================================================
echo  Generando GestionObras.exe
echo ============================================================
echo.

echo [1/3] Instalando PyInstaller...
pip install pyinstaller --trusted-host pypi.org --trusted-host files.pythonhosted.org -q
if errorlevel 1 (
    echo ERROR: No se pudo instalar PyInstaller.
    pause
    exit /b 1
)

echo [2/3] Compilando launcher.py...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "GestionObras" ^
    --distpath "." ^
    --workpath "build_tmp" ^
    --specpath "build_tmp" ^
    launcher.py

if errorlevel 1 (
    echo ERROR: Fallo la compilacion.
    pause
    exit /b 1
)

echo [3/3] Limpiando archivos temporales...
rmdir /s /q build_tmp 2>nul

echo.
echo ============================================================
echo  Listo! Archivo generado: GestionObras.exe
echo.
echo  El .exe debe estar en la misma carpeta que app.py
echo  (ya esta en el lugar correcto)
echo ============================================================
echo.
pause
