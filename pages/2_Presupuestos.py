from datetime import date

import streamlit as st

from utils import mostrar_boton_salir
from database import (
    init_db,
    get_clientes,
    get_presupuestos,
    get_presupuesto_by_id,
    get_facturas,
    add_presupuesto,
    update_presupuesto,
    aprobar_presupuesto,
    cancelar_presupuesto,
    delete_presupuesto,
)

st.set_page_config(page_title="Presupuestos — Gestión de Obras", page_icon="📋", layout="wide")


@st.cache_resource
def inicializar():
    init_db()


inicializar()
mostrar_boton_salir()

ESTADOS = ["Todos", "pendiente", "aprobado", "cancelado"]

st.title("📋 Presupuestos")

clientes_df = get_clientes()
if clientes_df.empty:
    st.warning("⚠️ Primero registrá al menos un cliente en la sección **Clientes**.")
    st.stop()

# ── Filtros ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
cli_opts = {"Todos": None, **{r["nombre"]: r["id"] for _, r in clientes_df.iterrows()}}
cli_filter    = col1.selectbox("Cliente",   list(cli_opts.keys()), key="pres_cli_filter")
estado_filter = col2.selectbox("Estado",    ESTADOS,               key="pres_est_filter")

cliente_id_f = cli_opts[cli_filter]
estado_f     = estado_filter if estado_filter != "Todos" else None
df           = get_presupuestos(cliente_id=cliente_id_f, estado=estado_f)

# ── Tabla principal ───────────────────────────────────────────────────────────
if df.empty:
    st.info("No hay presupuestos con los filtros seleccionados.")
else:
    df_show = df[["id", "cliente", "descripcion", "monto_total", "cobrado", "fecha_emision", "estado"]].copy()
    df_show["saldo"] = df["monto_total"] - df["cobrado"]
    df_show["monto_total"] = df_show["monto_total"].map("${:,.2f}".format)
    df_show["cobrado"]     = df_show["cobrado"].map("${:,.2f}".format)
    df_show["saldo"]       = df_show["saldo"].map("${:,.2f}".format)
    df_show.columns = ["ID", "Cliente", "Descripción", "Monto Total", "Cobrado", "Fecha", "Estado", "Saldo"]
    st.dataframe(df_show, use_container_width=True, hide_index=True)

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_detalle, tab_nuevo = st.tabs(["📂 Ver / Acciones", "➕ Nuevo Presupuesto"])

# ── Tab: Detalle y acciones ───────────────────────────────────────────────────
with tab_detalle:
    if df.empty:
        st.info("No hay presupuestos que mostrar con los filtros actuales.")
    else:
        pres_opts = {
            f"[{r['id']}] {r['cliente']} — {r['descripcion'][:50]}": r["id"]
            for _, r in df.iterrows()
        }
        sel    = st.selectbox("Seleccionar presupuesto", list(pres_opts.keys()), key="pres_sel")
        pres_id = pres_opts[sel]
        pres    = get_presupuesto_by_id(pres_id)

        if pres:
            # ── Métricas del presupuesto ──────────────────────────────────────
            facturas_pres = get_facturas(presupuesto_id=pres_id)
            cobrado = facturas_pres[facturas_pres["estado"] == "abonada"]["monto"].sum() if not facturas_pres.empty else 0.0
            facturado = facturas_pres["monto"].sum() if not facturas_pres.empty else 0.0
            saldo   = pres["monto_total"] - cobrado

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Monto Total",    f"${pres['monto_total']:,.2f}")
            m2.metric("Facturado",      f"${facturado:,.2f}")
            m3.metric("Cobrado",        f"${cobrado:,.2f}")
            m4.metric("Saldo Pendiente", f"${saldo:,.2f}", delta=f"-${saldo:,.2f}" if saldo > 0 else None, delta_color="inverse")

            if pres["monto_total"] > 0:
                pct = min(cobrado / pres["monto_total"], 1.0)
                st.progress(pct, text=f"Cobrado: {pct * 100:.1f}% del total")

            estado_icon = {"pendiente": "🟡", "aprobado": "🟢", "cancelado": "🔴"}.get(pres["estado"], "⚪")
            st.write(
                f"**Cliente:** {pres['cliente_nombre']} &nbsp;|&nbsp; "
                f"**Estado:** {estado_icon} {pres['estado'].upper()} &nbsp;|&nbsp; "
                f"**Fecha:** {pres['fecha_emision']}"
            )
            if pres["notas"]:
                st.caption(f"📝 Notas: {pres['notas']}")

            # ── Botones de acción ─────────────────────────────────────────────
            a1, a2, a3, _pad = st.columns([1, 1, 1, 3])

            if pres["estado"] == "pendiente":
                if a1.button("✅ Aprobar", type="primary", key="btn_aprobar"):
                    aprobar_presupuesto(pres_id)
                    st.success("Presupuesto aprobado.")
                    st.rerun()
            elif pres["estado"] == "aprobado":
                if a1.button("❌ Cancelar", type="secondary", key="btn_cancelar"):
                    cancelar_presupuesto(pres_id)
                    st.warning("Presupuesto cancelado.")
                    st.rerun()

            if a3.button("🗑️ Eliminar", type="secondary", key="btn_eliminar_pres"):
                try:
                    delete_presupuesto(pres_id)
                    st.success("Presupuesto eliminado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se puede eliminar (tiene facturas asociadas): {e}")

            # ── Facturas del presupuesto ──────────────────────────────────────
            st.subheader("Facturas de este Presupuesto")
            if facturas_pres.empty:
                st.info("No hay facturas asociadas. Creá una en la sección **Facturas**.")
            else:
                df_fac = facturas_pres[
                    ["numero_factura", "tipo", "monto", "fecha_emision", "estado", "fecha_pago"]
                ].copy()
                df_fac["monto"] = df_fac["monto"].map("${:,.2f}".format)
                df_fac.columns = ["N° Factura", "Tipo", "Monto", "Fecha Emisión", "Estado", "Fecha Pago"]
                st.dataframe(df_fac, use_container_width=True, hide_index=True)

            # ── Editar presupuesto ────────────────────────────────────────────
            with st.expander("✏️ Editar este Presupuesto"):
                with st.form("form_editar_pres"):
                    desc_e  = st.text_area("Descripción *", value=pres["descripcion"])
                    col_e1, col_e2 = st.columns(2)
                    monto_e = col_e1.number_input(
                        "Monto Total ($) *",
                        value=float(pres["monto_total"]),
                        min_value=0.0,
                        format="%.2f",
                    )
                    fecha_val = date.fromisoformat(pres["fecha_emision"]) if pres["fecha_emision"] else date.today()
                    fecha_e = col_e2.date_input("Fecha Emisión", value=fecha_val)
                    notas_e = st.text_area("Notas", value=pres["notas"] or "")

                    if st.form_submit_button("Guardar Cambios", type="primary"):
                        if not desc_e.strip():
                            st.error("La descripción es obligatoria.")
                        elif monto_e <= 0:
                            st.error("El monto debe ser mayor a 0.")
                        else:
                            update_presupuesto(pres_id, desc_e, monto_e, str(fecha_e), notas_e)
                            st.success("Presupuesto actualizado.")
                            st.rerun()

# ── Tab: Nuevo presupuesto ────────────────────────────────────────────────────
with tab_nuevo:
    with st.form("form_nuevo_pres", clear_on_submit=True):
        cli_nueva_opts = {r["nombre"]: r["id"] for _, r in clientes_df.iterrows()}
        cli_sel  = st.selectbox("Cliente *", list(cli_nueva_opts.keys()))
        desc     = st.text_area("Descripción *", placeholder="Descripción del trabajo a realizar…")
        col1, col2 = st.columns(2)
        monto    = col1.number_input("Monto Total ($) *", min_value=0.0, format="%.2f")
        fecha    = col2.date_input("Fecha de Emisión", value=date.today())
        notas    = st.text_area("Notas", placeholder="Condiciones, observaciones…")

        if st.form_submit_button("Crear Presupuesto", type="primary"):
            if not desc.strip():
                st.error("La descripción es obligatoria.")
            elif monto <= 0:
                st.error("El monto debe ser mayor a 0.")
            else:
                add_presupuesto(cli_nueva_opts[cli_sel], desc, monto, str(fecha), notas)
                st.success(f"Presupuesto creado para **{cli_sel}**.")
                st.rerun()
