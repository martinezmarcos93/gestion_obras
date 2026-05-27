from __future__ import annotations

import os
import streamlit as st


def mostrar_boton_salir():
    """Agrega el botón de salida en el sidebar. Llamar desde cada página."""
    with st.sidebar:
        st.divider()

        if "confirm_exit" not in st.session_state:
            st.session_state.confirm_exit = False

        if not st.session_state.confirm_exit:
            if st.button("🔴 Cerrar aplicación", use_container_width=True):
                st.session_state.confirm_exit = True
                st.rerun()
        else:
            st.warning("¿Cerrar la aplicación?")
            c1, c2 = st.columns(2)
            if c1.button("Sí, cerrar", type="primary", use_container_width=True):
                os._exit(0)
            if c2.button("Cancelar", use_container_width=True):
                st.session_state.confirm_exit = False
                st.rerun()
