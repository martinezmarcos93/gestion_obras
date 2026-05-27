import altair as alt
import streamlit as st

from database import init_db, get_stats, get_seguimiento, get_facturacion_mensual
from utils import mostrar_boton_salir

st.set_page_config(
    page_title="Gestión de Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def inicializar():
    init_db()


inicializar()
mostrar_boton_salir()

# ── Estilos ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .big-metric { font-size: 2rem; font-weight: 700; }
    div[data-testid="stMetric"] { background:#fff; border-radius:10px; padding:1rem 1.2rem; box-shadow:0 1px 4px rgba(0,0,0,.08); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Encabezado ───────────────────────────────────────────────────────────────
st.title("🏗️ Gestión de Obras")
st.caption("Sistema de Presupuestos y Facturas — Maestro Mayor de Obras")

stats = get_stats()

# ── KPIs ─────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Trabajos activos",     stats["presupuestos_activos"])
c2.metric("Presupuestos pendientes", stats["presupuestos_pendientes"])
c3.metric("Facturas por cobrar",  stats["facturas_pendientes"])
c4.metric("Monto por cobrar",     f"${stats['monto_por_cobrar']:,.2f}")

st.divider()

# ── Cuerpo principal ──────────────────────────────────────────────────────────
col_izq, col_der = st.columns([3, 2])

with col_izq:
    st.subheader("Trabajos en Curso")
    df_seg = get_seguimiento()
    if df_seg.empty:
        st.info("No hay trabajos en curso. Aprobá un presupuesto para verlos aquí.")
    else:
        df_show = df_seg.copy()
        df_show["Monto Total"]    = df_show["monto_total"].map("${:,.2f}".format)
        df_show["Cobrado"]        = df_show["cobrado"].map("${:,.2f}".format)
        df_show["Saldo Pendiente"] = df_show["saldo_pendiente"].map("${:,.2f}".format)
        st.dataframe(
            df_show[["Cliente", "Descripcion", "Monto Total", "Cobrado", "Saldo Pendiente", "fecha_emision"]]
            .rename(columns={"fecha_emision": "Fecha"}),
            use_container_width=True,
            hide_index=True,
        )

with col_der:
    st.subheader("Facturación — Últimos 12 meses")
    df_mes = get_facturacion_mensual()
    if df_mes.empty:
        st.info("Sin facturas registradas aún.")
    else:
        df_chart = df_mes.melt("mes", ["cobrado", "pendiente"], var_name="Tipo", value_name="Monto")
        chart = (
            alt.Chart(df_chart)
            .mark_bar()
            .encode(
                x=alt.X("mes:N", title="Mes"),
                y=alt.Y("Monto:Q", title="$"),
                color=alt.Color(
                    "Tipo:N",
                    scale=alt.Scale(domain=["cobrado", "pendiente"], range=["#22c55e", "#f59e0b"]),
                ),
                tooltip=["mes", "Tipo", alt.Tooltip("Monto:Q", format="$,.2f")],
            )
            .properties(height=300)
        )
        st.altair_chart(chart, use_container_width=True)

st.divider()

# ── Resumen inferior ──────────────────────────────────────────────────────────
c5, c6 = st.columns(2)
c5.metric("Total cobrado (histórico)", f"${stats['total_cobrado']:,.2f}")
c6.metric("Clientes registrados",      stats["total_clientes"])
