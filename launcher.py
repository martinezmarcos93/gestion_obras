"""
Lanzador de Gestión de Obras.
Inicia Streamlit en background y abre el navegador automáticamente.
Se puede convertir a .exe con PyInstaller (ver build.bat).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox

# ── Directorio base ───────────────────────────────────────────────────────────
# Funciona tanto como script (.py) como ejecutable PyInstaller (.exe)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

PORT = 8501
URL  = f"http://localhost:{PORT}"


# ── Búsqueda de Streamlit ─────────────────────────────────────────────────────

def _find_streamlit_cmd() -> list[str] | None:
    """
    Devuelve el comando para ejecutar 'streamlit run …', o None si no se encuentra.
    Busca en PATH, en carpetas comunes de Windows y prueba 'python -m streamlit'.
    """
    # 1. streamlit.exe en PATH
    st = shutil.which("streamlit")
    if st:
        return [st, "run"]

    # 2. Carpetas Scripts de instalaciones comunes en Windows
    appdata      = os.environ.get("APPDATA", "")
    localappdata = os.environ.get("LOCALAPPDATA", "")

    versiones = ["39", "310", "311", "312", "313"]
    scripts_candidatos: list[Path] = []

    for v in versiones:
        scripts_candidatos += [
            Path(appdata)      / "Python" / f"Python{v}" / "Scripts",
            Path(localappdata) / "Programs" / "Python" / f"Python{v}" / "Scripts",
            Path(f"C:/Python{v}/Scripts"),
        ]

    for scripts in scripts_candidatos:
        exe = scripts / "streamlit.exe"
        if exe.exists():
            return [str(exe), "run"]

    # 3. python -m streamlit (busca cualquier Python que tenga streamlit)
    python_candidatos: list[str] = []

    for nombre in ("python", "python3", "py"):
        p = shutil.which(nombre)
        if p:
            python_candidatos.append(p)

    for v in versiones:
        for base in (Path(localappdata) / "Programs" / "Python", Path("C:/")):
            exe = base / f"Python{v}" / "python.exe"
            if exe.exists():
                python_candidatos.append(str(exe))

    for py in python_candidatos:
        try:
            r = subprocess.run(
                [py, "-c", "import streamlit; print('ok')"],
                capture_output=True, text=True, timeout=8,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if "ok" in r.stdout:
                return [py, "-m", "streamlit", "run"]
        except Exception:
            continue

    return None


# ── Ventana principal ─────────────────────────────────────────────────────────

class GestionObrasApp:
    BG   = "#f8fafc"
    AZUL = "#2563eb"
    ROJO = "#dc2626"
    VERDE = "#16a34a"

    def __init__(self, root: tk.Tk):
        self.root    = root
        self.process: subprocess.Popen | None = None
        self._setup_ui()
        threading.Thread(target=self._iniciar, daemon=True).start()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = self.root
        root.title("Gestión de Obras")
        root.geometry("360x210")
        root.resizable(False, False)
        root.configure(bg=self.BG)
        root.protocol("WM_DELETE_WINDOW", self.cerrar)
        root.attributes("-topmost", True)
        root.after(4000, lambda: root.attributes("-topmost", False))

        tk.Label(
            root, text="🏗️  Gestión de Obras",
            font=("Segoe UI", 16, "bold"), bg=self.BG, fg="#1e293b",
        ).pack(pady=(22, 2))

        tk.Label(
            root, text="Maestro Mayor de Obras",
            font=("Segoe UI", 9), bg=self.BG, fg="#64748b",
        ).pack()

        self.lbl_estado = tk.Label(
            root, text="⏳  Iniciando servidor…",
            font=("Segoe UI", 10), bg=self.BG, fg="#d97706",
        )
        self.lbl_estado.pack(pady=14)

        btn_frame = tk.Frame(root, bg=self.BG)
        btn_frame.pack()

        self.btn_abrir = tk.Button(
            btn_frame, text="🌐  Abrir navegador",
            font=("Segoe UI", 10), bg=self.AZUL, fg="white",
            relief="flat", padx=14, pady=7,
            state="disabled", command=self.abrir_navegador, cursor="hand2",
            activebackground="#1d4ed8", activeforeground="white",
        )
        self.btn_abrir.pack(side="left", padx=8)

        self.btn_cerrar = tk.Button(
            btn_frame, text="🔴  Cerrar",
            font=("Segoe UI", 10), bg=self.ROJO, fg="white",
            relief="flat", padx=14, pady=7,
            command=self.cerrar, cursor="hand2",
            activebackground="#b91c1c", activeforeground="white",
        )
        self.btn_cerrar.pack(side="left", padx=8)

    # ── Inicio de Streamlit ────────────────────────────────────────────────────

    def _iniciar(self):
        cmd_base = _find_streamlit_cmd()
        if cmd_base is None:
            self.root.after(0, self._error_no_encontrado)
            return

        app_py = BASE_DIR / "app.py"
        if not app_py.exists():
            self.root.after(0, lambda: self._error_inicio(
                f"No se encontró app.py en:\n{BASE_DIR}\n\n"
                "Asegurate de que GestionObras.exe esté en la carpeta del proyecto."
            ))
            return

        cmd = cmd_base + [
            str(app_py),
            "--server.headless",          "true",
            "--server.port",              str(PORT),
            "--server.runOnSave",         "false",
            "--global.developmentMode",   "false",
            "--browser.gatherUsageStats", "false",
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=str(BASE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception as e:
            self.root.after(0, lambda: self._error_inicio(str(e)))
            return

        # Esperar a que el servidor levante (~4 s)
        time.sleep(4)

        if self.process.poll() is None:          # sigue corriendo ✓
            self.root.after(0, self._on_ready)
            threading.Thread(target=self._monitorear, daemon=True).start()
        else:
            stderr = self.process.stderr.read().decode(errors="replace")
            self.root.after(0, lambda: self._error_inicio(stderr[:300] or "Error desconocido"))

    def _monitorear(self):
        """Si Streamlit se cierra (botón 'Cerrar' de la app), cierra esta ventana también."""
        if self.process:
            self.process.wait()
        self.root.after(0, self._cerrar_silencioso)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_ready(self):
        self.lbl_estado.config(text="✅  Ejecutándose — localhost:8501", fg=self.VERDE)
        self.btn_abrir.config(state="normal")
        webbrowser.open(URL)

    def _error_no_encontrado(self):
        self.lbl_estado.config(text="❌  Streamlit no encontrado", fg=self.ROJO)
        messagebox.showerror(
            "Error — Streamlit no encontrado",
            "No se encontró Python con Streamlit instalado.\n\n"
            "Ejecutá en la terminal:\n"
            "  pip install streamlit pandas\n\n"
            "Luego volvé a abrir la aplicación.",
        )

    def _error_inicio(self, detalle: str):
        self.lbl_estado.config(text="❌  Error al iniciar", fg=self.ROJO)
        messagebox.showerror("Error al iniciar", f"No se pudo iniciar Streamlit:\n\n{detalle}")

    def abrir_navegador(self):
        webbrowser.open(URL)

    def cerrar(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.root.destroy()

    def _cerrar_silencioso(self):
        """Cierra la ventana sin matar el proceso (ya terminó solo)."""
        try:
            self.root.destroy()
        except Exception:
            pass


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    GestionObrasApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
