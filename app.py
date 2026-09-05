from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))


st.set_page_config(page_title="IES Manager", page_icon="🗂️", layout="wide")

st.markdown(
    """
    <style>
    .topbar {
        padding: 1.1rem 1.2rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #ff006f 0%, #0047ab 50%, #1a1a1a 100%);
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 6px 18px rgba(255,0,111,0.25);
    }
    .topbar-title { font-size: 1.8rem; font-weight: 700; line-height: 1.1; }
    .topbar-sub { font-size: 0.95rem; opacity: 0.95; margin-top: 0.35rem; }
    .section-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.5rem;
        font-weight: 700;
        margin-top: 0;
        margin-bottom: 0.5rem;
    }
    .panel-card {
        border-radius: 14px;
        padding: 1rem 1.1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .panel-card h3 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-top: 0;
    }
    @media (prefers-color-scheme: light) {
        .panel-card {
            background: #fff;
            border: 1px solid #f1e3d4;
            color: #333;
        }
    }
    @media (prefers-color-scheme: dark) {
        .panel-card {
            background: #1a1a2e;
            border: 1px solid #333;
            color: #e0e0e0;
        }
    }
    </style>
    <div class="topbar">
        <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.18em; opacity: 0.9; margin-bottom: 0.25rem;">Panel de gestión</div>
        <div class="topbar-title">IES Manager</div>
        <div class="topbar-sub">Gestión del día a día del departamento.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("")

# st.tabs no conserva la pestaña activa entre reruns (cada clic en un botón
# devuelve la vista a la primera pestaña), así que la navegación se hace con
# un widget normal atado a session_state para que sea persistente.
PAGES = ["Inicio", "Programación de aula"]
page = st.segmented_control(
    "Navegación",
    PAGES,
    default=PAGES[0],
    key="active_page",
    required=True,
    label_visibility="collapsed",
)

# PÁGINA: INICIO
if page == "Inicio":
    st.markdown('<div class="panel-card"><h3>Bienvenido</h3><p>Elige una sección arriba para empezar.</p></div>', unsafe_allow_html=True)

# PÁGINA: PROGRAMACIÓN DE AULA
elif page == "Programación de aula":
    st.markdown('<div class="panel-card"><h3>Programación de aula</h3><p>Se leerá un Excel con los datos del grupo y las situaciones de aprendizaje, y se generará el documento Word de la programación de aula.</p></div>', unsafe_allow_html=True)

    st.markdown("### Archivos")

    pa_excel = st.file_uploader(
        "Excel de datos (hojas 'Datos generales' y 'Situaciones de aprendizaje')",
        type=["xlsx", "xlsm"],
        key="pa_excel_uploader",
    )
    pa_template = st.file_uploader(
        "Plantilla Word (opcional, se usará la plantilla por defecto si no se sube)",
        type=["docx"],
        key="pa_template_uploader",
    )

    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Generar programación", use_container_width=True, type="primary", key="btn_gen_pa"):
            if pa_excel is None:
                st.error("Necesitas subir el Excel de datos.")
            else:
                try:
                    from tools.programacion_aula import run_programacion_aula

                    docx_bytes = run_programacion_aula(pa_excel, pa_template)
                    st.session_state.pa_docx = docx_bytes
                    st.success("Proceso completado.")
                except Exception as exc:
                    st.error(f"Error al generar la programación: {exc}")

    with col2:
        if st.button("Limpiar", use_container_width=True, key="btn_clear_pa"):
            st.session_state.pop("pa_docx", None)
            st.rerun()

    if st.session_state.get("pa_docx"):
        st.download_button(
            "Descargar programación (Word)",
            data=st.session_state.pa_docx,
            file_name="programacion_aula.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
