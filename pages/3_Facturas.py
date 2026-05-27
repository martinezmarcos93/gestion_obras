from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from utils import mostrar_boton_salir
from database import (
    ARCHIVOS_DIR,
    init_db,
    get_clientes,
    get_presupuestos,
    get_facturas,
    add_factura,
    set_factura_archivo,
    marcar_abonada,
    marcar_pendiente,
    delete_factura,
)

st.set_page_config(page_title="Facturas — Gestión de Obras", page_icon="🧾", layout="wide")


@st.cache_resource
def inicializar():
    init_db()


inicializar()
mostrar_boton_salir()

TIPOS_FACTURA   = ["adelanto", "saldo", "parcial", "otros"]
TIPOS_ARCHIVO   = ["pdf", "png", "jpg", "jpeg"]

st.title("🧾 Facturas")

clientes_df = get_clientes()

# ── Filtros ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
cli_opts      = {"Todos": None, **{r["nombre"]: r["id"] for _, r in clientes_df.iterrows()}}
cli_filter    = col1.selectbox("Cliente",   list(cli_opts.keys()), key="fac_cli_filter")
estado_filter = col2.selectbox("Estado",    ["Todos", "pendiente", "abonada"], key="fac_est_filter")

cli_id_f    = cli_opts[cli_filter]
estado_f    = estado_filter if estado_filter != "Todos" else None
df_facturas = get_facturas(cliente_id=cli_id_f, estado=estado_f)

# ── Métricas resumen ──────────────────────────────────────────────────────────
if not df_facturas.empty:
    total_pend = df_facturas[df_facturas["estado"] == "pendiente"]["monto"].sum()
    total_cob  = df_facturas[df_facturas["estado"] == "abonada"]["monto"].sum()
    m1, m2, m3 = st.columns(3)
    m1.metric("Total en lista",     f"${df_facturas['monto'].sum():,.2f}")
    m2.metric("Pendiente de cobro", f"${total_pend:,.2f}")
    m3.metric("Cobrado (lista)",    f"${total_cob:,.2f}")

# ── Tabla ─────────────────────────────────────────────────────────────────────
if df_facturas.empty:
    st.info("No hay facturas con los filtros seleccionados.")
else:
    df_show = df_facturas[
        ["id", "cliente", "presupuesto", "numero_factura", "tipo", "monto", "fecha_emision", "estado", "fecha_pago"]
    ].copy()
    df_show["monto"]   = df_show["monto"].map("${:,.2f}".format)
    df_show["adjunto"] = df_facturas["archivo_path"].apply(lambda p: "📎" if p else "")
    df_show.columns    = ["ID", "Cliente", "Presupuesto", "N° Factura", "Tipo", "Monto", "Fecha Emisión", "Estado", "Fecha Pago", "PDF"]
    st.dataframe(df_show, use_container_width=True, hide_index=True)

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_acciones, tab_nueva = st.tabs(["⚡ Acciones", "➕ Nueva Factura"])

# ══════════════════════════════════════════════════════
#  TAB ACCIONES
# ══════════════════════════════════════════════════════
with tab_acciones:
    if df_facturas.empty:
        st.info("No hay facturas disponibles con los filtros actuales.")
    else:
        fac_opts = {
            f"[{r['id']}] {r['cliente']} — {r['presupuesto'][:35]} — ${r['monto']:,.2f} ({r['estado']})": r["id"]
            for _, r in df_facturas.iterrows()
        }
        sel    = st.selectbox("Seleccionar factura", list(fac_opts.keys()), key="fac_sel")
        fac_id = fac_opts[sel]
        fac    = df_facturas[df_facturas["id"] == fac_id].iloc[0]

        # ── Detalle ──────────────────────────────────────────────────────────
        d1, d2, d3 = st.columns(3)
        d1.write(f"**Cliente:** {fac['cliente']}")
        d2.write(f"**Tipo:** {fac['tipo'].upper()}")
        d3.write(f"**Monto:** ${fac['monto']:,.2f}")
        d1.write(f"**Presupuesto:** {fac['presupuesto']}")
        d2.write(f"**N° Factura:** {fac['numero_factura'] or '—'}")
        d3.write(f"**Estado:** {'🟢 ABONADA' if fac['estado'] == 'abonada' else '🟡 PENDIENTE'}")
        if fac.get("notas"):
            st.caption(f"📝 {fac['notas']}")

        st.write("")
        col_a, col_b, col_c = st.columns([2, 2, 1])

        # ── Marcar abonada / revertir ─────────────────────────────────────────
        if fac["estado"] == "pendiente":
            with col_a.form("form_abonada"):
                fp = st.date_input("Fecha de Pago", value=date.today())
                if st.form_submit_button("✅ Marcar Abonada", type="primary"):
                    marcar_abonada(fac_id, str(fp))
                    st.success("Factura marcada como abonada.")
                    st.rerun()
        else:
            if col_a.button("↩️ Revertir a Pendiente", key="btn_revertir"):
                marcar_pendiente(fac_id)
                st.warning("Factura revertida a pendiente.")
                st.rerun()

        # ── Eliminar ──────────────────────────────────────────────────────────
        if col_c.button("🗑️ Eliminar", type="secondary", key="btn_del_fac"):
            # Borrar archivo adjunto si existe
            if fac.get("archivo_path"):
                archivo = ARCHIVOS_DIR / fac["archivo_path"]
                if archivo.exists():
                    archivo.unlink()
            delete_factura(fac_id)
            st.success("Factura eliminada.")
            st.rerun()

        st.divider()

        # ── Adjunto AFIP ──────────────────────────────────────────────────────
        st.subheader("📎 Comprobante AFIP")

        archivo_actual = fac.get("archivo_path")
        if archivo_actual:
            archivo_path = ARCHIVOS_DIR / archivo_actual
            if archivo_path.exists():
                ext = archivo_path.suffix.lower()
                file_bytes = archivo_path.read_bytes()
                col_prev, col_dl = st.columns([3, 1])
                if ext == ".pdf":
                    col_prev.info(f"PDF adjunto: `{archivo_actual}`")
                    col_dl.download_button(
                        "⬇️ Descargar PDF",
                        file_bytes,
                        file_name=archivo_actual,
                        mime="application/pdf",
                    )
                else:
                    col_prev.image(file_bytes, caption="Comprobante adjunto", use_container_width=True)
                    col_dl.download_button(
                        "⬇️ Descargar",
                        file_bytes,
                        file_name=archivo_actual,
                    )
            else:
                st.warning("El archivo registrado ya no existe en disco.")

        with st.expander("📤 Adjuntar / Reemplazar comprobante AFIP"):
            nuevo_archivo = st.file_uploader(
                "Seleccioná el PDF o imagen de la factura AFIP",
                type=TIPOS_ARCHIVO,
                key="fac_adj_uploader",
            )
            if st.button("Guardar adjunto", key="btn_guardar_adj") and nuevo_archivo:
                ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{fac_id}_{ts}_{nuevo_archivo.name}"
                dest     = ARCHIVOS_DIR / filename
                # Eliminar adjunto anterior si existe
                if archivo_actual and (ARCHIVOS_DIR / archivo_actual).exists():
                    (ARCHIVOS_DIR / archivo_actual).unlink()
                dest.write_bytes(nuevo_archivo.read())
                set_factura_archivo(fac_id, filename)
                st.success(f"Comprobante guardado: `{filename}`")
                st.rerun()
            elif st.session_state.get("btn_guardar_adj") and not nuevo_archivo:
                st.warning("Seleccioná un archivo primero.")

# ══════════════════════════════════════════════════════
#  TAB NUEVA FACTURA
# ══════════════════════════════════════════════════════
with tab_nueva:
    st.subheader("Nueva Factura")

    # Selector de cliente fuera del form (filtra presupuestos dinámicamente)
    cli_nueva_opts = {"Todos": None, **{r["nombre"]: r["id"] for _, r in clientes_df.iterrows()}}
    cli_nueva      = st.selectbox(
        "Cliente (para filtrar presupuestos)", list(cli_nueva_opts.keys()), key="fac_nueva_cli"
    )
    cli_id_nueva   = cli_nueva_opts[cli_nueva]

    pres_aprobados = get_presupuestos(cliente_id=cli_id_nueva, estado="aprobado")

    if pres_aprobados.empty:
        st.info(
            "No hay presupuestos **aprobados** para este cliente. "
            "Aprobá uno en **Presupuestos** antes de crear una factura."
        )
    else:
        pres_opts = {
            f"[{r['id']}] {r['cliente']} — {r['descripcion'][:50]}": r["id"]
            for _, r in pres_aprobados.iterrows()
        }

        with st.form("form_nueva_factura", clear_on_submit=True):
            pres_sel    = st.selectbox("Presupuesto *", list(pres_opts.keys()))
            pres_id_sel = pres_opts[pres_sel]

            col1, col2 = st.columns(2)
            numero  = col1.text_input("N° de Factura", placeholder="A-0001-00001234")
            tipo    = col2.selectbox("Tipo *", TIPOS_FACTURA)
            monto   = col1.number_input("Monto ($) *", min_value=0.01, format="%.2f")
            fecha   = col2.date_input("Fecha de Emisión", value=date.today())
            notas   = st.text_area("Notas", placeholder="Observaciones adicionales…")

            archivo = st.file_uploader(
                "📎 Adjuntar comprobante AFIP (PDF o imagen) — opcional",
                type=TIPOS_ARCHIVO,
            )

            if st.form_submit_button("Crear Factura", type="primary"):
                if monto <= 0:
                    st.error("El monto debe ser mayor a 0.")
                else:
                    fac_id = add_factura(pres_id_sel, numero, tipo, monto, str(fecha), notas)
                    if archivo is not None:
                        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{fac_id}_{ts}_{archivo.name}"
                        (ARCHIVOS_DIR / filename).write_bytes(archivo.read())
                        set_factura_archivo(fac_id, filename)
                        st.success(f"Factura creada y comprobante guardado (`{filename}`).")
                    else:
                        st.success("Factura creada. Podés adjuntar el comprobante AFIP desde **Acciones**.")
                    st.rerun()
