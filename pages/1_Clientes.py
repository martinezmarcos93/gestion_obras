import streamlit as st

from utils import mostrar_boton_salir
from database import (
    init_db,
    get_clientes,
    get_cliente_by_id,
    add_cliente,
    update_cliente,
    delete_cliente,
)

st.set_page_config(page_title="Clientes — Gestión de Obras", page_icon="👥", layout="wide")


@st.cache_resource
def inicializar():
    init_db()


inicializar()
mostrar_boton_salir()

TIPOS = ["consorcio", "particular", "empresa"]

st.title("👥 Clientes")

# ── Filtro ────────────────────────────────────────────────────────────────────
tipo_filter = st.selectbox("Filtrar por tipo", ["Todos", *TIPOS], key="cli_tipo_filter")
df = get_clientes(tipo_filter)

# ── Tabla ─────────────────────────────────────────────────────────────────────
if df.empty:
    st.info("No hay clientes registrados. Usá la pestaña **Nuevo Cliente** para agregar uno.")
else:
    df_show = df[["id", "nombre", "cuit", "tipo", "telefono", "email"]].copy()
    df_show.columns = ["ID", "Nombre", "CUIT", "Tipo", "Teléfono", "Email"]
    st.dataframe(df_show, use_container_width=True, hide_index=True)

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_nuevo, tab_editar = st.tabs(["➕ Nuevo Cliente", "✏️ Editar / Eliminar"])

# ── Tab: Nuevo ────────────────────────────────────────────────────────────────
with tab_nuevo:
    with st.form("form_nuevo_cliente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nombre   = col1.text_input("Nombre *", placeholder="Consorcio Av. Corrientes 1234")
        cuit     = col2.text_input("CUIT",     placeholder="20-12345678-9")
        tipo     = col1.selectbox("Tipo *", TIPOS)
        telefono = col2.text_input("Teléfono", placeholder="+54 11 1234-5678")
        email    = st.text_input("Email", placeholder="contacto@ejemplo.com")

        if st.form_submit_button("Guardar Cliente", type="primary"):
            if not nombre.strip():
                st.error("El nombre es obligatorio.")
            else:
                try:
                    add_cliente(nombre, cuit, tipo, telefono, email)
                    st.success(f"Cliente **{nombre.strip()}** agregado correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

# ── Tab: Editar ───────────────────────────────────────────────────────────────
with tab_editar:
    df_all = get_clientes()
    if df_all.empty:
        st.info("No hay clientes para editar.")
    else:
        opciones = {f"[{r['id']}] {r['nombre']}": r["id"] for _, r in df_all.iterrows()}
        sel      = st.selectbox("Seleccionar cliente", list(opciones.keys()), key="cli_sel_editar")
        cid      = opciones[sel]
        cliente  = get_cliente_by_id(cid)

        if cliente:
            with st.form("form_editar_cliente"):
                col1, col2 = st.columns(2)
                nombre_e   = col1.text_input("Nombre *",  value=cliente["nombre"])
                cuit_e     = col2.text_input("CUIT",      value=cliente["cuit"] or "")
                tipo_e     = col1.selectbox("Tipo *", TIPOS, index=TIPOS.index(cliente["tipo"]))
                telefono_e = col2.text_input("Teléfono",  value=cliente["telefono"] or "")
                email_e    = st.text_input("Email",       value=cliente["email"] or "")

                col_save, col_del = st.columns([4, 1])
                guardar  = col_save.form_submit_button("Guardar Cambios", type="primary")
                eliminar = col_del.form_submit_button("🗑️ Eliminar", type="secondary")

                if guardar:
                    if not nombre_e.strip():
                        st.error("El nombre es obligatorio.")
                    else:
                        update_cliente(cid, nombre_e, cuit_e, tipo_e, telefono_e, email_e)
                        st.success("Cliente actualizado.")
                        st.rerun()

                if eliminar:
                    try:
                        delete_cliente(cid)
                        st.success("Cliente eliminado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se puede eliminar (puede tener presupuestos asociados): {e}")
