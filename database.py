from __future__ import annotations

import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path
import pandas as pd

# Cuando corre como .exe congelado (PyInstaller), los datos se guardan
# en la carpeta "datos/" junto al ejecutable — nunca en la carpeta temporal.
if getattr(sys, "frozen", False):
    _BASE = Path(sys.executable).parent / "datos"
else:
    _BASE = Path(__file__).parent

DB_PATH      = _BASE / "gestion_obras.db"
ARCHIVOS_DIR = _BASE / "archivos" / "facturas"


@contextmanager
def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _migrate():
    """Agrega columnas nuevas a tablas existentes sin romper datos previos."""
    with get_conn() as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(facturas)").fetchall()}
        if "archivo_path" not in cols:
            conn.execute("ALTER TABLE facturas ADD COLUMN archivo_path TEXT")


def init_db():
    ARCHIVOS_DIR.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS clientes (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre   TEXT    NOT NULL,
                cuit     TEXT,
                tipo     TEXT    DEFAULT 'consorcio'
                                 CHECK (tipo IN ('consorcio', 'particular', 'empresa')),
                telefono TEXT,
                email    TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS presupuestos (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id   INTEGER NOT NULL REFERENCES clientes(id),
                descripcion  TEXT    NOT NULL,
                monto_total  REAL    NOT NULL,
                fecha_emision TEXT   DEFAULT (date('now')),
                estado       TEXT    DEFAULT 'pendiente'
                                     CHECK (estado IN ('pendiente', 'aprobado', 'cancelado')),
                notas        TEXT,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS facturas (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                presupuesto_id  INTEGER NOT NULL REFERENCES presupuestos(id),
                numero_factura  TEXT,
                tipo            TEXT    DEFAULT 'otros'
                                        CHECK (tipo IN ('adelanto', 'saldo', 'parcial', 'otros')),
                monto           REAL    NOT NULL,
                fecha_emision   TEXT    DEFAULT (date('now')),
                estado          TEXT    DEFAULT 'pendiente'
                                        CHECK (estado IN ('pendiente', 'abonada')),
                fecha_pago      TEXT,
                notas           TEXT,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    _migrate()


# ══════════════════════════════════════════════════════
#  CLIENTES
# ══════════════════════════════════════════════════════

def get_clientes(tipo: str | None = None) -> pd.DataFrame:
    query = "SELECT id, nombre, cuit, tipo, telefono, email FROM clientes"
    params: list = []
    if tipo and tipo != "Todos":
        query += " WHERE tipo = ?"
        params.append(tipo)
    query += " ORDER BY nombre"
    with get_conn() as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_cliente_by_id(id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM clientes WHERE id=?", (id,)).fetchone()
        return dict(row) if row else None


def add_cliente(nombre: str, cuit: str, tipo: str, telefono: str, email: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO clientes (nombre, cuit, tipo, telefono, email) VALUES (?,?,?,?,?)",
            (nombre.strip(), cuit.strip() or None, tipo, telefono.strip() or None, email.strip() or None),
        )


def update_cliente(id: int, nombre: str, cuit: str, tipo: str, telefono: str, email: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE clientes SET nombre=?, cuit=?, tipo=?, telefono=?, email=? WHERE id=?",
            (nombre.strip(), cuit.strip() or None, tipo, telefono.strip() or None, email.strip() or None, id),
        )


def delete_cliente(id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM clientes WHERE id=?", (id,))


# ══════════════════════════════════════════════════════
#  PRESUPUESTOS
# ══════════════════════════════════════════════════════

def get_presupuestos(cliente_id: int | None = None, estado: str | None = None) -> pd.DataFrame:
    query = """
        SELECT
            p.id,
            c.nombre  AS cliente,
            p.descripcion,
            p.monto_total,
            COALESCE((
                SELECT SUM(f.monto) FROM facturas f
                WHERE f.presupuesto_id = p.id AND f.estado = 'abonada'
            ), 0) AS cobrado,
            COALESCE((
                SELECT SUM(f.monto) FROM facturas f
                WHERE f.presupuesto_id = p.id
            ), 0) AS facturado,
            p.fecha_emision,
            p.estado,
            p.notas,
            p.cliente_id
        FROM presupuestos p
        JOIN clientes c ON p.cliente_id = c.id
        WHERE 1=1
    """
    params: list = []
    if cliente_id:
        query += " AND p.cliente_id = ?"
        params.append(cliente_id)
    if estado and estado != "Todos":
        query += " AND p.estado = ?"
        params.append(estado)
    query += " ORDER BY p.created_at DESC"
    with get_conn() as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_presupuesto_by_id(id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """SELECT p.*, c.nombre AS cliente_nombre
               FROM presupuestos p
               JOIN clientes c ON p.cliente_id = c.id
               WHERE p.id=?""",
            (id,),
        ).fetchone()
        return dict(row) if row else None


def add_presupuesto(cliente_id: int, descripcion: str, monto_total: float, fecha_emision: str, notas: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO presupuestos (cliente_id, descripcion, monto_total, fecha_emision, notas) VALUES (?,?,?,?,?)",
            (cliente_id, descripcion.strip(), monto_total, fecha_emision, notas.strip() or None),
        )


def update_presupuesto(id: int, descripcion: str, monto_total: float, fecha_emision: str, notas: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE presupuestos SET descripcion=?, monto_total=?, fecha_emision=?, notas=? WHERE id=?",
            (descripcion.strip(), monto_total, fecha_emision, notas.strip() or None, id),
        )


def aprobar_presupuesto(id: int):
    with get_conn() as conn:
        conn.execute("UPDATE presupuestos SET estado='aprobado' WHERE id=?", (id,))


def cancelar_presupuesto(id: int):
    with get_conn() as conn:
        conn.execute("UPDATE presupuestos SET estado='cancelado' WHERE id=?", (id,))


def delete_presupuesto(id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM presupuestos WHERE id=?", (id,))


# ══════════════════════════════════════════════════════
#  FACTURAS
# ══════════════════════════════════════════════════════

def get_facturas(
    presupuesto_id: int | None = None,
    estado: str | None = None,
    cliente_id: int | None = None,
) -> pd.DataFrame:
    query = """
        SELECT
            f.id,
            c.nombre          AS cliente,
            p.descripcion     AS presupuesto,
            f.presupuesto_id,
            f.numero_factura,
            f.tipo,
            f.monto,
            f.fecha_emision,
            f.estado,
            f.fecha_pago,
            f.notas,
            f.archivo_path,
            p.monto_total
        FROM facturas f
        JOIN presupuestos p ON f.presupuesto_id = p.id
        JOIN clientes c     ON p.cliente_id = c.id
        WHERE 1=1
    """
    params: list = []
    if presupuesto_id:
        query += " AND f.presupuesto_id = ?"
        params.append(presupuesto_id)
    if cliente_id:
        query += " AND p.cliente_id = ?"
        params.append(cliente_id)
    if estado and estado != "Todos":
        query += " AND f.estado = ?"
        params.append(estado)
    query += " ORDER BY f.fecha_emision DESC"
    with get_conn() as conn:
        return pd.read_sql_query(query, conn, params=params)


def add_factura(presupuesto_id: int, numero_factura: str, tipo: str, monto: float, fecha_emision: str, notas: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO facturas (presupuesto_id, numero_factura, tipo, monto, fecha_emision, notas) VALUES (?,?,?,?,?,?)",
            (presupuesto_id, numero_factura.strip() or None, tipo, monto, fecha_emision, notas.strip() or None),
        )
        return cur.lastrowid


def set_factura_archivo(id: int, filename: str):
    with get_conn() as conn:
        conn.execute("UPDATE facturas SET archivo_path=? WHERE id=?", (filename, id))


def marcar_abonada(id: int, fecha_pago: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE facturas SET estado='abonada', fecha_pago=? WHERE id=?",
            (fecha_pago, id),
        )


def marcar_pendiente(id: int):
    with get_conn() as conn:
        conn.execute("UPDATE facturas SET estado='pendiente', fecha_pago=NULL WHERE id=?", (id,))


def delete_factura(id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM facturas WHERE id=?", (id,))


# ══════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════

def get_stats() -> dict:
    with get_conn() as conn:
        c = conn
        return {
            "presupuestos_activos":    c.execute("SELECT COUNT(*) FROM presupuestos WHERE estado='aprobado'").fetchone()[0],
            "presupuestos_pendientes": c.execute("SELECT COUNT(*) FROM presupuestos WHERE estado='pendiente'").fetchone()[0],
            "facturas_pendientes":     c.execute("SELECT COUNT(*) FROM facturas WHERE estado='pendiente'").fetchone()[0],
            "monto_por_cobrar":        c.execute("SELECT COALESCE(SUM(monto),0) FROM facturas WHERE estado='pendiente'").fetchone()[0],
            "total_cobrado":           c.execute("SELECT COALESCE(SUM(monto),0) FROM facturas WHERE estado='abonada'").fetchone()[0],
            "total_clientes":          c.execute("SELECT COUNT(*) FROM clientes").fetchone()[0],
        }


def get_seguimiento() -> pd.DataFrame:
    query = """
        SELECT
            p.id,
            c.nombre  AS Cliente,
            p.descripcion AS Descripcion,
            p.monto_total,
            COALESCE(SUM(CASE WHEN f.estado='abonada' THEN f.monto ELSE 0 END), 0) AS cobrado,
            p.monto_total - COALESCE(SUM(CASE WHEN f.estado='abonada' THEN f.monto ELSE 0 END), 0) AS saldo_pendiente,
            p.fecha_emision
        FROM presupuestos p
        JOIN clientes c   ON p.cliente_id = c.id
        LEFT JOIN facturas f ON p.id = f.presupuesto_id
        WHERE p.estado = 'aprobado'
        GROUP BY p.id
        ORDER BY saldo_pendiente DESC
    """
    with get_conn() as conn:
        return pd.read_sql_query(query, conn)


def get_facturacion_mensual() -> pd.DataFrame:
    query = """
        SELECT
            strftime('%Y-%m', fecha_emision) AS mes,
            SUM(CASE WHEN estado='abonada'  THEN monto ELSE 0 END) AS cobrado,
            SUM(CASE WHEN estado='pendiente' THEN monto ELSE 0 END) AS pendiente
        FROM facturas
        WHERE fecha_emision >= date('now', '-12 months')
        GROUP BY mes
        ORDER BY mes
    """
    with get_conn() as conn:
        return pd.read_sql_query(query, conn)
