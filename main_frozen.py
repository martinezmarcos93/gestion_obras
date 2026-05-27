"""
Punto de entrada para el ejecutable PyInstaller.
Inicia el servidor Streamlit dentro del mismo proceso y abre el navegador.
"""
from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

PORT = 8501


def _abrir_navegador():
    time.sleep(4)
    webbrowser.open(f"http://localhost:{PORT}")


def _mostrar_error(mensaje: str):
    """Muestra un error visual si algo falla al iniciar."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Error — Gestión de Obras",
            f"No se pudo iniciar la aplicación:\n\n{mensaje}\n\n"
            "Contactá al soporte técnico.",
        )
        root.destroy()
    except Exception:
        pass


def main():
    try:
        if getattr(sys, "frozen", False):
            base = Path(sys._MEIPASS)
            # Cambiar al directorio de la app para que Streamlit encuentre
            # .streamlit/config.toml y los archivos correctamente
            os.chdir(str(base))
            if str(base) not in sys.path:
                sys.path.insert(0, str(base))
        else:
            base = Path(__file__).parent

        app_path = str(base / "app.py")

        # Abrir el navegador en segundo plano mientras arranca el servidor
        threading.Thread(target=_abrir_navegador, daemon=True).start()

        from streamlit.web import cli as stcli

        sys.argv = [
            "streamlit", "run", app_path,
            f"--server.port={PORT}",
            "--server.headless=true",
            "--server.runOnSave=false",
            "--server.fileWatcherType=none",   # desactiva watcher innecesario
            "--global.developmentMode=false",
            "--browser.gatherUsageStats=false",
            "--logger.level=error",
        ]
        stcli.main()

    except SystemExit:
        pass  # salida normal del proceso
    except Exception as exc:
        _mostrar_error(str(exc))


if __name__ == "__main__":
    main()
