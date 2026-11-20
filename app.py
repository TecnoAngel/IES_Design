from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))


def _favicon():
    """Marca propia y neutra para el icono de pestaña (cuadrado redondeado en
    los colores del tema). Sin escudos ni logotipos institucionales."""
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((8, 8, 120, 120), radius=26, fill=(15, 92, 168, 255))
        d.rounded_rectangle((30, 54, 98, 74), radius=10, fill=(230, 236, 243, 255))
        return img
    except Exception:
        return None


st.set_page_config(page_title="IES Diseño", page_icon=_favicon(), layout="wide")

# Aviso claro si se ha lanzado con el entorno equivocado (p. ej. el venv de otro
# proyecto que VSCode dejó activo): faltarían dependencias.
import importlib.util

_faltan = [
    m for m in ("matplotlib", "st_aggrid", "docxtpl")
    if importlib.util.find_spec(m) is None
]
if _faltan:
    st.error(
        "Faltan dependencias: **" + ", ".join(_faltan) + "**.\n\n"
        "Seguramente has lanzado la app con el entorno virtual de otro proyecto. "
        "Desde la carpeta del proyecto, ejecútala con su propio venv:\n\n"
        "```\n.\\.venv\\Scripts\\python.exe -m streamlit run app.py --server.port 8502\n```\n\n"
        "o directamente `.\\run_app.bat`. Si falta el venv: "
        "`python -m venv .venv ; .venv\\Scripts\\python.exe -m pip install -r requirements.txt`."
    )
    st.stop()

st.markdown(
    """
    <style>
    /* Paleta del tema: azul + plata + blanco. */
    :root {
        --c-azul: #0F5CA8;
        --c-azul-2: #1F7BD1;
        --c-acento: #4AA8E8;
        --c-tinta: #17212E;
        --c-plata: #F3F6FA;
        --c-linea: #D6DEE8;
    }
    .topbar {
        padding: 1.1rem 1.2rem;
        border-radius: 16px;
        background: linear-gradient(115deg, #0A3D73 0%, #1466B8 45%, #49A5E6 118%);
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 6px 18px rgba(15,92,168,0.28);
    }
    .topbar-title { font-size: 1.8rem; font-weight: 700; line-height: 1.1; }
    .topbar-sub { font-size: 0.95rem; opacity: 0.95; margin-top: 0.35rem; }
    .section-title {
        background: linear-gradient(120deg, var(--c-azul) 0%, var(--c-azul-2) 100%);
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
        box-shadow: 0 2px 10px rgba(15,92,168,0.10);
        background: #ffffff;
        border: 1px solid var(--c-linea);
        border-left: 4px solid var(--c-azul);
        color: #333333;
    }
    .panel-card h3 {
        background: linear-gradient(120deg, var(--c-azul) 0%, var(--c-azul-2) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-top: 0;
    }
    /* Cabecera de bloque dentro de una pestaña con varios apartados apilados. */
    .block-head {
        font-size: 1.12rem;
        font-weight: 700;
        color: #ffffff;
        background: linear-gradient(100deg, #0F5CA8 0%, #1B6FC2 70%, #49A5E6 140%);
        padding: 0.5rem 0.9rem;
        border-radius: 10px;
        margin: 1.6rem 0 0.7rem 0;
        box-shadow: 0 3px 10px rgba(15,92,168,0.22);
    }
    .block-head .block-sub {
        font-weight: 400;
        font-size: 0.8rem;
        opacity: 0.92;
        display: block;
        margin-top: 0.1rem;
    }
    /* Realza los contenedores con borde de Streamlit como "tarjetas". */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
        box-shadow: 0 2px 10px rgba(15,92,168,0.08);
    }
    /* Barra del proyecto abierto: una sola línea discreta, sin tarjeta. */
    .st-key-proybar {
        border-bottom: 1px solid var(--c-linea);
        padding-bottom: 0.35rem;
    }
    .st-key-proybar [data-testid="stMarkdownContainer"] { margin-bottom: 0; }
    .st-key-proybar .proy-info {
        font-size: 0.88rem; color: #556170;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .st-key-proybar .proy-info b { color: #1B2633; }
    .st-key-proybar [data-testid="stPopover"] button {
        min-height: 36px; padding: 0.2rem 0.8rem; font-size: 0.88rem;
    }
    /* Barra lateral de navegación: una entrada por página. */
    [data-testid="stSidebar"] {
        background: var(--c-plata);
        border-right: 1px solid var(--c-linea);
    }
    .side-brand {
        padding: 0.9rem 1rem;
        border-radius: 14px;
        background: linear-gradient(115deg, #0A3D73 0%, #1466B8 45%, #49A5E6 118%);
        color: #fff;
        margin-bottom: 1.1rem;
        box-shadow: 0 4px 12px rgba(15,92,168,0.22);
    }
    .side-brand .k {
        font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.16em; opacity: 0.9;
    }
    .side-brand .t { font-size: 1.35rem; font-weight: 700; line-height: 1.15; }
    /* Menú lateral: grupos numerados (.nav-grupo) y, dentro, una entrada por
       página (botones dentro del contenedor «menu»; la activa es la primaria). */
    .st-key-menu { gap: 0.15rem !important; }
    .st-key-menu [data-testid="stMarkdownContainer"] { margin-bottom: 0; }
    .nav-grupo {
        display: flex; align-items: center; gap: 0.5rem; margin: 0.9rem 0 0.2rem 0;
        font-size: 0.74rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.07em; color: #556170;
    }
    .nav-grupo .n {
        flex: none; width: 1.3rem; height: 1.3rem; border-radius: 50%;
        display: inline-flex; align-items: center; justify-content: center;
        background: var(--c-azul); color: #fff; font-size: 0.74rem; letter-spacing: 0;
    }
    .st-key-menu [data-testid="stButton"] button[kind="primary"],
    .st-key-menu [data-testid="stButton"] button[kind="secondary"] {
        width: 100% !important; justify-content: flex-start; text-align: left;
        min-height: 2.1rem; padding: 0.3rem 0.7rem 0.3rem 1.05rem; border-radius: 8px;
        border: 1px solid transparent; border-left: 4px solid transparent;
        background: transparent !important; box-shadow: none;
    }
    /* (el texto, a la izquierda: Streamlit lo centra en varios niveles) */
    .st-key-menu [data-testid="stButton"] button * { justify-content: flex-start; text-align: left; }
    .st-key-menu [data-testid="stButton"] button > div { width: 100%; }
    .st-key-menu [data-testid="stButton"] button p { font-size: 0.95rem; font-weight: 600; color: #1B2633; }
    .st-key-menu [data-testid="stButton"] button[kind="secondary"]:hover { background: #E4ECF5 !important; }
    .st-key-menu [data-testid="stButton"] button[kind="primary"] {
        background: #ffffff !important; border-color: var(--c-linea);
        border-left-color: var(--c-azul); box-shadow: 0 2px 8px rgba(15,92,168,0.10);
    }
    .st-key-menu [data-testid="stButton"] button[kind="primary"] p { color: var(--c-azul); }
    /* Pestañas de cada página (Situaciones, Criterios, …): selector
       segmentado. Un carril gris muy suave y, sobre él, la pestaña activa como
       una ficha blanca con el texto en azul; las demás, solo texto. Si no
       caben en una línea pasan a la siguiente dentro del mismo carril. */
    [data-testid="stTabs"] [role="tablist"] {
        display: flex;
        flex-wrap: wrap;
        gap: 2px;
        width: fit-content;
        max-width: 100%;
        padding: 4px;
        margin-bottom: 1.1rem;
        background: #EDF1F6;
        border: none;
        border-radius: 12px;
        overflow: visible;
    }
    [data-testid="stTabs"] [role="tab"] {
        height: auto !important;
        padding: 0.38rem 0.9rem !important;
        background: transparent;
        border: none !important;
        border-radius: 9px;
        cursor: pointer;
        transition: background-color 0.18s ease, box-shadow 0.18s ease;
    }
    [data-testid="stTabs"] [role="tab"] p {
        font-size: 0.9rem;
        font-weight: 500;
        color: #5A6675;
        white-space: nowrap;
        transition: color 0.18s ease;
    }
    [data-testid="stTabs"] [role="tab"]:hover { background: rgba(255,255,255,0.65); }
    [data-testid="stTabs"] [role="tab"]:hover p { color: var(--c-tinta); }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: #ffffff;
        box-shadow: 0 1px 2px rgba(15,30,50,0.10), 0 2px 6px rgba(15,30,50,0.07);
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] p {
        color: var(--c-azul);
        font-weight: 600;
    }
    [data-testid="stTabs"] [role="tab"]:focus-visible {
        outline: 2px solid var(--c-azul);
        outline-offset: 1px;
    }
    /* Fuera la raya del seleccionado y la línea del carril de Streamlit
       (en 1.63 son .react-aria-SelectionIndicator y el ::after del tablist). */
    [data-testid="stTabs"] .react-aria-SelectionIndicator,
    [data-testid="stTabs"] [data-baseweb="tab-highlight"],
    [data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }
    [data-testid="stTabs"] [role="tablist"]::after,
    [data-testid="stTabs"] [role="tablist"]::before { display: none !important; }
    .mini-label {
        font-size: 0.8rem;
        font-weight: 600;
        opacity: 0.78;
        margin-bottom: 0.2rem;
    }
    /* Navegación: pastilla activa en azul. */
    div[data-baseweb="segmented-control"] [aria-checked="true"],
    button[kind="segmented_controlActive"] {
        background: var(--c-azul) !important;
        color: #fff !important;
    }
    /* Panel de tics (CON/CT del indicador): se colorea en verde al marcar. */
    [class*="st-key-il_pick_box_"] {
        padding: 2px 6px;
        border-radius: 8px;
        transition: background-color 0.1s ease;
    }
    [class*="st-key-il_pick_box_"]:has(input:checked) {
        background: #dff2e2;
    }
    /* Paneles flotantes de resumen del indicador (contenidos, transversales,
       instrumento/agente/CC): etiquetas y tarjetas con el estilo del tema. */
    [data-testid="stDialog"] > div {
        border-top: 4px solid var(--c-azul);
        border-radius: 12px;
    }
    .il-chip {
        display: inline-block;
        background: var(--c-plata);
        border: 1px solid var(--c-linea);
        border-radius: 999px;
        padding: 3px 11px;
        margin: 2px 5px 2px 0;
        font-size: 0.82rem;
        line-height: 1.4;
    }
    .il-chip b { color: var(--c-azul); }
    .il-info-card {
        display: inline-block;
        min-width: 150px;
        background: #ffffff;
        border: 1px solid var(--c-linea);
        border-left: 4px solid var(--c-acento);
        border-radius: 10px;
        padding: 6px 14px;
        margin: 4px 10px 4px 0;
    }
    .il-info-card .lbl {
        font-size: 0.7rem;
        font-weight: 600;
        opacity: 0.7;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .il-info-card .val { font-size: 0.98rem; font-weight: 650; color: var(--c-tinta); }
    .il-dil-box {
        background: var(--c-plata);
        border-radius: 10px;
        padding: 8px 12px;
        font-size: 0.92rem;
        margin-bottom: 0.6rem;
    }
    /* ── Programación de aula: secciones, resumen de la SA y actividades.
       Grises con contraste ≥ 4,5:1 sobre blanco; el estado nunca va solo por
       color (siempre con texto). */
    .panel-card { margin-bottom: 0.9rem; }
    .pa-sec {
        display: flex; align-items: baseline; gap: 0.5rem;
        font-size: 1.1rem; font-weight: 700; color: var(--c-tinta);
        margin: 1.8rem 0 0.2rem 0; padding-bottom: 0.35rem;
        border-bottom: 2px solid var(--c-linea);
    }
    .pa-sec .n {
        font-size: 0.8rem; font-weight: 600; color: #556170;
        background: var(--c-plata); border: 1px solid var(--c-linea);
        border-radius: 999px; padding: 0 0.55rem;
    }
    .pa-sec-sub { font-size: 0.9rem; color: #556170; margin: 0.35rem 0 0.75rem 0; }
    .pa-tag {
        display: inline-block; font-size: 0.75rem; font-weight: 600; white-space: nowrap;
        border-radius: 999px; padding: 0.05rem 0.55rem; border: 1px solid;
    }
    .pa-tag.warn { background: #fff1cc; color: #7a4d00; border-color: #e3b04b; }
    .pa-tag.ok { background: #e3f3e6; color: #1e6b34; border-color: #9fd0a9; }
    .pa-tag.info { background: var(--c-plata); color: #556170; border-color: var(--c-linea); }
    /* Selector de situación de aprendizaje (Descripción SA y Actividades):
       banda azul, es la selección principal de la pestaña. */
    [class*="st-key-pasel_"] {
        background: linear-gradient(100deg, #0F5CA8 0%, #1B6FC2 100%);
        border-radius: 10px; padding: 0.55rem 0.9rem 0.75rem; margin-bottom: 0.2rem;
        box-shadow: 0 3px 10px rgba(15,92,168,0.18);
    }
    [class*="st-key-pasel_"] label p {
        color: #fff !important; font-size: 0.74rem !important; font-weight: 700 !important;
        text-transform: uppercase; letter-spacing: 0.1em;
    }
    [class*="st-key-pasel_"] [data-testid="stSelectbox"] [role="group"] {
        background: #fff !important; border: 1px solid var(--c-acento) !important;
        border-radius: 8px !important;
    }
    [class*="st-key-pasel_"] [data-testid="stSelectbox"] input {
        font-size: 1.05rem !important; font-weight: 700 !important; color: var(--c-tinta) !important;
        background: transparent !important;
    }
    /* Botones de toda la app: del ancho de su texto (no estirados a toda la
       columna, aunque lleven use_container_width), 36 px de alto y texto
       legible en negrita media. No toca los botones de solo icono (tertiary). */
    [data-testid="stButton"] button[kind="primary"], [data-testid="stButton"] button[kind="secondary"],
    [data-testid="stDownloadButton"] button {
        width: auto !important; min-height: 2.25rem; padding: 0.3rem 0.95rem; border-radius: 8px;
    }
    [data-testid="stButton"] button[kind="primary"] p, [data-testid="stButton"] button[kind="secondary"] p,
    [data-testid="stDownloadButton"] button p { font-size: 0.92rem; font-weight: 600; }
    /* Botones «Generar…»: centrados en altura con su cargador de plantilla. */
    .st-key-pa_gen, .st-key-fam_gen { margin-bottom: 1rem; }
    /* Vista en el cuaderno (iDoceo / Additio): columnas pastel por actividad.
       La tabla mide lo que ocupan sus columnas (no se estira a todo el ancho). */
    .cuad-wrap {
        display: inline-block; max-width: 100%; vertical-align: top;
        overflow-x: auto; background: #fff; border: 1px solid var(--c-linea);
        border-radius: 8px; margin: 0.2rem 0 0.4rem 0;
    }
    table.cuad { border-collapse: separate; border-spacing: 0; width: auto; margin: 0; font-size: 0.85rem; }
    .cuad th, .cuad td { border: none !important; }
    .cuad .alum {
        position: sticky; left: 0; z-index: 1; background: #fff; width: 6.5rem; min-width: 6.5rem;
        text-align: left; padding: 0 0.7rem; font-weight: 600; color: #556170; white-space: nowrap;
        box-shadow: inset -1px 0 0 var(--c-linea);
    }
    .cuad .alum.esq {
        vertical-align: bottom; padding-bottom: 0.5rem; font-size: 0.72rem;
        text-transform: uppercase; letter-spacing: 0.06em;
    }
    .cuad .act {
        vertical-align: top; text-align: left; padding: 0; width: 10.5rem; min-width: 10.5rem; max-width: 10.5rem;
        background: var(--bg); box-shadow: inset -1px 0 0 rgba(255,255,255,0.9);
    }
    .cuad .cab { border-top: 4px solid var(--franja); padding: 0.4rem 0.65rem 0.35rem; }
    .cuad .cod { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; color: var(--tinta); }
    .cuad .tit { font-size: 0.9rem; font-weight: 700; line-height: 1.25; color: var(--c-tinta); margin: 0.05rem 0 0.1rem; }
    .cuad .ie { font-size: 0.75rem; font-weight: 500; color: var(--tinta); }
    .cuad .ces {
        display: flex; flex-wrap: wrap; gap: 0.25rem; padding: 0.35rem 0.65rem 0.45rem;
        border-top: 1px dashed rgba(23,33,46,0.14);
    }
    .cuad .ce {
        background: rgba(255,255,255,0.8); border-radius: 7px; padding: 0.12rem 0.5rem;
        font-size: 0.8rem; font-weight: 700; color: var(--c-tinta); white-space: nowrap;
        font-variant-numeric: tabular-nums; box-shadow: 0 1px 2px rgba(23,33,46,0.06);
    }
    .cuad .ce .x { font-weight: 500; color: var(--tinta); margin: 0 0.25rem; }
    .cuad .ce.warn { background: #fff1cc; color: #7a4d00; box-shadow: inset 0 0 0 1px #e3b04b; }
    .cuad .vacio { font-size: 0.78rem; color: #556170; font-style: italic; }
    .cuad tbody .alum { height: 1.8rem; font-weight: 500; font-size: 0.8rem; border-top: 1px solid #E6ECF3 !important; }
    .cuad td.cel {
        background: var(--soft); border-top: 1px solid #fff !important;
        box-shadow: inset -1px 0 0 #fff;
    }
    .cuad td.cel::after {
        content: ""; display: block; width: 2.2rem; height: 0.42rem; margin: auto;
        border-radius: 4px; background: rgba(23,33,46,0.07);
    }
    </style>
    <div class="topbar">
        <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.18em; opacity: 0.9; margin-bottom: 0.25rem;">Programación didáctica</div>
        <div class="topbar-title">IES Diseño</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("")

# streamlit-aggrid se renderiza en un <iframe>: dentro de una pestaña oculta (o
# un st.expander plegado) puede montarse con ancho 0 y quedarse "en una
# columna". Este parche fuerza el ancho de esos iframes al 100 % y lanza un
# 'resize' para que AG-Grid recoloque las columnas, al cambiar de pestaña /
# abrir una sección y durante los primeros segundos.
components.html(
    """
    <script>
    (function () {
      const doc = window.parent.document;
      function nudge() {
        doc.querySelectorAll('iframe').forEach(f => {
          if (f.closest('[data-testid="stExpander"], [data-testid="stTabs"]')) {
            f.style.width = '100%';
            try { f.contentWindow.dispatchEvent(new Event('resize')); } catch (e) {}
          }
        });
        window.parent.dispatchEvent(new Event('resize'));
      }
      doc.addEventListener('click', e => {
        if (e.target.closest('summary, [role="tab"]')) { [60, 250, 600, 1200].forEach(t => setTimeout(nudge, t)); }
      }, true);
      let n = 0;
      const iv = setInterval(() => { nudge(); if (++n > 20) clearInterval(iv); }, 350);
    })();
    </script>
    """,
    height=0,
)

# Navegación principal en la barra lateral (widget atado a session_state, así
# que la página activa se conserva entre reruns). Dentro de cada página, los
# bloques van en st.tabs con key + on_change="rerun" (también persistentes).
# MENÚ: grupos y, dentro de cada uno, sus páginas como (id, etiqueta). El id
# es lo que se guarda en `active_page` y lo que miran los `if page == …` de
# abajo; para añadir una página basta una línea aquí y su bloque abajo.
NAV = [
    ("Programación didáctica", [
        ("Diseño de la programación", "Diseño de la programación"),
        ("Contenidos", "Contenidos"),
        ("Redacción", "Redacción"),
    ]),
    ("Programación de aula", [
        ("aula_datos", "Datos generales"),
        ("aula_sa", "Situaciones de aprendizaje"),
    ]),
    ("Generación de documentos", [
        ("doc_didactica", "Programación didáctica"),
        ("doc_aula", "Programación de aula"),
        ("doc_otros", "Otros informes"),
    ]),
]
# Páginas del menú anterior (una sesión abierta antes de un despliegue).
_PAG_ANTES = {"Programación de aula": "aula_datos", "Información a familias": "doc_otros"}
_pag_ids = [i for _g, _its in NAV for i, _e in _its]
_pag = st.session_state.get("active_page")
_pag = _PAG_ANTES.get(_pag, _pag)
st.session_state.active_page = _pag if _pag in _pag_ids else _pag_ids[0]


def _ir_a(pagina: str) -> None:
    st.session_state.active_page = pagina


with st.sidebar:
    st.markdown(
        '<div class="side-brand"><div class="k">Programación didáctica</div>'
        '<div class="t">IES Diseño</div></div>',
        unsafe_allow_html=True,
    )
    with st.container(key="menu"):
        for _gi, (_grupo, _items) in enumerate(NAV):
            st.markdown(
                f'<div class="nav-grupo"><span class="n">{_gi + 1}</span>{_grupo}</div>',
                unsafe_allow_html=True,
            )
            for _ii, (_pid, _etq) in enumerate(_items):
                st.button(
                    _etq, key=f"nav_{_gi}_{_ii}", use_container_width=True,
                    type="primary" if st.session_state.active_page == _pid else "secondary",
                    on_click=_ir_a, args=(_pid,),
                )
page = st.session_state.active_page

# ── Currículo común (curriculo.db, se descarga de GitHub) y proyecto del
#    docente (.sqlite): barra global para abrir / crear / guardar desde
#    cualquier página. La descarga se rellena luego (dl_box), cuando la página
#    activa ya ha recogido los cambios.
from tools import curriculo as cur
from tools import categorias as categorias_def
from tools import redaccion as red_def
from tools.indicadores_logro import recompute as il_recompute
from tools.info_familias import CAMPOS_KEYS as FAM_CAMPOS
from tools.programacion_aula_editor import desde_formato_antiguo
from ui import categorias as ui_categorias
from tools.proyecto import DATOS_CAMPOS, SA_CAMPOS, estado_vacio, guardar_proyecto, leer_proyecto
from tools.situaciones_aprendizaje import TRIMESTRES

SA_COLS = ["SA", "EV", "DSA", "HSA"]
IL_COLS = ["CE", "CED", "IL", "PIL", "PIL%", "DIL", "DO", "CON", "CT", "IE", "CC", "AE", "SA"]


@st.cache_resource(ttl=6 * 3600, show_spinner="Descargando el currículo…")
def _curriculo_db():
    return cur.obtener_curriculo()


@st.cache_data(show_spinner=False)
def _materia_curriculo(db: str, materia_id: str) -> dict:
    # La ruta de la caché no cambia al volver a descargar: se limpia a mano
    # cuando cambia el origen (ver abajo).
    return cur.cargar_materia(db, materia_id)


try:
    CUR_DB, CUR_ORIGEN = _curriculo_db()
except Exception as exc:
    st.error(f"No se puede cargar el currículo (curriculo.db): {exc}")
    st.stop()
if st.session_state.get("_cur_origen") != CUR_ORIGEN:
    _materia_curriculo.clear()
    st.session_state._cur_origen = CUR_ORIGEN
CUR_DB = str(CUR_DB)

with st.sidebar:
    st.caption(f"Currículo: {CUR_ORIGEN}")


def _hay_proyecto() -> bool:
    return "proy_materia" in st.session_state


def _cargar_estado(estado: dict, nombre: str) -> None:
    """Pasa a la sesión un proyecto (leído del .sqlite o recién creado) junto
    con el currículo de su materia, y descarta todo lo derivado del anterior."""
    ss = st.session_state
    curm = _materia_curriculo(CUR_DB, estado["materia_id"])
    ce_list = curm["ce_list"]

    ss.cur = curm
    ss.proy_materia = curm["materia"]
    ss.proy_nombre = nombre
    ss.prog_sello_cargado = estado.get("sello", "")

    ss.sa_df = pd.DataFrame(
        [[s["SA"], s["EV"], s["DSA"], s["HSA"]] for s in estado["situaciones"]], columns=SA_COLS
    )
    ss.sa_previstas = {t: float(estado["horas_previstas"].get(t, 0.0) or 0) for t in TRIMESTRES}
    ss.sa_fechas_trimestre = dict(estado["fechas_trimestre"])
    ss.sa_horas_dia = list(estado["horas_dia"])
    ss.sa_festivo_local = estado["festivo_local"]

    # Los criterios son los de la materia en el currículo: un peso de un CE
    # que ya no existe se descarta, y un CE nuevo empieza con P = 0.
    ss.il_ce_list = ce_list
    ss.il_ce_ced = curm["ce_ced"]
    ss.il_ce_p = {ce: float(estado["ce_p"].get(ce, 0) or 0) for ce in ce_list}
    ss.il_rows = il_recompute(estado["il_rows"], curm["ce_ced"], ce_list)
    ss.il_aux = curm["aux"]
    ss.il_categorias = categorias_def.normalizar(estado.get("categorias"))
    ss.elementos = curm["elementos"]

    ss.pa_datos = {k: estado["pa_datos"].get(k, "") for k in DATOS_CAMPOS}
    ss.pa_campos_datos = list(DATOS_CAMPOS)
    ss.pa_sa_campos = list(SA_CAMPOS)
    ss.pa_sa_cols = estado["pa_sa_cols"]
    ss.pa_acts = estado["pa_acts"] or desde_formato_antiguo(
        estado.get("pa_acts_antiguas", []), ss.il_rows
    )
    ss.pa_sa_edits = {}
    # Redacción de la programación didáctica: lo guardado en el proyecto sobre
    # los textos y tablas propuestos (ver tools/redaccion.py).
    ss.red = red_def.completar(estado.get("redaccion"), curm["materia"])

    ss.fam_campos = {k: estado["fam_campos"].get(k, "") for k in FAM_CAMPOS}

    # al cambiar de proyecto, se descartan los estados canónicos derivados
    for _k in (
        "prog_out", "sa_grid_rows", "ce_rows", "il_pending", "pa_docx", "pd_docx",
        "consist_seen", "fam_docx", "prog_msg", "ipf_obj_df", "il_filtro_sa",
        "pa_sa_actual",
    ):
        ss.pop(_k, None)
    # ...los widgets con estado propio (familias, campos de aula, datos
    # generales) y las fechas/horas por día/festivo local que hubiera
    # tecleado en la calculadora de sesiones (se recargan las guardadas en
    # este proyecto, o se vuelve a proponer el reparto automático si no tiene).
    for _k in [
        k for k in list(ss.keys())
        if k.startswith(("fam_w_", "pad_", "pasa_", "ses_tr", "ses_d", "paact_", "pa_new_", "redw_", "ilcat_"))
        or k in ("ses_loc", "ses_loc_on")
    ]:
        ss.pop(_k, None)


def _huella(f) -> str:
    """Nombre + hash del contenido: un proyecto con el mismo nombre pero
    distinto contenido también se recarga."""
    import hashlib

    return f"{f.name}|{hashlib.md5(f.getvalue()).hexdigest()}"


def _abrir_o_crear(apilado: bool) -> None:
    """Abrir un proyecto (.sqlite) o crear uno nuevo (etapa → curso → materia).
    Con `apilado` los desplegables van uno debajo de otro (caben en el
    desplegable «Cambiar de proyecto»); si no, en una fila."""
    _modo = st.segmented_control(
        "Proyecto", ["Abrir proyecto", "Nuevo proyecto"], default="Abrir proyecto",
        key="proy_modo", label_visibility="collapsed",
    )
    if _modo == "Nuevo proyecto":
        if apilado:
            n1 = n2 = n3 = n4 = st.container()
        else:
            n1, n2, n3, n4 = st.columns([1.5, 0.8, 2.6, 0.9], vertical_alignment="bottom")
        _etapa = n1.selectbox(
            "Etapa", cur.ETAPAS, format_func=lambda e: cur.ETAPA_NOMBRE[e], key="nuevo_etapa"
        )
        _curso = n2.selectbox(
            "Curso", cur.cursos(CUR_DB, _etapa), format_func=lambda c: f"{c}º", key="nuevo_curso"
        )
        _mats = {m["id"]: m["nombre"] for m in cur.materias(CUR_DB, _etapa, _curso)}
        _mid = n3.selectbox(
            "Materia", list(_mats), format_func=lambda i: _mats.get(i, i), key="nuevo_materia"
        )
        if n4.button("Crear", type="primary", use_container_width=True, key="nuevo_crear",
                     disabled=not _mid):
            _cargar_estado(estado_vacio(_materia_curriculo(CUR_DB, _mid)), _mid)
            # Un proyecto vacío aún no tiene SA ni indicadores: no se avisa
            # de coherencia hasta que se vuelva a abrir (o al generar Word).
            st.session_state.consist_seen = True
            st.rerun()
    else:
        proy_file = st.file_uploader(
            "Proyecto (.sqlite)", type=["sqlite", "db"], key="proy_uploader",
            label_visibility="collapsed",
        )
        # Solo se carga un archivo subido NUEVO (si no, al crear un proyecto
        # nuevo con un archivo aún en el uploader, lo volvería a pisar).
        if proy_file is not None and st.session_state.get("proy_file_seen") != _huella(proy_file):
            st.session_state.proy_file_seen = _huella(proy_file)
            try:
                _cargar_estado(leer_proyecto(proy_file.getvalue()), proy_file.name.rsplit(".", 1)[0])
            except Exception as exc:
                st.error(f"No se ha podido abrir el proyecto: {exc}")
            else:
                # Se vuelve a pintar ya con la barra compacta.
                st.rerun()


# Barra del proyecto. Sin proyecto, abrir/crear es lo único que se puede hacer
# y va a la vista. Con proyecto se queda en una sola línea: qué proyecto es,
# «Cambiar de proyecto» (desplegable con lo mismo) y «Guardar proyecto».
if _hay_proyecto():
    import html as _html

    with st.container(key="proybar"):
        ubar1, ubar2, ubar3 = st.columns([4.6, 2.1, 3.3], vertical_alignment="center")
        _m = st.session_state.proy_materia
        _det = f"{_m['curso']}º {cur.ETAPA_NOMBRE.get(_m['etapa_app'], _m['etapa'])}"
        if st.session_state.get("prog_sello_cargado"):
            _det += f" · guardado {st.session_state.prog_sello_cargado}"
        _tit = f"{_m['nombre']} · {_det}" + (f" · {_m['normativa']}" if _m.get("normativa") else "")
        ubar1.markdown(
            f'<div class="proy-info" title="{_html.escape(_tit, quote=True)}">'
            f'<b>{_html.escape(_m["nombre"])}</b> · {_html.escape(_det)}</div>',
            unsafe_allow_html=True,
        )
        with ubar2.popover("Cambiar de proyecto"):
            _abrir_o_crear(apilado=True)
        dl_box = ubar3.container()
else:
    with st.container(border=True):
        _abrir_o_crear(apilado=False)
    dl_box = st.container()
# Una sesión abierta con la versión anterior (el servidor recarga el código
# sin perder la sesión, y el mismo archivo no se vuelve a leer) puede traer
# actividades de un solo IL, sin «id»: se convierten aquí.
if _hay_proyecto() and any("id" not in a for a in st.session_state.get("pa_acts", [])):
    st.session_state.pa_acts = desde_formato_antiguo(
        st.session_state.pa_acts, st.session_state.get("il_rows", [])
    )
# Lo mismo con la redacción: una sesión anterior a ese apartado no la trae.
if _hay_proyecto() and "red" not in st.session_state:
    st.session_state.red = red_def.completar(None, st.session_state.proy_materia)


def _trimestre_txt(ev):
    try:
        n = int(ev)
    except (TypeError, ValueError):
        return ""
    return f"{n}º trimestre" if n in (1, 2, 3) else ""


def _sa_filas():
    """Filas de la tabla de situaciones: del estado editado si lo hay, si no
    las del proyecto cargado."""
    ss = st.session_state
    rows = ss.get("sa_grid_rows")
    if rows is None and "sa_df" in ss:
        rows = [
            {
                "SA": None if pd.isna(v[0]) else int(v[0]),
                "EV": None if pd.isna(v[1]) else int(v[1]),
                "DSA": str(v[2] or ""),
                "HSA": None if pd.isna(v[3]) else v[3],
            }
            for v in ss.sa_df.itertuples(index=False)
        ]
    return [{k: r.get(k) for k in SA_COLS} for r in (rows or [])]


def _sa_datos():
    """(nº, descripción, trimestre) de cada SA, ordenados por nº."""
    return sorted(
        (r["SA"], r["DSA"], _trimestre_txt(r.get("EV")))
        for r in _sa_filas() if r.get("SA") is not None
    )


def _sa_pares():
    return [(n, d) for n, d, _t in _sa_datos()]


def _codigos_curriculo() -> dict[str, set[str]]:
    el = st.session_state.get("elementos", {})
    return {
        "CON": {c["cod"].replace(" ", "") for c in el.get("contenidos", [])},
        "CT": {c["num"] for c in el.get("transversales", [])},
        "DO": {c["cod"] for c in el.get("descriptores", [])},
    }


def _estado_coherencia():
    ss = st.session_state
    sits = [{"SA": n, "DSA": d} for n, d in _sa_pares()]
    return (
        sits,
        ss.get("il_ce_list", []),
        ss.get("il_rows", []),
        ss.get("pa_acts", []),
        _codigos_curriculo(),
    )


def _estado_actual() -> dict:
    """Todo lo que hay en sesión, en el formato de `tools.proyecto`."""
    ss = st.session_state
    _fechas_prev = ss.get("sa_fechas_trimestre", {})
    _horas_prev = ss.get("sa_horas_dia") or [None] * 5
    il_g = il_recompute(ss.get("il_pending", ss.get("il_rows", [])), ss.il_ce_ced, ss.il_ce_list)
    return {
        "situaciones": _sa_filas(),
        "horas_previstas": {
            t: float(ss.get(f"sa_prev_{t}", ss.get("sa_previstas", {}).get(t, 0.0)))
            for t in TRIMESTRES
        },
        # Fechas de cada evaluación, horas por día y festivo local
        # (calculadora de sesiones): lo que haya en sus selectores si se ha
        # abierto esta sesión, si no lo que ya tuviera guardado el proyecto.
        # El festivo se limpia explícitamente si se desmarca la casilla.
        "fechas_trimestre": {
            t: (
                ss.get(f"ses_tr{t - 1}a", _fechas_prev.get(t, (None, None))[0]),
                ss.get(f"ses_tr{t - 1}b", _fechas_prev.get(t, (None, None))[1]),
            )
            for t in TRIMESTRES
        },
        "horas_dia": [ss.get(f"ses_d{i}", _horas_prev[i]) for i in range(5)],
        "festivo_local": (
            (ss.get("ses_loc") if ss.get("ses_loc_on") else None)
            if "ses_loc_on" in ss
            else ss.get("sa_festivo_local")
        ),
        "ce_p": {r["CE"]: r["P"] for r in ss.get("ce_rows", [])} or dict(ss.il_ce_p),
        "il_rows": il_g,
        "categorias": ss.get("il_categorias", []),
        "pa_datos": dict(ss.get("pa_datos", {})),
        "pa_sa_cols": ss.get("pa_sa_cols", []),
        "pa_acts": ss.get("pa_acts", []),
        "fam_campos": dict(ss.get("fam_campos", {})),
        "redaccion": ss.get("red") or {},
    }


def _datos_redaccion() -> dict:
    """Lo que necesitan las tablas y gráficas automáticas de la programación
    didáctica (Redacción y su Word), con lo que hay ahora en Diseño."""
    ss = st.session_state
    return red_def.preparar(
        cur=ss.cur,
        sits=_sa_filas(),
        il_rows=il_recompute(ss.get("il_pending", ss.get("il_rows", [])), ss.il_ce_ced, ss.il_ce_list),
        ce_p={r["CE"]: r["P"] for r in ss.get("ce_rows", [])} or dict(ss.get("il_ce_p", {})),
    )


def _guardar_todo() -> bytes:
    """Bytes del proyecto (.sqlite) con todos los cambios en sesión."""
    ss = st.session_state
    data, ss.prog_sello = guardar_proyecto(
        _estado_actual(), ss.proy_materia, pa_sa_edits=ss.get("pa_sa_edits", {})
    )
    return data


def _invalidar_prog_out() -> None:
    """Fuerza a que el próximo render recalcule el proyecto (ver dl_box): lo usan
    como `on_change` los campos de la calculadora de sesiones (horas por día,
    fechas de evaluación, festivo local) porque, al ser simples widgets sin
    un botón «Actualizar» propio, nada más los invalidaría — y con el cálculo
    ahora automático (sin botón intermedio, ver dl_box) un valor tecleado ahí
    se quedaría sin guardar hasta la próxima edición en otro sitio."""
    st.session_state.pop("prog_out", None)


def _nombre_sin_sello(nombre: str) -> str:
    """Quita del principio de un nombre de archivo el/los «AAAAMMDD_HHMM_» que
    le hubiera puesto una descarga anterior de esta app (uno o varios, por si
    el nombre ya venía con más de uno acumulado), para que un guardado
    repetido sobre el mismo archivo no siga acumulando sellos."""
    return re.sub(r"^(?:\d{8}_\d{4}_)+", "", nombre)


# JavaScript del botón «Guardar proyecto» (ver _guardar_archivo_html).
#
# El guardado NO se hace dentro del iframe del botón sino en una función que se
# deja en la página (window.parent.__iesGuardar), por esto: si el docente pulsa
# Guardar con el cursor todavía dentro de un campo de texto, Streamlit recibe
# ese texto justo entonces, vuelve a ejecutar la app y cambia este iframe por
# uno nuevo con el proyecto actualizado. El iframe viejo (y su JavaScript)
# desaparece a mitad del clic y guardaría el proyecto de antes. La función de
# la página sobrevive al cambio: espera a que Streamlit termine y guarda lo que
# haya publicado el iframe más reciente en window.parent.__iesDatos.
_JS_GUARDAR = r"""
(function () {
    const pagina = window.parent;
    pagina.__iesDatos = __DATOS__;      // el proyecto más reciente
    const btn = document.getElementById("iesSaveBtn");

    pagina.__iesGuardar = new pagina.Function(`
        const pausa = (ms) => new Promise((r) => setTimeout(r, ms));
        const conTiempo = (promesa, ms) => Promise.race([
            promesa, new Promise((_, rej) => setTimeout(() => rej(new Error("tiempo agotado")), ms)),
        ]);
        // El mensaje se escribe en el iframe del botón que haya en ese momento.
        const decir = (texto, color) => {
            const f = document.querySelector(".st-key-proybar iframe");
            const m = f && f.contentDocument && f.contentDocument.getElementById("iesSaveMsg");
            if (m) { m.textContent = texto; m.title = texto; m.style.color = color || "#556170"; }
        };
        const ejecutando = () => {
            const app = document.querySelector('[data-testid="stApp"]');
            return !!app && app.getAttribute("data-test-script-state") === "running";
        };
        return (async () => {
            if (window.__iesGuardando) return;
            window.__iesGuardando = true;
            try {
                // 1. Dar tiempo a que llegue a Streamlit lo último tecleado y
                //    esperar a que termine de recalcular (máx. ~4 s: el permiso
                //    del navegador para abrir «Guardar como» caduca a los 5 s).
                const t0 = Date.now();
                await pausa(300);
                let hubo = false;
                while (Date.now() - t0 < 4000 && ejecutando()) { hubo = true; await pausa(80); }
                if (hubo) await pausa(350);   // que el botón nuevo publique sus datos

                // 2. Guardar lo más reciente.
                const datos = window.__iesDatos;
                const bin = atob(datos.b64);
                const bytes = new Uint8Array(bin.length);
                for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
                // Sello AAAAMMDD_HHMM con la hora real del clic.
                const d = new Date();
                const pad = (n) => String(n).padStart(2, "0");
                const fname = "" + d.getFullYear() + pad(d.getMonth() + 1) + pad(d.getDate())
                    + "_" + pad(d.getHours()) + pad(d.getMinutes()) + "_" + datos.base + datos.ext;

                const descargar = () => {
                    const url = URL.createObjectURL(new Blob([bytes], {type: datos.mime}));
                    const a = document.createElement("a");
                    a.href = url; a.download = fname;
                    document.body.appendChild(a); a.click(); a.remove();
                    setTimeout(() => URL.revokeObjectURL(url), 4000);
                    decir("Descargado como " + fname + ".", "#2e7d32");
                };
                if ("showSaveFilePicker" in window) {
                    // Chrome / Edge: elige dónde, puede sobrescribir el original.
                    let handle;
                    try {
                        handle = await window.showSaveFilePicker({
                            suggestedName: fname,
                            types: [{description: datos.desc, accept: {[datos.mime]: [datos.ext]}}],
                        });
                    } catch (err) {
                        if (err && err.name === "AbortError") { decir(""); return; }
                        descargar();   // sin permiso para el selector: descarga normal
                        return;
                    }
                    const writable = await conTiempo(handle.createWritable(), 6000);
                    await conTiempo(writable.write(bytes), 10000);
                    await conTiempo(writable.close(), 6000);
                    decir("Guardado en " + handle.name + ".", "#2e7d32");
                } else {
                    descargar();       // Firefox / Safari
                }
            } catch (err) {
                decir("No se ha podido guardar: " + ((err && err.message) || err), "#c62828");
            } finally {
                window.__iesGuardando = false;
            }
        })();
    `);

    btn.addEventListener("click", () => { pagina.__iesGuardar(); });
})();
"""


def _guardar_archivo_html(
    data: bytes, base: str, *, ext: str = ".sqlite", etiqueta: str = "Guardar proyecto",
    descripcion: str = "Proyecto de IES Diseño", mime: str = "application/vnd.sqlite3",
    height: int = 38,
) -> None:
    """Un único botón «Guardar proyecto»: si el navegador soporta elegir dónde
    guardar (Chrome/Edge, la File System Access API) abre el explorador de
    archivos del sistema para que lo guardes donde quieras, incluso
    sobrescribiendo el original; si no (Firefox, Safari…) hace una descarga
    normal a la carpeta de Descargas. Todo en el mismo botón, decidido por JS
    con un `if` — nada que configurar ni detectar desde Python.

    Va en HTML/JS puro (un `st.button` no sirve: la API de guardar exige un
    gesto de usuario síncrono en el propio DOM). No recuerda el archivo entre
    guardados —eso fue lo que se quedaba colgado en un intento anterior—: cada
    clic vuelve a preguntar dónde. Los pasos de escritura llevan un tiempo
    límite por si acaso; el propio diálogo de elegir archivo no (ahí esperar a
    que decidas es normal, no un cuelgue).

    El guardado en sí lo hace una función que se deja en la página, no el
    iframe del botón: así se guarda también lo que se acaba de teclear en un
    campo del que aún no se ha salido (ver ``_JS_GUARDAR``).

    El botón se pinta una sola vez (mientras no cambien los datos) y luego se
    puede pulsar varias veces sin que Streamlit vuelva a ejecutar Python —por
    eso el sello de fecha/hora del NOMBRE se calcula aquí, en JS, en el propio
    instante del clic (`base` ya viene sin sellos previos); así cada guardado
    propone un nombre con la hora real de ese guardado, no la de cuando se
    generó el archivo. El sello DENTRO del proyecto (``meta.actualizado``) es
    otra cosa y sigue siendo el de la última vez que se generó."""
    import base64
    import html
    import json

    payload = json.dumps({
        "b64": base64.b64encode(data).decode("ascii"), "base": base, "ext": ext,
        "mime": mime, "desc": descripcion,
    })
    js = _JS_GUARDAR.replace("__DATOS__", payload)
    components.html(
        f"""
        <style>
        body {{ margin: 0; display: flex; align-items: center; gap: 10px; height: 38px; }}
        .ies-save-btn {{
            flex: none; min-height: 36px; padding: 0.3rem 1rem; border-radius: 8px; border: none;
            background: #0F5CA8; color: #fff; font-weight: 600; font-size: 0.92rem;
            font-family: "Source Sans Pro", sans-serif; cursor: pointer;
        }}
        .ies-save-btn:hover:not(:disabled) {{ background: #0A4A8C; }}
        .ies-save-btn:disabled {{ background: #CFD6DE; color: #66717E; cursor: not-allowed; }}
        /* El mensaje va a la derecha del botón, en una línea (entero en el title). */
        .ies-save-msg {{
            font-size: 0.78rem; font-family: "Source Sans Pro", sans-serif; min-width: 0;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }}
        </style>
        <button id="iesSaveBtn" class="ies-save-btn">{html.escape(etiqueta)}</button>
        <div id="iesSaveMsg" class="ies-save-msg"></div>
        <script>{js}</script>
        """,
        height=height,
    )


def _resumen_por_sa_docx():
    """Para el .docx: por cada SA (por título), sus indicadores y el resumen de
    actividades (valor s/ programación y s/ SA) tal cual se ven en pantalla."""
    from tools.programacion_aula_editor import valores_actividades

    ss = st.session_state
    il_state = il_recompute(
        ss.get("il_pending", ss.get("il_rows", [])), ss.il_ce_ced, ss.il_ce_list
    )
    ce_p = {r["CE"]: r["P"] for r in ss.get("ce_rows", [])} or dict(ss.get("il_ce_p", {}))
    val = valores_actividades(ss.get("pa_acts", []), il_state, ce_p)

    out = {}
    for n, dsa, _t in _sa_datos():
        out[dsa] = {
            "indicadores": [
                {c: r.get(c) for c in ("CE", "IL", "CT", "IE", "CC", "AE")}
                for r in il_state if r.get("SA") == n
            ],
            "actividades": [
                {
                    "A": a["A"], "DA": a["titulo"], "IE": a["IE"], "IL": a["ILs"],
                    "valor_programacion": a["valor_prog"], "valor_sa": a["valor_sa"],
                }
                for a in val if a.get("SA") == n
            ],
        }
    return out


def _generar_docx() -> bytes:
    """Word de la programación de aula con lo que hay en sesión."""
    from tools.programacion_aula import run_programacion_aula
    from tools.proyecto import norm_titulo

    ss = st.session_state
    edits = {norm_titulo(k): v for k, v in ss.get("pa_sa_edits", {}).items()}
    previos = {
        norm_titulo(c.get("valores", {}).get("titulo")): c.get("valores", {})
        for c in ss.get("pa_sa_cols", [])
    }
    situaciones = []
    for n, dsa, tri in _sa_datos():
        vals = edits.get(norm_titulo(dsa)) or previos.get(norm_titulo(dsa)) or {}
        sit = {campo: vals.get(campo, "") for campo in ss.get("pa_sa_campos", [])}
        sit.update(numero=n, titulo=dsa, trimestre=tri)
        situaciones.append(sit)
    return run_programacion_aula(
        dict(ss.get("pa_datos", {})),
        situaciones,
        ss.get("pa_tpl"),
        resumen_por_sa=_resumen_por_sa_docx(),
    )


def _tabla_html(headers, rows, *, alto=None) -> str:
    """Tabla HTML de solo lectura a todo el ancho (el estilo de «Copiar tabla
    (Word)»); con `alto`, con barra de desplazamiento. Sustituye a st.dataframe
    donde en algunos navegadores el <canvas> de Streamlit salía en negro."""
    from tools.situaciones_informe import render_word_table_html

    tabla = render_word_table_html(headers, rows).replace(
        '<table style="border-collapse:collapse;">',
        '<table style="border-collapse:collapse;width:100%;font-size:0.9rem;">', 1,
    )
    estilo = f"max-height:{alto}px;overflow-y:auto;" if alto else ""
    return f'<div style="{estilo}overflow-x:auto;margin-bottom:0.6rem">{tabla}</div>'


def _seccion(titulo, n=None, sub=None):
    """Título de sección dentro de una pestaña (con contador opcional y una
    línea explicativa debajo)."""
    from html import escape as _esc

    cnt = f'<span class="n">{n}</span>' if n is not None else ""
    st.markdown(
        f'<div class="pa-sec" role="heading" aria-level="3">{_esc(titulo)}{cnt}</div>'
        + (f'<div class="pa-sec-sub">{_esc(sub)}</div>' if sub else ""),
        unsafe_allow_html=True,
    )


def _pestanas(key, titulos):
    """Pestañas de una página. Con `key` + `on_change="rerun"` la pestaña activa
    se conserva entre reruns (Añadir/Borrar/Actualizar no devuelven a la
    primera) y cada contenedor expone `.open`. OJO: en «Diseño» el cuerpo de
    TODAS las pestañas se ejecuta siempre (no se mira `.open`) porque unas
    usan variables que definen otras (`sits`, `ce_p`, `pending`).
    Al cambiar de página en la barra lateral el widget no se pinta y Streamlit
    borra su estado; la última pestaña se guarda aparte (`_last_<key>`) para
    volver a ella."""
    ss = st.session_state
    last = f"_last_{key}"

    def _recordar():
        ss[last] = ss[key]

    default = ss.get(last) if ss.get(last) in titulos else None
    return st.tabs(titulos, key=key, default=default, on_change=_recordar)


class _Zona:
    """Hace de pestaña para un apartado que ya no va en pestañas porque tiene
    su entrada en el menú: `with zona:` no hace nada y `.open` dice si toca
    pintarlo en la página actual."""

    def __init__(self, abierta: bool = False):
        self.open = abierta

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _calc_sesiones_por_evaluacion():
    """Pestaña «Sesiones por evaluación» de Diseño: con el calendario
    escolar oficial de Castilla y León y las sesiones de la materia por día de la
    semana, cuenta día a día los días lectivos y las sesiones de cada evaluación.
    El resultado puede volcarse a las «horas previstas» de cada trimestre."""
    from datetime import date as _date  # noqa: F401  (por si se usa en el futuro)

    ss = st.session_state
    ss.setdefault("sa_previstas", {})

    from tools.sesiones_calendario import (
        DEFAULT_CALENDAR_URL,
        DIAS_SEMANA,
        contar_evaluacion,
        default_trimester_ranges,
        fetch_school_calendar,
    )

    st.caption(
        "Cuenta día a día los días lectivos de cada evaluación según el calendario "
        "escolar de Castilla y León y, con las sesiones que tengas cada día de la "
        "semana, las sesiones totales de tu materia. El resultado se puede volcar a "
        "«horas previstas»."
    )

    u1, u2 = st.columns([3, 1])
    url = u1.text_input("URL del calendario (JCyL)", value=DEFAULT_CALENDAR_URL, key="ses_url")
    if u2.button("Cargar calendario", use_container_width=True, key="ses_load"):
        for k in [k for k in list(ss.keys()) if k.startswith(("ses_tr", "ses_hol")) or k == "ses_loc"]:
            ss.pop(k, None)
        try:
            ss.ses_cal = fetch_school_calendar(url)
            st.success("Calendario cargado.")
        except Exception as exc:
            ss.pop("ses_cal", None)
            st.error(f"No se ha podido leer el calendario: {exc}")

    cal = ss.get("ses_cal")
    if cal is None:
        st.info("Carga el calendario oficial para calcular.")
        return

    st.markdown(
        f"**Curso ESO:** {cal.course_start:%d/%m/%Y} – {cal.course_end:%d/%m/%Y}  \n"
        f"**Navidad:** {min(cal.christmas_days):%d/%m/%Y} – {max(cal.christmas_days):%d/%m/%Y} · "
        f"**Semana Santa:** {min(cal.easter_days):%d/%m/%Y} – {max(cal.easter_days):%d/%m/%Y}"
    )

    st.markdown(
        '<div class="mini-label">Sesiones de la materia por día de la semana '
        "(normalmente 0, 1 o 2)</div>",
        unsafe_allow_html=True,
    )
    # Si el proyecto ya trae horas por día guardadas se proponen esas; si no, 0.
    _horas_guardadas = ss.get("sa_horas_dia") or [None] * 5
    dcols = st.columns(5)
    ses_dia = {
        i: dc.number_input(
            nom, min_value=0, max_value=6, step=1,
            value=int(ss.get(f"ses_d{i}", _horas_guardadas[i] or 0)), key=f"ses_d{i}",
            on_change=_invalidar_prog_out,
        )
        for i, (dc, nom) in enumerate(zip(dcols, DIAS_SEMANA))
    }

    # Si el proyecto ya trae fechas guardadas se proponen esas; si no —o caen
    # fuera del curso del calendario cargado—, el reparto automático en
    # torno a Navidad y Semana Santa.
    def _en_curso(d):
        return d is not None and cal.course_start <= d <= cal.course_end

    deftr_auto = default_trimester_ranges(cal)
    _guardadas = ss.get("sa_fechas_trimestre", {})
    deftr = []
    hay_guardadas = False
    for i in range(3):
        ini_g, fin_g = _guardadas.get(i + 1, (None, None))
        ini = ini_g if _en_curso(ini_g) else deftr_auto[i][0]
        fin = fin_g if _en_curso(fin_g) else deftr_auto[i][1]
        hay_guardadas = hay_guardadas or _en_curso(ini_g) or _en_curso(fin_g)
        deftr.append((ini, fin))

    st.markdown(
        '<div class="mini-label">Fechas de cada evaluación '
        + (
            "(las que ya tenías guardadas en este proyecto; ajústalas si hace falta)"
            if hay_guardadas
            else "(se proponen en torno a Navidad y Semana Santa; ajústalas si hace falta)"
        )
        + "</div>",
        unsafe_allow_html=True,
    )
    trcols = st.columns(3)
    rangos = []
    for i, (tc, lbl) in enumerate(zip(trcols, ("1ª evaluación", "2ª evaluación", "3ª evaluación"))):
        with tc:
            st.markdown(f"**{lbl}**")
            a = st.date_input(
                "Inicio", value=ss.get(f"ses_tr{i}a", deftr[i][0]),
                min_value=cal.course_start, max_value=cal.course_end,
                key=f"ses_tr{i}a", format="DD/MM/YYYY", on_change=_invalidar_prog_out,
            )
            b = st.date_input(
                "Fin", value=ss.get(f"ses_tr{i}b", deftr[i][1]),
                min_value=cal.course_start, max_value=cal.course_end,
                key=f"ses_tr{i}b", format="DD/MM/YYYY", on_change=_invalidar_prog_out,
            )
            rangos.append((a, b))
    st.caption(
        "Las horas por día, estas fechas y el festivo local se guardan en "
        "el proyecto — la próxima vez no hace falta volver a pensarlas."
    )

    extra = set()
    if cal.other_holidays:
        st.markdown(
            '<div class="mini-label">Festivos y días no lectivos a descontar</div>',
            unsafe_allow_html=True,
        )
        for i, g in enumerate(cal.other_holidays):
            rng = (
                f"{g.start:%d/%m/%Y}" if g.start == g.end
                else f"{g.start:%d/%m/%Y} – {g.end:%d/%m/%Y}"
            )
            if st.checkbox(f"{g.name}  ({rng})", value=ss.get(f"ses_hol{i}", True), key=f"ses_hol{i}"):
                extra |= g.days

    # Si el proyecto ya trae un festivo local guardado y cae dentro del
    # curso del calendario cargado, se propone activado con esa fecha.
    _festivo_guardado = ss.get("sa_festivo_local")
    _festivo_en_curso = _festivo_guardado is not None and cal.course_start <= _festivo_guardado <= cal.course_end
    loc = None
    if st.checkbox(
        "Añadir fiesta local", value=ss.get("ses_loc_on", _festivo_en_curso), key="ses_loc_on",
        on_change=_invalidar_prog_out,
    ):
        loc = st.date_input(
            "Fecha de la fiesta local",
            value=ss.get("ses_loc", _festivo_guardado if _festivo_en_curso else cal.course_start),
            min_value=cal.course_start, max_value=cal.course_end,
            key="ses_loc", format="DD/MM/YYYY", on_change=_invalidar_prog_out,
        )

    margen = st.slider(
        "Margen de seguridad (% de sesiones que se prevé perder: excursiones, "
        "actividades, imprevistos…)",
        min_value=0, max_value=50, value=int(ss.get("ses_margen", 10)), step=1,
        key="ses_margen",
    )
    factor = margen / 100

    no_lectivos = cal.holiday_days | extra | ({loc} if loc else set())
    resultados = [contar_evaluacion(a, b, ses_dia, no_lectivos, factor) for a, b in rangos]

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Evaluación": lbl,
                    "Días lectivos": c.dias_lectivos,
                    "Días con clase": c.dias_con_clase,
                    "Sesiones": c.sesiones,
                    f"Sesiones −{margen}%": c.sesiones_ajustadas,
                    "Festivos restados": c.festivos_restados,
                }
                for lbl, c in zip(("1ª", "2ª", "3ª"), resultados)
            ]
        ),
        hide_index=True, use_container_width=True,
    )
    st.caption(
        f"Total curso: **{sum(c.sesiones for c in resultados)} sesiones** "
        f"({sum(c.sesiones_ajustadas for c in resultados)} con el margen) · "
        f"{sum(c.dias_lectivos for c in resultados)} días lectivos"
    )

    ss._ses_prev = {
        tri: float(c.sesiones_ajustadas) for tri, c in zip(TRIMESTRES, resultados)
    }

    def _volcar():
        for tri, val in st.session_state.get("_ses_prev", {}).items():
            st.session_state[f"sa_prev_{tri}"] = val
            st.session_state.sa_previstas[tri] = val
        st.session_state.pop("prog_out", None)

    st.button(
        f"Usar estas sesiones (con el margen del {margen}%) como horas previstas "
        "de cada trimestre",
        key="ses_apply", type="primary", on_click=_volcar,
    )


def _ipf_cargar(p_por_ce, pil_por_il, ce_ced, ce_list):
    """Vuelca a las tablas en sesión los pesos sugeridos por el IPF y remonta las
    rejillas afectadas (mismo patrón que el botón «Actualizar»)."""
    ss = st.session_state
    if p_por_ce is not None:
        cur = {r["CE"]: r["P"] for r in ss.get("ce_rows", [])}
        pairs = [(ce, float(p_por_ce.get(ce, cur.get(ce, 0.0)))) for ce in ce_list]
        total = sum(v for _, v in pairs)
        ss.ce_rows = [
            {"CE": ce, "CED": ce_ced.get(ce, ""), "P": p,
             "PCT": (p / total if (p and total) else 0.0)}
            for ce, p in pairs
        ]
        ss.il_ce_p = {ce: p for ce, p in pairs}
        ss.ce_nonce = ss.get("ce_nonce", 0) + 1
    if pil_por_il is not None:
        nuevas = []
        for r in ss.get("il_rows", []):
            r2 = dict(r)
            if r.get("IL") in pil_por_il:
                r2["PIL"] = pil_por_il[r["IL"]]
            nuevas.append(r2)
        ss.il_rows = il_recompute(nuevas, ce_ced, ce_list)
        ss.il_pending = list(ss.il_rows)
        ss.il_nonce = ss.get("il_nonce", 0) + 1
    ss.pop("prog_out", None)
    _que = "P y PIL" if (p_por_ce is not None and pil_por_il is not None) else (
        "P de los criterios" if p_por_ce is not None else "PIL de los indicadores")
    ss.ipf_msg = f"Cargados los pesos sugeridos ({_que}). Las tablas y gráficos se han actualizado."
    st.rerun()


def _ajuste_pesos_ipf(il_rows, ce_list, ce_ced, ce_p, sits):
    """Herramienta colapsable (entre Indicadores de logro y la matriz CE×SA):
    fija el % objetivo de cada instrumento de evaluación y, con el reparto de
    horas como restricción, itera (IPF) hasta aproximar los pesos P de los
    criterios y los PIL de los indicadores. No toca las tablas: el profesor
    decide si carga la propuesta."""
    from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
    from tools.situaciones_informe import AGGRID_GRID_CSS
    from tools.ajuste_pesos import (
        instrumentos_presentes,
        reparto_horario,
        reparto_ie_actual,
        sugerir_pesos,
    )

    ss = st.session_state

    if ss.pop("ipf_msg", None):
        st.success("Pesos cargados: las tablas y los gráficos ya están actualizados.")

    if not reparto_horario(sits):
        st.info("Las situaciones de aprendizaje no tienen horas.")
        return

    presentes = instrumentos_presentes(il_rows)
    lista_ie = list(ss.get("il_aux", {}).get("IE", []))
    ies = presentes + [ie for ie in lista_ie if ie not in presentes]
    if not ies:
        st.info("Todavía no hay indicadores con instrumento de evaluación asignado.")
        return

    actual = reparto_ie_actual(il_rows, ce_p)
    if "ipf_obj_df" not in ss or list(ss.ipf_obj_df["Instrumento"]) != ies:
        ss.ipf_obj_df = pd.DataFrame(
            {"Instrumento": ies,
             "Objetivo (%)": [round(actual.get(ie, 0.0), 1) for ie in ies]}
        )

    col_obj, col_sug = st.columns([1, 1], gap="large")

    with col_obj:
        st.markdown('<div class="mini-label">Distribución de pesos por instrumento (deben sumar 100 %)</div>', unsafe_allow_html=True)
        # AgGrid y no st.data_editor: en algunos navegadores las tablas nativas
        # de Streamlit (dibujadas en <canvas>) salían en negro.
        # OJO: st_aggrid añade al DataFrame que recibe la columna interna
        # «::auto_unique_id::». Como este se guarda en la sesión, a la rejilla
        # se le da una copia (si no, a la siguiente ejecución la columna
        # aparecía como una más, con 0, 1, 2…).
        _obj_df = ss.ipf_obj_df.drop(columns="::auto_unique_id::", errors="ignore").copy()
        _ogb = GridOptionsBuilder.from_dataframe(_obj_df)
        _ogb.configure_default_column(editable=False, resizable=True, sortable=False, filter=False)
        _ogb.configure_column("Instrumento", flex=1, minWidth=180)
        _ogb.configure_column(
            "Objetivo (%)", editable=True, width=120, type=["numericColumn"],
            valueParser=JsCode(
                "function(p){var n=parseFloat(String(p.newValue).replace(',','.'));"
                "return isNaN(n)?0:Math.min(100,Math.max(0,Math.round(n*10)/10))}"
            ),
            valueFormatter=JsCode("function(p){return p.value==null?'':Number(p.value).toFixed(1)}"),
        )
        _ogb.configure_grid_options(rowHeight=30)
        _og = AgGrid(
            _obj_df, gridOptions=_ogb.build(), update_on=[("cellValueChanged", 300)],
            allow_unsafe_jscode=True, fit_columns_on_grid_load=False, custom_css=AGGRID_GRID_CSS,
            height=56 + 30 * len(ss.ipf_obj_df), theme="balham",
            key="ipf_obj_grid_" + "|".join(ies),
        )
        ed = pd.DataFrame(_og["data"])
        if ed.empty or "Objetivo (%)" not in ed.columns:
            ed = ss.ipf_obj_df
        obj = {
            r["Instrumento"]: 0.0 if pd.isna(r["Objetivo (%)"]) else float(r["Objetivo (%)"] or 0.0)
            for _, r in ed.iterrows()
        }
        suma = sum(obj.values())
        suma_ok = abs(suma - 100) <= 0.5
        st.caption(
            f"Σ = {suma:.1f} %" if suma_ok
            else f"Σ = {suma:.1f} % — deben sumar 100 % para poder cargar."
        )

    obj_ipf = {ie: v for ie, v in obj.items() if v > 0 or ie in presentes}
    res = sugerir_pesos(il_rows, sits, obj_ipf, max_iter=1000)
    pce, pil = res["p_por_ce"], res["pil_por_il"]

    with col_sug:
        st.markdown('<div class="mini-label">Sugerencia</div>', unsafe_allow_html=True)
        _info = {r["IL"]: r for r in il_rows}
        _tab_p, _tab_il = st.tabs([f"P por CE ({len(ce_list)})", f"PIL por IL ({len(pil)})"])
        _tab_p.markdown(
            _tabla_html(["CE", "P sugerido"], [[ce, f"{pce.get(ce, 0):g}"] for ce in ce_list],
                        alto=260),
            unsafe_allow_html=True,
        )
        _tab_il.markdown(
            _tabla_html(
                ["IL", "CE", "PIL sugerido"],
                [[il, _info.get(il, {}).get("CE", ""), f"{v:g}"] for il, v in pil.items()],
                alto=260,
            ),
            unsafe_allow_html=True,
        )

    b1, b2, b3, _ = st.columns([1.1, 1, 1.1, 3.8])
    if b1.button("Cargar P y PIL", type="primary", use_container_width=True,
                 disabled=not suma_ok, key="ipf_all"):
        _ipf_cargar(pce, pil, ce_ced, ce_list)
    if b2.button("Cargar solo P", use_container_width=True,
                 disabled=not suma_ok, key="ipf_p"):
        _ipf_cargar(pce, None, ce_ced, ce_list)
    if b3.button("Cargar solo PIL", use_container_width=True,
                 disabled=not suma_ok, key="ipf_pil"):
        _ipf_cargar(None, pil, ce_ced, ce_list)


def _abrir_dialogo_elementos(campo, titulo, row_idx, pending, items, *, cod_key="cod", desc_key="desc"):
    """Panel flotante para marcar con ticks (verde = marcado) los elementos
    (contenidos o transversales) de un indicador de logro, en vez de
    escribirlos a mano. Al cerrarlo —con el botón o con la X/Esc— se escribe
    en `campo` la lista marcada, separada por «, »."""
    ss = st.session_state
    if not (0 <= row_idx < len(pending)):
        ss.il_pick_dialog = None
        return
    fila = pending[row_idx]
    actuales = {
        t.strip().replace(" ", "")
        for t in str(fila.get(campo) or "").split(",")
        if t.strip()
    }
    _key = lambda cod: f"il_pick_{campo}_{row_idx}_{cod}"

    def _cerrar():
        seleccion = [it[cod_key] for it in items if st.session_state.get(_key(it[cod_key]))]
        nuevos = list(pending)
        nuevos[row_idx] = dict(nuevos[row_idx], **{campo: ", ".join(seleccion)})
        st.session_state.il_rows = il_recompute(nuevos, ss.il_ce_ced, ss.il_ce_list)
        st.session_state.il_nonce = st.session_state.get("il_nonce", 0) + 1
        st.session_state.pop("prog_out", None)
        for it in items:
            st.session_state.pop(_key(it[cod_key]), None)
        ss.il_pick_dialog = None
        ss.il_pick_seen = ""

    @st.dialog(titulo, width="large", on_dismiss=_cerrar)
    def _panel():
        st.markdown(
            f'<div class="mini-label">IL {fila.get("IL") or "(sin agrupar todavía)"} · '
            f'CE {fila.get("CE") or "—"}</div>',
            unsafe_allow_html=True,
        )
        st.caption("Marca lo que trabaja este indicador; se colorea en verde al marcarlo.")
        cols = st.columns(2)
        for i, it in enumerate(items):
            cod, desc = it[cod_key], it.get(desc_key, "")
            with cols[i % 2]:
                with st.container(key=f"il_pick_box_{campo}_{row_idx}_{i}"):
                    st.checkbox(
                        f"{cod} — {desc}" if desc else cod,
                        value=cod.replace(" ", "") in actuales,
                        key=_key(cod),
                    )
        # Botón imperativo (no on_click): dentro de un st.dialog, on_click solo
        # relanza el propio diálogo (como un fragment); hace falta un st.rerun()
        # explícito (con scope="app") para que se cierre de verdad, igual que
        # ya hace _dlg_coherencia.
        if st.button("Cerrar", type="primary", use_container_width=True):
            _cerrar()
            st.rerun(scope="app")

    _panel()


def _aplicar_regeneracion(issues):
    """Aplica en sesión los arreglos automáticos de los desajustes: 1 IL en
    blanco por CE sin indicador, quita los IL de criterios que no existen y los
    códigos (CON/CT/DO) que no están en el currículo, y las actividades
    huérfanas."""
    ss = st.session_state
    from tools.consistencia import (
        add_il_para_ce,
        limpiar_codigos,
        quitar_actividades_huerfanas,
        quitar_il_de_ce,
        repartir_pendientes,
    )

    rows = list(ss.get("il_pending") or ss.il_rows)
    for it in issues:
        if it["clave"] == "ce_sin_il":
            rows = add_il_para_ce(rows, it["datos"], ss.cur.get("ce_do"))
        elif it["clave"] == "il_ce_malo":
            rows = quitar_il_de_ce(rows, it["datos"])
        elif it.get("autofix") == "limpiar_codigos":
            rows = limpiar_codigos(rows, it["datos"])
    ss.il_rows = il_recompute(rows, ss.il_ce_ced, ss.il_ce_list)
    ss.pop("il_pending", None)
    ss.il_nonce = ss.get("il_nonce", 0) + 1
    ss.pa_acts = quitar_actividades_huerfanas(ss.get("pa_acts", []), ss.il_rows)
    if any(it["clave"] in ("act_huerfanas", "reparto_pendiente") for it in issues):
        ss.pa_acts = repartir_pendientes(ss.pa_acts)
    for _k in [k for k in ss.keys() if str(k).startswith("paact_")]:
        ss.pop(_k, None)
    ss.pop("prog_out", None)
    ss.pop("pa_docx", None)


@st.dialog("Revisión de coherencia del proyecto", width="large")
def _dlg_coherencia_panel(issues, contexto="guardar"):
    ss = st.session_state
    _txt = {
        "guardar": "El **currículo** de la materia y la tabla de **situaciones de "
        "aprendizaje** mandan. Hay desajustes:",
        "generar": "El **currículo** de la materia y la tabla de **situaciones de "
        "aprendizaje** mandan. Antes de generar la programación hay desajustes:",
    }[contexto]
    st.write(_txt)
    for it in issues:
        st.warning(f"**{it['titulo']}**\n\n{it['detalle']}")
    _manual = [it for it in issues if not it.get("autofix")]
    if _manual:
        st.error(
            "Alguno no se puede arreglar solo: corrígelo en la página "
            "«Diseño de la programación»."
        )

    _accion = "Aplicar los arreglos"
    if contexto == "guardar":
        _accion += " y guardar"
    elif contexto == "generar":
        _accion += " y generar"

    c1, c2 = st.columns(2)
    if c1.button("Lo reviso yo", use_container_width=True, key="dlg_abort"):
        ss.consist_seen = True
        st.rerun()
    if c2.button(_accion, type="primary", use_container_width=True,
                 disabled=bool(_manual), key="dlg_regen"):
        try:
            _aplicar_regeneracion(issues)
            ss.consist_seen = True
            ss.prog_msg = ""
            if contexto in ("guardar", "generar"):
                ss.prog_out = _guardar_todo()
                if contexto == "generar":
                    ss.pa_docx = _generar_docx()
        except Exception as exc:
            ss.prog_msg = f"Error al regenerar: {exc}"
        st.rerun()


_DLG_ABIERTO = False


def _dlg_coherencia(issues, contexto="guardar"):
    """Abre el aviso de coherencia como mucho una vez por ejecución (Streamlit
    no admite dos st.dialog a la vez) y lo da por visto: cerrarlo con la X
    tampoco lo vuelve a sacar en cada clic."""
    global _DLG_ABIERTO
    if _DLG_ABIERTO:
        return
    _DLG_ABIERTO = True
    st.session_state.consist_seen = True
    _dlg_coherencia_panel(issues, contexto)


# ── Botón global "Guardar proyecto" en la barra de arriba (todas las páginas).
# Un único botón, siempre el mismo, sin paso previo que pulsar: en cuanto hay
# proyecto cargado se calcula solo (en segundo plano, sin botón intermedio) y
# aparece ya listo para guardar/descargar; cada clic en él (el 1º, el 2º o el
# 1000º) hace una descarga/guardado real con el nombre actualizado a ese
# instante. Cualquier edición posterior invalida "prog_out" (se pone a None
# en cada Añadir/Borrar/Actualizar) y se recalcula solo otra vez. Si hay
# desajustes de coherencia se avisa una sola vez por proyecto cargado (reutiliza
# "consist_seen", el mismo aviso que al cargar) y no en cada edición.
with dl_box:
    if _hay_proyecto():
        if not st.session_state.get("prog_out"):
            from tools.consistencia import revisar

            _iss = revisar(*_estado_coherencia())
            if _iss and not st.session_state.get("consist_seen"):
                _dlg_coherencia(_iss, contexto="guardar")
            else:
                try:
                    st.session_state.prog_out = _guardar_todo()
                    st.session_state.prog_msg = ""
                except Exception as exc:
                    st.session_state.prog_msg = f"Error al generar el proyecto: {exc}"
                    st.session_state.pop("prog_out", None)
        if st.session_state.get("prog_msg"):
            st.caption(f"⚠️ {st.session_state.prog_msg}")
        if st.session_state.get("prog_out"):
            _base = _nombre_sin_sello(st.session_state.proy_nombre)
            _guardar_archivo_html(st.session_state.prog_out, _base)

# PÁGINA: DISEÑO DE LA PROGRAMACIÓN
if page == "Diseño de la programación":
    st.caption(
        "Diseña la programación sobre el currículo de la materia. Abre, crea y guarda "
        "el proyecto en la barra de arriba."
    )

    COLS = SA_COLS

    if not _hay_proyecto():
        st.info("Abre un proyecto o crea uno nuevo en la barra de arriba para empezar.")
    else:
        from tools.situaciones_aprendizaje import Situacion, acumulado_por_trimestre
        from tools.situaciones_informe import (
            AGGRID_GRID_CSS,
            AGGRID_LINES_CSS,
            build_image_copy_html,
            build_pie_png,
            build_table_copy_html,
            hsa_share,
            zebra_styler,
        )

        (
            _tab_sa, _tab_ses, _tab_ce, _tab_il, _tab_aj, _tab_dist, _tab_pf,
        ) = _pestanas("tabs_diseno", [
            "Situaciones de aprendizaje",
            "Sesiones por evaluación",
            "Criterios de evaluación",
            "Indicadores de logro",
            "Ajuste de pesos",
            "Distribución CE × SA",
            "Peso final por instrumento",
        ])

        # ───────────────── PESTAÑA: SITUACIONES DE APRENDIZAJE ─────────────────
        with _tab_sa:
            from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

            st.session_state.setdefault("sa_nonce", 0)

            def _sa_recompute(rows):
                clean = [
                    r for r in rows
                    if r.get("SA") not in (None, "")
                    or str(r.get("DSA") or "").strip()
                    or r.get("HSA") not in (None, "")
                ]

                def _n(v):
                    if v in (None, "") or (isinstance(v, float) and pd.isna(v)):
                        return None
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return None

                total = sum(h for h in (_n(r.get("HSA")) for r in clean) if h)
                out = []
                for r in clean:
                    h = _n(r.get("HSA"))
                    ev = _n(r.get("EV"))
                    sa = _n(r.get("SA"))
                    out.append(
                        {
                            "SA": None if sa is None else int(sa),
                            "EV": None if ev is None else int(ev),
                            "DSA": "" if r.get("DSA") is None or (isinstance(r.get("DSA"), float) and pd.isna(r.get("DSA"))) else str(r.get("DSA")),
                            "HSA": None if h is None else (int(h) if h.is_integer() else h),
                            "PCT": (100 * h / total) if (h and total) else 0.0,
                        }
                    )
                return out

            def _sa_sig(rows):
                return [(r["SA"], r["EV"], r["DSA"], r["HSA"]) for r in rows]

            if "sa_grid_rows" not in st.session_state:
                _init = [
                    {"SA": v[0], "EV": v[1], "DSA": v[2], "HSA": v[3]}
                    for v in st.session_state.sa_df.itertuples(index=False)
                ]
                st.session_state.sa_grid_rows = _sa_recompute(_init)

            calc_box = st.container()
            st.divider()

            st.markdown(
                '<div class="mini-label">SA · EV (trimestre) · Descripción · Horas · '
                "<b>% horas</b> (se recalcula al pulsar Actualizar) · marca la casilla y "
                "pulsa Borrar</div>",
                unsafe_allow_html=True,
            )
            sc1, sc2, sc3, _sc = st.columns([0.9, 1.15, 0.85, 4.1])
            sa_add_click = sc1.button("Añadir fila", use_container_width=True, key="sa_add")
            sa_del_click = sc2.button("Borrar marcadas", use_container_width=True, key="sa_del")
            sa_upd_click = sc3.button("Actualizar", use_container_width=True, type="primary", key="sa_upd")

            col_edit, col_pie = st.columns([3.2, 2], gap="medium")

            with col_edit:
                _sa_df = pd.DataFrame(
                    [
                        {
                            "X": False,
                            "SA": r["SA"],
                            "EV": "" if r["EV"] in (None, "") else str(int(r["EV"])),
                            "DSA": "" if r["DSA"] is None else str(r["DSA"]),
                            "HSA": r["HSA"],
                            "% horas": r["PCT"],
                        }
                        for r in st.session_state.sa_grid_rows
                    ],
                    columns=["X", "SA", "EV", "DSA", "HSA", "% horas"],
                )
                _sa_df["X"] = _sa_df["X"].astype(bool)
                _sa_df["EV"] = _sa_df["EV"].astype(str)
                _sa_df["DSA"] = _sa_df["DSA"].astype(str)
                _gb = GridOptionsBuilder.from_dataframe(_sa_df)
                _gb.configure_default_column(editable=True, resizable=True, sortable=False, filter=False)
                _gb.configure_column("X", headerName="", editable=True, width=44, pinned="left",
                                     cellRenderer="agCheckboxCellRenderer",
                                     cellEditor="agCheckboxCellEditor", cellDataType="boolean")
                _gb.configure_column("SA", headerName="SA (nº)", width=82, cellDataType="number",
                                     type=["numericColumn"])
                _gb.configure_column("EV", headerName="EV (trim.)", width=96, cellDataType="text",
                                     cellEditor="agSelectCellEditor",
                                     cellEditorParams={"values": [""] + [str(t) for t in TRIMESTRES]})
                _gb.configure_column("DSA", headerName="Descripción", flex=1, minWidth=220,
                                     cellDataType="text", tooltipField="DSA")
                _gb.configure_column("HSA", headerName="Horas", width=82, cellDataType="number",
                                     type=["numericColumn"])
                _gb.configure_column(
                    "% horas", editable=False, width=94, cellDataType="number",
                    valueFormatter=JsCode(
                        "function(p){return p.value==null?'':Number(p.value).toFixed(1)+' %'}"
                    ),
                )
                _gb.configure_grid_options(enableBrowserTooltips=True, tooltipShowDelay=300, rowHeight=30)
                _sa_grid = AgGrid(
                    _sa_df, gridOptions=_gb.build(),
                    update_on=[("cellValueChanged", 300)],
                    allow_unsafe_jscode=True, fit_columns_on_grid_load=False,
                    custom_css=AGGRID_GRID_CSS,
                    height=min(430, 42 + 30 * len(_sa_df)),
                    theme="balham", key=f"sa_grid_{st.session_state.sa_nonce}",
                )

            _sg = pd.DataFrame(_sa_grid["data"])
            if _sg.empty or "SA" not in _sg.columns:
                _sg = _sa_df.copy()

            def _truthy(v):
                return str(v).strip().lower() in ("true", "1", "yes", "x")

            sa_pending = [
                {"SA": r.get("SA"), "EV": r.get("EV"), "DSA": r.get("DSA"), "HSA": r.get("HSA")}
                for _, r in _sg.iterrows()
            ]
            sa_del_flags = [_truthy(r.get("X")) for _, r in _sg.iterrows()]

            if sa_add_click:
                _rows = _sa_recompute(sa_pending)
                _exist = [r["SA"] for r in _rows if r["SA"] is not None]
                _rows.append(
                    {
                        "SA": (max(_exist) + 1) if _exist else 1,
                        "EV": None, "DSA": "", "HSA": None, "PCT": 0.0,
                    }
                )
                st.session_state.sa_grid_rows = _rows
                st.session_state.sa_nonce += 1
                st.session_state.pop("prog_out", None)
                st.rerun()
            if sa_del_click and any(sa_del_flags):
                st.session_state.sa_grid_rows = _sa_recompute(
                    [p for p, d in zip(sa_pending, sa_del_flags) if not d]
                )
                st.session_state.sa_nonce += 1
                st.session_state.pop("prog_out", None)
                st.rerun()
            if sa_upd_click:
                st.session_state.sa_grid_rows = _sa_recompute(sa_pending)
                st.session_state.sa_nonce += 1
                st.session_state.pop("prog_out", None)
                st.rerun()

            _sa_live = _sa_recompute(sa_pending)
            if _sa_sig(_sa_live) != _sa_sig(st.session_state.sa_grid_rows):
                st.info("Hay cambios en las situaciones. Pulsa **Actualizar** para recalcular el % de horas.")

            sits = [
                Situacion(sa=r["SA"], ev=r["EV"], dsa=r["DSA"], hsa=r["HSA"])
                for r in _sa_live
            ]
            shares = hsa_share(sits)
            pie_png = build_pie_png(shares)
            total_h = sum(float(s.hsa) for s in sits if s.hsa)

            with col_edit:
                components.html(build_table_copy_html(shares), height=38)

            with col_pie:
                st.markdown('<div class="mini-label">Reparto de horas</div>', unsafe_allow_html=True)
                if shares:
                    st.image(pie_png, use_container_width=True)
                    bcol1, bcol2 = st.columns(2)
                    with bcol1:
                        components.html(build_image_copy_html(pie_png), height=38)
                    with bcol2:
                        st.download_button(
                            "Descargar PNG", data=pie_png,
                            file_name="reparto_horas_SA.png", mime="image/png",
                            use_container_width=True,
                        )
                else:
                    st.caption("Añade situaciones con horas para ver el gráfico.")

            # Validaciones
            errores = []
            for i, r in enumerate(_sa_live, start=1):
                if r["SA"] is None:
                    errores.append(f"Fila {i}: falta el nº de situación (SA).")
                if not r["DSA"].strip():
                    errores.append(f"Fila {i}: falta la descripción (DSA).")
                if r["HSA"] is None or float(r["HSA"]) < 0:
                    errores.append(f"Fila {i}: las horas (HSA) deben ser un número ≥ 0.")
                if r["EV"] not in TRIMESTRES:
                    errores.append(f"Fila {i}: la evaluación (EV) debe ser 1, 2 o 3.")
            _sn = [r["SA"] for r in _sa_live if r["SA"] is not None]
            _dup = sorted({n for n in _sn if _sn.count(n) > 1})
            if _dup:
                errores.append(f"Hay números de situación repetidos: {_dup}.")

            # Calculadora de horas por trimestre (compacta, arriba del bloque).
            acumulado = acumulado_por_trimestre(sits)
            previstas = {}
            with calc_box:
                st.markdown(
                    '<div class="mini-label">Horas por trimestre — previstas (editables) · '
                    "planificadas (Σ HSA) · desviación</div>",
                    unsafe_allow_html=True,
                )
                cc = st.columns([1, 1, 1, 1.3])
                for col, tri in zip(cc[:3], TRIMESTRES):
                    with col:
                        previstas[tri] = st.number_input(
                            f"{tri}º trim. previstas",
                            min_value=0.0,
                            step=1.0,
                            value=float(st.session_state.sa_previstas.get(tri, 0.0)),
                            key=f"sa_prev_{tri}",
                        )
                        acc = acumulado.get(tri, 0.0)
                        desv = previstas[tri] - acc
                        color = "#c62828" if desv < 0 else "#2e7d32"
                        st.markdown(
                            f"<div style='font-size:13px;margin-top:-8px'>plan. <b>{acc:g} h</b> · "
                            f"<span style='color:{color}'>desv. {desv:+g} h</span></div>",
                            unsafe_allow_html=True,
                        )
                total_prev = sum(previstas.values())
                total_acc = sum(acumulado.values())
                tcolor = "#c62828" if total_prev - total_acc < 0 else "#2e7d32"
                with cc[3]:
                    st.markdown(
                        f"<div style='font-size:13px;margin-top:6px'><b>Curso</b><br>"
                        f"{total_acc:g} / {total_prev:g} h "
                        f"<span style='color:{tcolor}'>({total_prev - total_acc:+g} h)</span></div>",
                        unsafe_allow_html=True,
                    )

            if errores:
                st.warning("Situaciones — avisos:\n\n- " + "\n- ".join(errores))

        # ───────────────── PESTAÑA: CALCULADORA DE SESIONES ─────────────────
        with _tab_ses:
            _calc_sesiones_por_evaluacion()

        ce_list = st.session_state.il_ce_list
        ce_ced = st.session_state.il_ce_ced
        aux = st.session_state.il_aux
        sa_options = sorted({s.sa for s in sits if s.sa})

        # ───────────────── PESTAÑA: CRITERIOS DE EVALUACIÓN ─────────────────
        with _tab_ce:
            from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

            st.session_state.setdefault("ce_nonce", 0)
            _ce_p0 = st.session_state.get("il_ce_p", {})

            def _ce_recompute(pairs):
                total = sum(p for _, p in pairs if p)
                return [
                    {
                        "CE": ce, "CED": ce_ced.get(ce, ""),
                        "P": p, "PCT": (p / total if (p and total) else 0.0),
                    }
                    for ce, p in pairs
                ]

            if "ce_rows" not in st.session_state:
                st.session_state.ce_rows = _ce_recompute(
                    [(ce, float(_ce_p0.get(ce, 0.0))) for ce in ce_list]
                )

            st.markdown(
                '<div class="mini-label">Solo se puede modificar el <b>peso P</b> '
                "(hasta 2 decimales) · no se añaden ni quitan criterios · %CE se "
                "recalcula al pulsar Actualizar</div>",
                unsafe_allow_html=True,
            )
            _cc1, _ = st.columns([1.2, 5])
            ce_upd_click = _cc1.button("Actualizar", use_container_width=True, type="primary", key="ce_upd")

            ce_grid_col, ce_side_col = st.columns([3.4, 1.6], gap="medium")
            with ce_grid_col:
                _ce_df = pd.DataFrame(
                    [
                        {"CE": r["CE"], "CED": r["CED"], "P": r["P"], "%CE": r["PCT"] * 100}
                        for r in st.session_state.ce_rows
                    ],
                    columns=["CE", "CED", "P", "%CE"],
                )
                _cgb = GridOptionsBuilder.from_dataframe(_ce_df)
                _cgb.configure_default_column(editable=False, resizable=True, sortable=False, filter=False)
                _cgb.configure_column("CE", width=70, pinned="left")
                _cgb.configure_column("CED", width=230, cellDataType="text", tooltipField="CED")
                _cgb.configure_column(
                    "P", editable=True, width=90, cellDataType="number", type=["numericColumn"],
                    valueParser=JsCode(
                        "function(p){var n=parseFloat(String(p.newValue).replace(',','.'));"
                        "return isNaN(n)?0:Math.round(n*100)/100}"
                    ),
                    valueFormatter=JsCode(
                        "function(p){return p.value==null?'':Number(p.value).toFixed(2)}"
                    ),
                )
                _cgb.configure_column(
                    "%CE", width=88,
                    valueFormatter=JsCode(
                        "function(p){return p.value==null?'':Number(p.value).toFixed(2)+' %'}"
                    ),
                )
                _cgb.configure_grid_options(enableBrowserTooltips=True, tooltipShowDelay=300, rowHeight=28)
                _ce_grid = AgGrid(
                    _ce_df, gridOptions=_cgb.build(),
                    update_on=[("cellValueChanged", 300)],
                    allow_unsafe_jscode=True, fit_columns_on_grid_load=False,
                    custom_css=AGGRID_GRID_CSS,
                    height=min(460, 42 + 28 * len(_ce_df)),
                    theme="balham", key=f"ce_grid_{st.session_state.ce_nonce}",
                )

            _cg = pd.DataFrame(_ce_grid["data"])
            if _cg.empty or "CE" not in _cg.columns:
                _cg = _ce_df.copy()
            ce_pending = [
                (
                    str(r["CE"]),
                    0.0 if r["P"] in (None, "") or pd.isna(r["P"]) else round(float(r["P"]), 2),
                )
                for _, r in _cg.iterrows()
            ]
            _sum_p_live = sum(p for _, p in ce_pending if p)
            _sum_p_canon = sum(r["P"] for r in st.session_state.ce_rows if r["P"])

            with ce_side_col:
                st.metric("Σ pesos (P)", f"{_sum_p_live:g}")
                if abs(_sum_p_live - _sum_p_canon) > 1e-9:
                    st.caption("Pulsa **Actualizar** para refrescar la columna %CE de esta tabla.")

            if ce_upd_click:
                st.session_state.ce_rows = _ce_recompute(ce_pending)
                st.session_state.ce_nonce += 1
                st.session_state.pop("prog_out", None)
                st.rerun()

        # Pesos vigentes (en vivo desde la rejilla) para todos los cálculos.
        ce_p = dict(ce_pending)

        # ───────────────── SECCIÓN: INDICADORES DE LOGRO ─────────────────
        def _with_existing(options, key):
            # Los SelectboxColumn de Streamlit fallan si una celda tiene un valor
            # que no está en las opciones; añadimos los valores ya presentes al
            # final para que la tabla no reviente (las validaciones ya avisan).
            extra = [
                r[key]
                for r in st.session_state.il_rows
                if r[key] not in (None, "") and r[key] not in options
            ]
            return list(options) + list(dict.fromkeys(extra))

        ce_col_opts = _with_existing(ce_list, "CE")
        sa_col_opts = _with_existing(sa_options, "SA")

        def _il_sig(rows):
            return [
                (
                    r["CE"], r["IL"],
                    (None if r["PIL"] in (None, "") else float(r["PIL"])),
                    r["DIL"], r["DO"], r["CON"], r["CT"], r["IE"], r["CC"], r["AE"],
                    (None if r["SA"] in (None, "") else int(r["SA"])),
                    tuple(sorted((r.get("CAT") or {}).items())),
                )
                for r in rows
            ]

        from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

        st.session_state.setdefault("il_nonce", 0)

        def _parse_grid_row(r):
            _cat = {}
            for _c in st.session_state.get("il_categorias", []):
                _v = r.get(categorias_def.columna(_c["id"]))
                _oid = None if _v is None or pd.isna(_v) else categorias_def.id_de_opcion(_c, _v)
                if _oid is not None:
                    _cat[_c["id"]] = _oid
            return {
                "CAT": _cat,
                "CE": "" if pd.isna(r.get("CE")) else str(r.get("CE")).strip(),
                "CED": "", "IL": "",
                "PIL": None if r.get("PIL") in (None, "") or pd.isna(r.get("PIL")) else float(r.get("PIL")),
                "DIL": "" if pd.isna(r.get("DIL")) else str(r.get("DIL")),
                "DO": "" if pd.isna(r.get("DO")) else str(r.get("DO")),
                "CON": "" if pd.isna(r.get("CON")) else str(r.get("CON")),
                "CT": "" if pd.isna(r.get("CT")) else str(r.get("CT")),
                "IE": "" if pd.isna(r.get("IE")) else str(r.get("IE")),
                "CC": "" if pd.isna(r.get("CC")) else str(r.get("CC")),
                "AE": "" if pd.isna(r.get("AE")) else str(r.get("AE")),
                "SA": None if r.get("SA") in (None, "") or pd.isna(r.get("SA")) else int(float(r.get("SA"))),
            }

        with _tab_il:
            st.markdown(
                '<div class="mini-label">CE se elige de la lista · CED e IL (4.2.1, 4.2.2…) '
                "son automáticos · PIL a mano, PIL% automático · SA solo entre las de arriba · "
                "pulsa una celda de DO, CON o CT para marcarlos con ticks (al añadir un "
                "indicador, DO trae los descriptores del criterio) · pasa el ratón por CED/DIL para ver el texto completo · marca la casilla de la "
                "izquierda y pulsa <b>Borrar</b> · escribe y pulsa <b>Actualizar</b> para agrupar "
                "por criterio y renumerar (nada se pierde hasta entonces)</div>",
                unsafe_allow_html=True,
            )

            # Filtro por SA: es un filtro de la rejilla (las filas ocultas siguen
            # en ella y se devuelven todas, ver data_return_mode). Al cambiarlo
            # se consolida lo tecleado, porque la rejilla se remonta.
            def _il_filtro_cambia():
                ss = st.session_state
                if ss.get("il_pending") is not None:
                    ss.il_rows = il_recompute(ss.il_pending, ce_ced, ce_list)
                ss.pop("prog_out", None)

            _filtro_opts = ["Todas"] + [str(x) for x in sa_options] + ["Sin SA"]
            if st.session_state.get("il_filtro_sa") not in _filtro_opts:
                st.session_state.il_filtro_sa = "Todas"
            filtro_sa = st.columns([1, 3])[0].selectbox(
                "Filtrar por SA", _filtro_opts, key="il_filtro_sa",
                format_func=lambda v: v if v in ("Todas", "Sin SA") else f"SA {v}",
                on_change=_il_filtro_cambia,
            )
            # valor de la columna SA (texto) que pasa el filtro; None = todas
            _filtro_val = {"Todas": None, "Sin SA": ""}.get(filtro_sa, filtro_sa)

            ui_categorias.pintar(lambda filas: il_recompute(filas, ce_ced, ce_list))
            _cats = st.session_state.get("il_categorias", [])

            ac1, ac2, ac3, ac4, ac5, _ = st.columns([1.7, 0.8, 1.15, 1.15, 0.9, 1.6])
            add_ce = ac1.selectbox("Criterio", ce_list, key="il_add_ce", label_visibility="collapsed")
            add_n = ac2.number_input("nº", 1, 20, 1, key="il_add_n", label_visibility="collapsed")
            add_click = ac3.button("Añadir al criterio", use_container_width=True)
            del_click = ac4.button("Borrar marcadas", use_container_width=True)
            upd_click = ac5.button("Actualizar", use_container_width=True, type="primary")

            il_df = pd.DataFrame(
                [
                    {
                        "X": False,
                        "CE": r["CE"], "CED": r["CED"], "IL": r["IL"],
                        "PIL": r["PIL"], "PIL%": r["PIL%"] * 100,
                        "DIL": r["DIL"], "DO": r["DO"], "CON": r["CON"], "CT": r["CT"],
                        "IE": r["IE"], "CC": r["CC"], "AE": r["AE"],
                        "SA": "" if r["SA"] in (None, "") else str(r["SA"]),
                        **{
                            categorias_def.columna(c["id"]): categorias_def.nombre_de_opcion(
                                c, (r.get("CAT") or {}).get(c["id"])
                            )
                            for c in _cats
                        },
                        "__shade": False,  # se calcula justo debajo
                        "_pick": "",  # aviso de clic en CON (ver onCellClicked)
                    }
                    for r in st.session_state.il_rows
                ],
                columns=["X", "CE", "CED", "IL", "PIL", "PIL%", "DIL", "DO",
                         "CON", "CT", "IE", "CC", "AE", "SA",
                         *[categorias_def.columna(c["id"]) for c in _cats],
                         "__shade", "_pick"],
            )
            # sombreado alterno por CE contando solo las filas que se ven
            _ce_seq = list(dict.fromkeys(
                ce for ce, sa in zip(il_df["CE"], il_df["SA"])
                if _filtro_val is None or sa == _filtro_val
            ))
            _ce_shade = {ce: (i % 2 == 1) for i, ce in enumerate(_ce_seq)}
            il_df["__shade"] = il_df["CE"].map(lambda c: bool(_ce_shade.get(c)))
            il_df["X"] = il_df["X"].astype(bool)

            gb = GridOptionsBuilder.from_dataframe(il_df)
            gb.configure_default_column(editable=True, resizable=True, sortable=False, filter=False)
            gb.configure_column("__shade", hide=True)
            gb.configure_column("_pick", hide=True)
            gb.configure_column(
                "X", headerName="", editable=True, width=44, pinned="left",
                cellRenderer="agCheckboxCellRenderer", cellEditor="agCheckboxCellEditor",
                cellDataType="boolean", headerTooltip="Marca y pulsa «Borrar»",
            )
            gb.configure_column("CE", width=78, pinned="left", cellEditor="agSelectCellEditor",
                                cellEditorParams={"values": ce_col_opts})
            gb.configure_column("CED", editable=False, width=130, tooltipField="CED")
            gb.configure_column("IL", editable=False, width=78)
            gb.configure_column(
                "PIL", width=70, type=["numericColumn"],
                valueFormatter=JsCode(
                    "function(p){return p.value===''||p.value==null?'':Number(p.value).toFixed(2)}"
                ),
            )
            gb.configure_column(
                "PIL%", editable=False, width=82,
                valueFormatter=JsCode(
                    "function(p){return p.value==null?'':Number(p.value).toFixed(2)+' %'}"
                ),
            )
            gb.configure_column("DIL", width=240, tooltipField="DIL")
            _pick_cell_style = JsCode(
                "function(p){return {cursor:'pointer', textDecoration:'underline'}}"
            )
            _pick_on_click = JsCode(
                "function(p){ p.node.setDataValue("
                "'_pick', p.colDef.field + '|' + String(p.rowIndex) + '|' + Date.now()); }"
            )
            gb.configure_column(
                "DO", width=180, editable=False, tooltipField="DO",
                headerTooltip="Pulsa una celda para marcar los descriptores operativos con ticks",
                cellStyle=_pick_cell_style, onCellClicked=_pick_on_click,
            )
            gb.configure_column(
                "CON", width=130, editable=False, tooltipField="CON",
                headerTooltip="Pulsa una celda para marcar los contenidos con ticks",
                cellStyle=_pick_cell_style, onCellClicked=_pick_on_click,
            )
            gb.configure_column(
                "CT", width=80, editable=False, tooltipField="CT",
                headerTooltip="Pulsa una celda para marcar los elementos transversales con ticks",
                cellStyle=_pick_cell_style, onCellClicked=_pick_on_click,
            )
            gb.configure_column("IE", width=140, cellEditor="agSelectCellEditor",
                                cellEditorParams={"values": _with_existing(aux.get("IE", []), "IE")})
            gb.configure_column("CC", width=130, cellEditor="agSelectCellEditor",
                                cellEditorParams={"values": _with_existing(aux.get("CC", []), "CC")})
            gb.configure_column("AE", width=70, cellEditor="agSelectCellEditor",
                                cellEditorParams={"values": _with_existing(aux.get("AE", []), "AE")})
            gb.configure_column("SA", width=62, cellEditor="agSelectCellEditor",
                                cellEditorParams={"values": [str(x) for x in sa_col_opts]})
            for _c in _cats:
                gb.configure_column(
                    categorias_def.columna(_c["id"]), headerName=_c["nombre"] or "(sin nombre)",
                    width=130, cellEditor="agSelectCellEditor",
                    cellEditorParams={"values": [""] + [o["nombre"] for o in _c["opciones"] if o["nombre"]]},
                )
            gb.configure_grid_options(
                enableBrowserTooltips=True,
                tooltipShowDelay=300,
                getRowStyle=JsCode(
                    "function(p){return (p.data && p.data.__shade) "
                    "? {'background-color':'#E3EEF9'} : null}"
                ),
                rowHeight=30,
            )
            if _filtro_val is not None:
                gb.configure_grid_options(
                    isExternalFilterPresent=JsCode("function(){return true}"),
                    doesExternalFilterPass=JsCode(
                        "function(n){return n.data && String(n.data.SA ?? '') === "
                        + repr(_filtro_val) + "}"
                    ),
                )

            grid = AgGrid(
                il_df,
                gridOptions=gb.build(),
                # todas las filas, también las ocultas por el filtro de SA, y en
                # su orden: «pending» y los índices de fila cuentan con ello.
                data_return_mode="AS_INPUT",
                update_on=[("cellValueChanged", 300)],
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=False,
                custom_css=AGGRID_LINES_CSS,
                height=430,
                theme="balham",
                key=f"il_grid_{st.session_state.il_nonce}_{filtro_sa}",
            )

            # Lo que hay ahora mismo en la rejilla (en su orden actual, sin agrupar).
            grid_df = pd.DataFrame(grid["data"])
            if grid_df.empty or "CE" not in grid_df.columns:
                grid_df = il_df.copy()
            pending = [_parse_grid_row(r) for _, r in grid_df.iterrows()]
            # para consumidores externos (Elementos, Programación de aula) se guarda
            # ya recalculado: con IL/CED/PIL% rellenos.
            st.session_state.il_pending = il_recompute(pending, ce_ced, ce_list)

            # Clic en la celda CON o CT: abre el panel flotante de esa lista para
            # esa fila (marca «_pick» vía onCellClicked, se detecta aquí como
            # cualquier otra edición de la rejilla).
            if "_pick" in grid_df.columns:
                for _pi, _mark in enumerate(grid_df["_pick"].tolist()):
                    _mark = "" if pd.isna(_mark) else str(_mark)
                    if _mark and _mark != st.session_state.get("il_pick_seen"):
                        st.session_state.il_pick_seen = _mark
                        _campo_click = _mark.split("|", 1)[0]
                        if _campo_click not in ("CON", "CT", "DO"):
                            _campo_click = "CON"
                        st.session_state.il_pick_dialog = {"campo": _campo_click, "row_idx": _pi}
                        break

            _PICK_CONFIG = {
                "CON": ("contenidos", "cod", "Contenidos de la materia (CON)"),
                "CT": ("transversales", "num", "Elementos transversales (CT)"),
                "DO": ("descriptores", "cod", "Descriptores operativos (DO)"),
            }
            if st.session_state.get("il_pick_dialog"):
                _pd_info = st.session_state.il_pick_dialog
                _el_key, _cod_key, _pd_titulo = _PICK_CONFIG.get(
                    _pd_info["campo"], _PICK_CONFIG["CON"]
                )
                _pd_items = st.session_state.get("elementos", {}).get(_el_key, [])
                if _pd_info["campo"] == "DO" and 0 <= _pd_info["row_idx"] < len(pending):
                    # Solo los descriptores del criterio de esa fila (los que
                    # el currículo vincula a ese CE), más los ya marcados.
                    _fila_do = pending[_pd_info["row_idx"]]
                    _rel = set(st.session_state.cur["ce_do"].get(_fila_do["CE"], []))
                    _rel |= {t.strip() for t in str(_fila_do.get("DO") or "").split(",") if t.strip()}
                    if _rel:
                        _pd_items = [it for it in _pd_items if it["cod"] in _rel]
                _abrir_dialogo_elementos(
                    _pd_info["campo"], _pd_titulo, _pd_info["row_idx"], pending, _pd_items,
                    cod_key=_cod_key,
                )

            def _truthy(v):
                return str(v).strip().lower() in ("true", "1", "yes", "x")

            del_flags = [_truthy(r.get("X")) for _, r in grid_df.iterrows()]

            # Botones (reruns "de golpe", no molestos): reconstruyen la tabla ya
            # agrupada y renumerada, y remontan la rejilla (cambia il_nonce).
            if add_click:
                base = list(pending)
                for _ in range(int(add_n)):
                    base.append(
                        {
                            "CE": add_ce, "CED": "", "IL": "", "PIL": 1, "DIL": "",
                            "DO": ", ".join(st.session_state.cur["ce_do"].get(add_ce, [])),
                            "CON": "", "CT": "",
                            "IE": "", "CC": "", "AE": "",
                            # con el filtro puesto, nace en esa SA (si no, no se vería)
                            "SA": int(_filtro_val) if _filtro_val else None,
                        }
                    )
                st.session_state.il_rows = il_recompute(base, ce_ced, ce_list)
                st.session_state.il_nonce += 1
                st.session_state.pop("prog_out", None)
                st.rerun()

            if del_click and any(del_flags):
                kept = [p for p, d in zip(pending, del_flags) if not d]
                st.session_state.il_rows = il_recompute(kept, ce_ced, ce_list)
                st.session_state.il_nonce += 1
                st.session_state.pop("prog_out", None)
                st.rerun()

            if upd_click:
                st.session_state.il_rows = il_recompute(pending, ce_ced, ce_list)
                st.session_state.il_nonce += 1
                st.session_state.pop("prog_out", None)
                st.rerun()

            # ¿Hay ediciones sin agrupar/renumerar?
            if _il_sig(il_recompute(pending, ce_ced, ce_list)) != _il_sig(st.session_state.il_rows):
                st.info("Hay cambios en la tabla. Pulsa **Actualizar** para agrupar por criterio y renumerar los IL.")

            il_errores = []
            for i, r in enumerate(pending, start=1):
                if not r["CE"]:
                    il_errores.append(f"Fila {i}: falta el criterio (CE).")
                elif r["CE"] not in ce_ced:
                    il_errores.append(f"Fila {i}: el criterio {r['CE']} no existe en el currículo de la materia.")
                if r["SA"] not in (None, "") and int(r["SA"]) not in sa_options:
                    il_errores.append(
                        f"Fila {i}: la SA {r['SA']} no está en la tabla de situaciones de aprendizaje."
                    )
            if il_errores:
                st.warning("Indicadores — avisos:\n\n- " + "\n- ".join(il_errores))

            # Resumen por criterio (como la hoja RESUMEN) + copiar para Word.
            from tools.indicadores_logro import resumen_por_ce
            from tools.situaciones_informe import (
                build_html_table_copy_html,
                render_word_table_html,
            )

            _res = resumen_por_ce(
                il_recompute(pending, ce_ced, ce_list), ce_list, ce_ced, ce_p
            )
            _res_headers = ["CE", "%CE", "CONTENIDOS", "CT", "SA"]
            _res_rows = [
                [
                    r["CE"],
                    f"{r['pct'] * 100:.2f}".replace(".", ",") + " %",
                    r["CONTENIDOS"], r["CT"], r["SA"],
                ]
                for r in _res
            ]
            _res_table = render_word_table_html(_res_headers, _res_rows)
            st.markdown('<div class="mini-label">Resumen por criterio</div>', unsafe_allow_html=True)
            components.html(
                build_html_table_copy_html(
                    _res_table, btn_id="il-copy-res", fn="ilCopyRes",
                    label="Copiar resumen (Word)",
                ),
                height=40,
            )
            if st.toggle("Ver resumen por criterio", key="il_ver_resumen"):
                st.dataframe(
                    zebra_styler(pd.DataFrame(_res_rows, columns=_res_headers)),
                    use_container_width=True,
                    hide_index=True,
                )

        # ─── PESTAÑA: AJUSTE DE PESOS ───
        with _tab_aj:
            st.caption("Objetivo por instrumento de evaluación + reparto horario de las situaciones.")
            _ajuste_pesos_ipf(
                il_recompute(pending, ce_ced, ce_list), ce_list, ce_ced, ce_p, sits
            )

        # ─────── PESTAÑA: DISTRIBUCIÓN DE PORCENTAJES POR CE Y SA ───────
        with _tab_dist:
            st.caption("Distribución de porcentajes por criterios de evaluación y situaciones de aprendizaje.")
            from st_aggrid import AgGrid, GridOptionsBuilder
            from tools.indicadores_logro import matriz_sa_ce
            from tools.situaciones_informe import (
                _fmt_pct2,
                build_html_table_copy_html,
                build_sa_compare_png,
                render_word_table_html,
            )

            _il_now = il_recompute(pending, ce_ced, ce_list)
            _m = matriz_sa_ce(_il_now, ce_list, ce_p)
            sa_rows_m = _m["sa_rows"]
            ce_cols_m = _m["ce_cols"]

            _total_h = sum(float(s.hsa) for s in sits if s.hsa)
            _dsa = {int(s.sa): s.dsa for s in sits if s.sa}
            _pct_h = {
                int(s.sa): (float(s.hsa) / _total_h if (s.hsa and _total_h) else 0.0)
                for s in sits if s.sa
            }

            st.markdown(
                '<div class="mini-label">Peso de cada SA sobre el total de la programación, '
                "por criterio (según los IL asignados) · «Total (IL)» = suma de la fila · "
                "«% SA (horas)» = reparto de horas de la tabla de arriba, para comparar</div>",
                unsafe_allow_html=True,
            )

            _headers = ["SA"] + ce_cols_m + ["Total (IL)", "% SA (horas)"]
            _body = []
            for sa in sa_rows_m:
                r = [str(sa)]
                for c in ce_cols_m:
                    v = _m["matrix"].get((sa, c), 0.0)
                    r.append(_fmt_pct2(v) if v else "")
                r.append(_fmt_pct2(_m["sa_total"].get(sa, 0.0)))
                r.append(_fmt_pct2(_pct_h.get(sa, 0.0)))
                _body.append(r)
            _tot = ["Total general"]
            _tot += [_fmt_pct2(_m["ce_total"].get(c, 0.0)) for c in ce_cols_m]
            _tot.append(_fmt_pct2(_m["grand_total"]))
            _tot.append(_fmt_pct2(sum(_pct_h.values())))
            _body.append(_tot)

            _labels = [f"{sa}: {_dsa.get(sa, '')}" for sa in sa_rows_m]
            _cmp_png = build_sa_compare_png(
                sa_rows_m, _labels,
                [_m["sa_total"].get(sa, 0.0) for sa in sa_rows_m],
                [_pct_h.get(sa, 0.0) for sa in sa_rows_m],
            )

            mx_tab, mx_gra = st.columns([4, 1.25], gap="medium")

            with mx_tab:
                _mx_df = pd.DataFrame(_body, columns=_headers)
                _mx_df.insert(1, "Título", [_dsa.get(sa, "") for sa in sa_rows_m] + [""])
                _gb = GridOptionsBuilder.from_dataframe(_mx_df)
                _gb.configure_default_column(
                    editable=False, resizable=True, sortable=False, filter=False,
                    width=84, minWidth=84, cellStyle={"textAlign": "center"},
                )
                _gb.configure_column("Título", hide=True)
                _gb.configure_column("SA", pinned="left", width=56, tooltipField="Título",
                                     cellStyle={"fontWeight": "600", "textAlign": "center"})
                _gb.configure_column("Total (IL)", pinned="right", width=116,
                                     cellStyle={"fontWeight": "600", "textAlign": "center"})
                _gb.configure_column("% SA (horas)", pinned="right", width=136,
                                     cellStyle={"fontWeight": "600", "textAlign": "center"})
                _gb.configure_grid_options(
                    enableBrowserTooltips=True, tooltipShowDelay=300, rowHeight=28,
                    suppressColumnVirtualisation=True,
                )
                AgGrid(
                    _mx_df, gridOptions=_gb.build(), allow_unsafe_jscode=True,
                    # Anchos fijos: el ajuste automático (FIT_CONTENTS) se calcula
                    # con la pestaña aún oculta y recortaba los valores.
                    fit_columns_on_grid_load=False,
                    custom_css=AGGRID_GRID_CSS,
                    height=min(430, 34 + 28 * len(_body)),
                    theme="balham", update_on=[], key="mx_grid",
                )
                components.html(
                    build_html_table_copy_html(
                        render_word_table_html(_headers, _body),
                        btn_id="mx-copy-tab", fn="mxCopyTab", label="Copiar tabla (Word)",
                    ),
                    height=40,
                )

            with mx_gra:
                st.image(_cmp_png, use_container_width=True)
                components.html(build_image_copy_html(_cmp_png), height=40)
                st.download_button(
                    "Descargar PNG", data=_cmp_png,
                    file_name="peso_SA_IL_vs_horas.png", mime="image/png",
                    use_container_width=True, key="dl_cmp_png",
                )

        # ─────── PESTAÑA: PESO FINAL POR INSTRUMENTO DE EVALUACIÓN ───────
        with _tab_pf:
            from tools.indicadores_logro import peso_por_ie
            from tools.situaciones_informe import build_pie_png_simple

            _ie = peso_por_ie(il_recompute(pending, ce_ced, ce_list), ce_p)
            _ie_headers = ["Instrumento de evaluación", "% acumulado"]
            _ie_rows = [
                [k, f"{v * 100:.2f}".replace(".", ",") + " %"] for k, v in _ie
            ]
            _ie_rows.append(
                ["Total", f"{sum(v for _, v in _ie) * 100:.2f}".replace(".", ",") + " %"]
            )
            _iec1, _iec2 = st.columns([2, 2.3], gap="large")
            with _iec1:
                st.markdown(_tabla_html(_ie_headers, _ie_rows), unsafe_allow_html=True)
                components.html(
                    build_html_table_copy_html(
                        render_word_table_html(_ie_headers, _ie_rows),
                        btn_id="ie-copy-tab", fn="ieCopyTab", label="Copiar tabla (Word)",
                    ),
                    height=40,
                )
            with _iec2:
                _ie_png = build_pie_png_simple(
                    [k for k, _ in _ie], [v for _, v in _ie],
                    titulo="Peso por instrumento de evaluación", leyenda="Instrumento",
                )
                st.image(_ie_png, use_container_width=True)
                _g1, _g2 = st.columns(2)
                with _g1:
                    components.html(build_image_copy_html(_ie_png), height=40)
                with _g2:
                    st.download_button(
                        "Descargar PNG", data=_ie_png, file_name="peso_por_IE.png",
                        mime="image/png", use_container_width=True, key="dl_ie_png",
                    )

# PÁGINA: CONTENIDOS
elif page == "Contenidos":
    st.markdown(
        '<div class="panel-card"><h3>Contenidos</h3>'
        "<p>Contenidos de la materia y contenidos transversales de la etapa, tal "
        "como vienen en el currículo. Se marca en verde cada elemento que ya está "
        "asignado a algún indicador de logro (en su columna CON o CT).</p></div>",
        unsafe_allow_html=True,
    )

    if not _hay_proyecto():
        st.info("Abre un proyecto o crea uno nuevo en la barra de arriba.")
    else:
        from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
        from tools.indicadores_logro import usados_en_il
        from tools.situaciones_informe import AGGRID_GRID_CSS

        _el = st.session_state.elementos
        _il_state = st.session_state.get("il_pending") or st.session_state.get("il_rows") or []
        _con_used = usados_en_il(_il_state, "CON")
        _ct_used = usados_en_il(_il_state, "CT")

        _solo_falta = st.toggle("Ver solo los que faltan por asignar", value=False, key="ec_solo_falta")

        _rowstyle = JsCode(
            "function(p){if(!p.data) return null;"
            "return p.data.__ok ? {'background-color':'#dff2e2'} "
            ": {'background-color':'#fce4e4'}}"
        )

        def _render(items, key_field, label_field, header_cod, used_set, grid_key):
            rows = []
            for it in items:
                cod = it[key_field]
                ok = cod.replace(" ", "") in used_set
                rows.append({"__ok": ok, "●": "🟢" if ok else "🔴", header_cod: cod,
                             "Bloque": it.get("bloque", ""), "Descripción": it[label_field]})
            n_ok = sum(1 for r in rows if r["__ok"])
            st.caption(f"🟢 {n_ok} asignados · 🔴 {len(rows) - n_ok} sin asignar · {len(rows)} en total")
            if _solo_falta:
                rows = [r for r in rows if not r["__ok"]]
            if not rows:
                st.success("Todos asignados.")
                return
            df = pd.DataFrame(rows, columns=["__ok", "●", header_cod, "Bloque", "Descripción"])
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_default_column(editable=False, resizable=True, sortable=True, filter=False)
            gb.configure_column("__ok", hide=True)
            gb.configure_column("●", headerName="", width=46, pinned="left",
                                cellStyle={"textAlign": "center"})
            gb.configure_column(header_cod, width=88, pinned="left")
            # Bloque (solo contenidos de la materia): oculto si ninguno lo tiene.
            gb.configure_column("Bloque", width=220, tooltipField="Bloque",
                                hide=not any(r["Bloque"] for r in rows))
            gb.configure_column("Descripción", flex=1, minWidth=280, tooltipField="Descripción")
            gb.configure_grid_options(enableBrowserTooltips=True, tooltipShowDelay=300,
                                      rowHeight=28, getRowStyle=_rowstyle)
            AgGrid(df, gridOptions=gb.build(), allow_unsafe_jscode=True,
                   fit_columns_on_grid_load=False, custom_css=AGGRID_GRID_CSS,
                   height=min(460, 44 + 28 * len(df)), theme="balham",
                   update_on=[], key=grid_key)

        _tab_cm, _tab_ctr = _pestanas(
            "tabs_contenidos", ["Contenidos de la materia", "Contenidos transversales"]
        )
        with _tab_cm:
            if _tab_cm.open:
                _render(_el["contenidos"], "cod", "desc", "Código", _con_used, "ec_grid_con")
        with _tab_ctr:
            if _tab_ctr.open:
                _render(_el["transversales"], "num", "desc", "Nº", _ct_used, "ec_grid_ct")

# PÁGINAS: PROGRAMACIÓN DE AULA (Datos generales · Situaciones de aprendizaje)
# y GENERACIÓN DE DOCUMENTOS › Programación de aula. Comparten la preparación.
elif page in ("aula_datos", "aula_sa", "doc_aula"):
    _cab_t, _cab_p = {
        "aula_datos": ("Programación de aula · Datos generales",
                       "Datos del grupo, sus características y la evaluación."),
        "aula_sa": ("Programación de aula · Situaciones de aprendizaje",
                    "Descripción de cada situación de aprendizaje para la programación "
                    "de aula y sus actividades."),
        "doc_aula": ("Generar la programación de aula",
                     "Documento Word con la plantilla por defecto o con una tuya. Su "
                     "contenido se rellena en «Programación de aula»."),
    }[page]
    st.markdown(
        f'<div class="panel-card"><h3>{_cab_t}</h3><p>{_cab_p}</p></div>',
        unsafe_allow_html=True,
    )

    if not _hay_proyecto():
        st.info("Abre un proyecto o crea uno nuevo en la barra de arriba para empezar.")
    else:
        ss = st.session_state

        # Indicadores de logro ya recalculados (IL/SA/PIL rellenos). Se toma el
        # estado canónico (il_rows); si hay edición reciente en Diseño con IL
        # válidos, esa.
        _il_state = ss.get("il_rows") or []
        _ilp = ss.get("il_pending")
        if _ilp and all(r.get("IL") for r in _ilp):
            _il_state = _ilp
        _ce_p = {r["CE"]: r["P"] for r in ss.get("ce_rows", [])} or dict(ss.get("il_ce_p", {}))

        _sa_opts = _sa_pares()

        # Etiquetas con tildes de los campos que las llevan; el resto, del nombre.
        _ETIQ = {
            "numero_alumnos": "Número de alumnos",
            "alumnos_atencion_individualizada": "Alumnos con atención individualizada",
            "caracteristicas_fisicas_cognitivas_afectivas": "Características físicas, cognitivas y afectivas",
            "nivel_competencia_curricular": "Nivel de competencia curricular",
            "otras_caracteristicas_grupo": "Otras características del grupo",
            "resultados_evaluacion_inicial": "Resultados de la evaluación inicial",
            "conclusiones_evaluacion_inicial": "Conclusiones de la evaluación inicial",
            "resultados_evaluacion_aprendizajes": "Resultados de la evaluación de los aprendizajes",
            "revision_programacion": "Revisión de la programación",
            "contextualizacion": "Contextualización",
            "contenidos_materia": "Contenidos de la materia",
            "metodos": "Métodos",
            "organizacion_alumnado": "Organización del alumnado",
            "organizacion_espacio": "Organización del espacio",
            "materiales_recursos": "Materiales y recursos",
            "atencion_diferencias": "Atención a las diferencias individuales",
            "medidas_especificas": "Medidas específicas",
            "proceso_evaluacion": "Proceso de evaluación",
            "puesta_en_practica": "Puesta en práctica",
            "valoracion": "Valoración",
        }

        def _hum(k):
            return _ETIQ.get(k) or k.replace("_", " ").strip().capitalize()

        if page == "doc_aula":
            # ── Generar programación de aula
            gc1, gc2 = st.columns([2.2, 1.6], vertical_alignment="bottom")
            _tpl = gc1.file_uploader("Plantilla Word (opcional)", type=["docx"], key="pa_tpl")
            if gc2.button("Generar programación de aula", use_container_width=True, type="primary", key="pa_gen"):
                from tools.consistencia import revisar

                _iss = revisar(*_estado_coherencia())
                if _iss:
                    _dlg_coherencia(_iss, contexto="generar")
                else:
                    try:
                        ss.pa_docx = _generar_docx()
                        ss.pa_gen_msg = ""
                    except Exception as exc:
                        ss.pa_gen_msg = f"No se ha podido generar: {exc}"
                        ss.pop("pa_docx", None)
            if ss.get("pa_gen_msg"):
                st.error(ss.pa_gen_msg)
            if ss.get("pa_docx"):
                st.download_button(
                    "Descargar programación (Word)", data=ss.pa_docx,
                    file_name="programacion_aula.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

        # Datos generales va solo en su página; Situaciones de aprendizaje, en
        # dos pestañas. (`_Zona` = apartado sin pestaña; ver su definición.)
        _tab_pad = _tab_pasa = _tab_pact = _Zona()
        if page == "aula_datos":
            _tab_pad = _Zona(True)
        elif page == "aula_sa":
            _tab_pasa, _tab_pact = _pestanas(
                "tabs_aula", ["Descripción SA", "Actividades por situación de aprendizaje"]
            )

        _lbl = {sa: f"SA {sa}: {d}" for sa, d in _sa_opts}
        _nums_sa = [sa for sa, _ in _sa_opts]

        def _sel_sa(key):
            """Selector de SA. Las pestañas «Campos de aula» y «Actividades»
            comparten la SA elegida (pa_sa_actual): cada una tiene su widget,
            pero se inicializa con la última elegida en cualquiera de ellas."""
            if ss.get("pa_sa_actual") in _nums_sa:
                ss[key] = ss.pa_sa_actual
            # (banda destacada: es la selección principal de la pestaña;
            # estilo en el CSS general, clase st-key-pasel_…)
            with st.container(key=f"pasel_{key}"):
                sel = st.selectbox(
                    "Situación de aprendizaje", _nums_sa,
                    format_func=lambda s: _lbl.get(s, str(s)), key=key,
                    on_change=lambda: ss.__setitem__("pa_sa_actual", ss[key]),
                )
            ss.pa_sa_actual = sel
            return sel

        # ── PESTAÑA: Datos generales
        _LARGOS = {
            "alumnos_atencion_individualizada", "caracteristicas_fisicas_cognitivas_afectivas",
            "nivel_competencia_curricular", "otras_caracteristicas_grupo",
            "resultados_evaluacion_inicial", "conclusiones_evaluacion_inicial",
            "resultados_evaluacion_aprendizajes", "revision_programacion",
        }
        def _pad_sync(k):
            """Copia lo tecleado al estado e invalida el proyecto antes del
            rerun: la barra de arriba lo recalcula antes de que esta página
            vuelva a pintar los campos (mismo patrón que _fam_sync)."""
            ss.pa_datos[k] = ss[f"pad_{k}"]
            ss.pop("prog_out", None)
            ss.pop("pa_docx", None)

        with _tab_pad:
            if _tab_pad.open:
                _cortos = [k for k in ss.pa_campos_datos if k not in _LARGOS]
                _seccion("Grupo")
                _cc = st.columns(2)
                for i, k in enumerate(_cortos):
                    ss.pa_datos[k] = _cc[i % 2].text_input(_hum(k), value=ss.pa_datos.get(k, ""), key=f"pad_{k}",
                                                        on_change=_pad_sync, args=(k,))
                _seccion("Características del grupo y evaluación")
                for k in ss.pa_campos_datos:
                    if k in _LARGOS:
                        ss.pa_datos[k] = st.text_area(_hum(k), value=ss.pa_datos.get(k, ""), key=f"pad_{k}", height=90,
                                                   on_change=_pad_sync, args=(k,))

        # ── PESTAÑA: Campos de la programación de aula de cada SA. Se emparejan
        # por título (las ediciones de la sesión se guardan por título de SA y
        # el proyecto las asigna a su SA al guardar).
        with _tab_pasa:
            if _tab_pasa.open:
                import re as _re

                sa_sel = _sel_sa("pa_sa_sel_campos")
                _dsa_sel = next((d for n, d in _sa_opts if n == sa_sel), "")
                _norm = lambda s: _re.sub(r"\s+", " ", str(s or "")).strip().lower()
                _base = {}
                for _e in ss.pa_sa_cols:
                    if _norm(_e.get("valores", {}).get("titulo")) == _norm(_dsa_sel):
                        _base = _e["valores"]
                        break
                _tri_sel = next((t for n, _d, t in _sa_datos() if n == sa_sel), "")
                def _pasa_sync(dsa, campo, key):
                    # Igual que _pad_sync, para los campos de aula de la SA.
                    ss.pa_sa_edits.setdefault(dsa, dict(_base))[campo] = ss[key]
                    ss.pop("prog_out", None)
                    ss.pop("pa_docx", None)

                _cur = ss.pa_sa_edits.get(_dsa_sel, dict(_base))
                # titulo y trimestre son automáticos (de la tabla de situaciones)
                _cur["titulo"] = _dsa_sel
                _cur["trimestre"] = _tri_sel
                # (texto, no campos deshabilitados: tienen poco contraste)
                _seccion(
                    f"SA {sa_sel} · {_dsa_sel or 'sin título'}",
                    sub=f"Trimestre {_tri_sel or '—'} · título y trimestre se toman de la "
                        "tabla de situaciones de aprendizaje.",
                )
                for campo in ss.pa_sa_campos:
                    if campo in ("titulo", "trimestre"):
                        continue
                    _cur[campo] = st.text_area(
                        _hum(campo), value=_cur.get(campo, ""),
                        key=f"pasa_{sa_sel}_{campo}", height=70,
                        on_change=_pasa_sync, args=(_dsa_sel, campo, f"pasa_{sa_sel}_{campo}"),
                    )
                ss.pa_sa_edits[_dsa_sel] = _cur

        # ── PESTAÑA: Actividades por situación de aprendizaje. Todo lo que se
        # ve (los tres cuadros) está en ui/actividades.py.
        with _tab_pact:
            if _tab_pact.open:
                from ui import actividades as ui_actividades

                sa_sel = _sel_sa("pa_sa_sel")
                ui_actividades.pintar(sa_sel, _il_state, _ce_p)

# PÁGINA: GENERACIÓN DE DOCUMENTOS › OTROS INFORMES (por ahora, solo el de
# información a familias; los que vengan, con un selector de informe arriba).
elif page == "doc_otros":
    st.markdown(
        '<div class="panel-card"><h3>Otros informes · Información a familias</h3>'
        "<p>Documento para informar al alumnado y a las familias sobre la evaluación "
        "(ORDEN EDU/424/2024, art. 12 · ORDEN EDU/425/2024, art. 10). Lo que no sale "
        "de la programación se escribe aquí y se guarda en el proyecto.</p></div>",
        unsafe_allow_html=True,
    )

    if not _hay_proyecto():
        st.info("Abre un proyecto o crea uno nuevo en la barra de arriba para empezar.")
    else:
        from tools.info_familias import (
            AGENTES,
            CAMPOS,
            campos_vacios,
            datos_familias,
            generar_docx,
            tabla_sa_filas,
        )
        from tools.situaciones_informe import build_pie_png_simple

        ss = st.session_state

        _calc = datos_familias(
            sits=_sa_filas(),
            ce_list=ss.il_ce_list,
            ce_ced=ss.il_ce_ced,
            ce_p={r["CE"]: r["P"] for r in ss.get("ce_rows", [])} or dict(ss.get("il_ce_p", {})),
            il_rows=il_recompute(ss.get("il_pending", ss.get("il_rows", [])), ss.il_ce_ced, ss.il_ce_list),
            elementos=ss.get("elementos", {}),
        )
        _nums = [n for n, _p in _calc["competencias"]]
        _comp_txt = ss.cur["competencias"]  # texto del currículo, no editable

        def _fam_sync():
            """Pasa lo tecleado (widgets fam_w_*) al estado canónico e invalida
            el proyecto y el Word ya generados. Va como on_change: así, en el
            rerun, la barra de arriba recalcula el proyecto ya con el texto nuevo."""
            for k, _l, _h in CAMPOS:
                if f"fam_w_{k}" in ss:
                    ss.fam_campos[k] = ss[f"fam_w_{k}"]
            ss.pop("prog_out", None)
            ss.pop("fam_docx", None)

        # ── Generar documento
        fg1, fg2 = st.columns([2.2, 1.6], vertical_alignment="bottom")
        _fam_tpl = fg1.file_uploader("Plantilla Word (opcional)", type=["docx"], key="fam_tpl")
        if fg2.button("Generar documento para familias", use_container_width=True,
                      type="primary", key="fam_gen"):
            try:
                ss.fam_docx = generar_docx(
                    datos_generales=dict(ss.get("pa_datos", {})),
                    calculo=_calc,
                    campos=ss.fam_campos,
                    competencias=_comp_txt,
                    template_source=_fam_tpl,
                )
                ss.fam_msg = ""
            except Exception as exc:
                ss.fam_msg = f"No se ha podido generar: {exc}"
                ss.pop("fam_docx", None)
        if ss.get("fam_msg"):
            st.error(ss.fam_msg)
        if ss.get("fam_docx"):
            _dg = ss.get("pa_datos", {})
            _nom = "_".join(
                re.sub(r"[^\w]+", "", str(_dg.get(k, "")))
                for k in ("materia", "curso", "grupo") if _dg.get(k)
            )
            fg2.download_button(
                "Descargar documento (Word)", data=ss.fam_docx,
                file_name=f"informacion_familias_{_nom or 'materia'}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )

        _faltan = campos_vacios(ss.fam_campos, _comp_txt, _nums)
        if _faltan:
            st.warning(
                "Faltan por rellenar (en el documento saldrán como «pendiente de "
                "completar»):\n\n- " + "\n- ".join(_faltan)
            )

        _tab_comp, _tab_cal, _tab_aten, _tab_prev = _pestanas(
            "tabs_familias",
            ["Competencias específicas", "Calificación y promoción",
             "Atención individualizada", "Vista previa por SA"],
        )
        _AYUDA = {k: (lbl, h) for k, lbl, h in CAMPOS}

        def _area(k, height=110):
            lbl, h = _AYUDA[k]
            st.text_area(lbl, value=ss.fam_campos.get(k, ""), help=h, height=height,
                         key=f"fam_w_{k}", on_change=_fam_sync)

        with _tab_comp:
            if _tab_comp.open:
                _norma = ss.proy_materia.get("normativa") or "currículo"
                st.caption(
                    "Una por cada competencia específica que aparece en los criterios "
                    f"(el primer número del CE: 2.4 → competencia 2). Texto del {_norma}."
                )
                _peso = dict(_calc["competencias"])
                _cdo = ss.cur.get("comp_descriptores", {})
                st.markdown(
                    _tabla_html(
                        ["Nº", "Competencia específica", "Descriptores", "Peso"],
                        [
                            [n, _comp_txt.get(n, ""), _cdo.get(n, ""),
                             f"{_peso[n] * 100:.2f} %".replace(".", ",")]
                            for n in _nums
                        ],
                    ),
                    unsafe_allow_html=True,
                )

        with _tab_cal:
            if _tab_cal.open:
                st.caption("Según la Propuesta Curricular del centro y la programación didáctica.")
                for k in ("redondeo_criterios", "redondeo_materia", "competencias_clave",
                          "promocion_titulacion"):
                    _area(k)

        with _tab_aten:
            if _tab_aten.open:
                st.warning(
                    "Este documento va a **todas** las familias: describe las medidas en "
                    "general, sin datos de alumnos concretos (lo de «Datos generales» de la "
                    "programación de aula **no** se usa aquí)."
                )
                for k in ("plan_recuperacion", "plan_refuerzo", "apoyos", "adaptaciones"):
                    _area(k, height=90)

        with _tab_prev:
            if _tab_prev.open:
                _sas = _calc["situaciones"]
                if not _sas:
                    st.info("No hay situaciones de aprendizaje.")
                else:
                    _by_n = {s["numero"]: s for s in _sas}
                    _sel = st.selectbox(
                        "Situación de aprendizaje", list(_by_n),
                        format_func=lambda n: f"{n}: {_by_n[n]['titulo']}", key="fam_prev_sa",
                    )
                    _s = _by_n[_sel]
                    st.markdown(
                        f"**{_s['EV'] or '—'}ª evaluación** · {float(_s['HSA'] or 0):g} h "
                        f"({_s['pct_h'] * 100:.2f} % de las horas) · peso en la calificación "
                        f"de la materia: **{_s['peso'] * 100:.2f} %**".replace(".", ",")
                    )
                    _h, _r = tabla_sa_filas(_s)
                    pv1, pv2 = st.columns([3.2, 1.6], gap="medium")
                    with pv1:
                        if _r:
                            st.markdown(_tabla_html(_h, _r), unsafe_allow_html=True)
                            if _s["agentes"]:
                                st.caption("Agente evaluador: " + "; ".join(
                                    f"{a} = {AGENTES.get(a, a)}" for a in _s["agentes"]))
                        else:
                            st.caption("Esta SA no tiene indicadores de logro asignados.")
                    with pv2:
                        if _s["instrumentos"]:
                            st.image(build_pie_png_simple(
                                [k for k, _ in _s["instrumentos"]],
                                [v for _, v in _s["instrumentos"]],
                                titulo=f"Instrumentos · SA {_s['numero']}", leyenda="Instrumento",
                            ), use_container_width=True)

# PÁGINA: PROGRAMACIÓN DIDÁCTICA › REDACCIÓN. Una pestaña por capítulo de la
# programación didáctica; todo lo que se ve está en ui/redaccion.py y qué
# lleva cada capítulo, en tools/redaccion.py.
elif page == "Redacción":
    st.markdown(
        '<div class="panel-card"><h3>Redacción de la programación didáctica</h3>'
        "<p>Un capítulo por pestaña, según la guía de la Junta de Castilla y León. Los textos "
        "vienen con una propuesta que puedes cambiar; las tablas y gráficas marcadas como "
        "automáticas salen de «Diseño de la programación» y solo eliges si aparecen. El "
        "documento se genera en «Generación de documentos».</p></div>",
        unsafe_allow_html=True,
    )
    if not _hay_proyecto():
        st.info("Abre un proyecto o crea uno nuevo en la barra de arriba para empezar.")
    else:
        from ui import redaccion as ui_redaccion

        ui_redaccion.pintar(
            _pestanas("tabs_redaccion", [c["pestana"] for c in red_def.CAPITULOS]),
            _datos_redaccion,
        )

# PÁGINA: GENERACIÓN DE DOCUMENTOS › PROGRAMACIÓN DIDÁCTICA
elif page == "doc_didactica":
    st.markdown(
        '<div class="panel-card"><h3>Generar la programación didáctica</h3>'
        "<p>Documento Word con la plantilla por defecto o con una tuya. Su contenido se "
        "escribe en «Programación didáctica › Redacción» y las tablas y gráficas salen de "
        "«Diseño de la programación».</p></div>",
        unsafe_allow_html=True,
    )
    if not _hay_proyecto():
        st.info("Abre un proyecto o crea uno nuevo en la barra de arriba para empezar.")
    else:
        from tools.programacion_didactica import generar_docx as _generar_pd
        from tools.programacion_didactica import plantilla_por_defecto

        ss = st.session_state
        dg1, dg2 = st.columns([2.2, 1.6], vertical_alignment="bottom")
        _pd_tpl = dg1.file_uploader("Plantilla Word (opcional)", type=["docx"], key="pd_tpl")
        if dg2.button("Generar programación didáctica", use_container_width=True,
                      type="primary", key="pd_gen"):
            try:
                ss.pd_docx = _generar_pd(
                    materia=ss.proy_materia, redaccion=ss.red, datos=_datos_redaccion(),
                    template_source=_pd_tpl,
                )
                ss.pd_msg = ""
            except Exception as exc:
                ss.pd_msg = f"No se ha podido generar: {exc}"
                ss.pop("pd_docx", None)
        if ss.get("pd_msg"):
            st.error(ss.pd_msg)
        _m = ss.proy_materia
        _nom = re.sub(r"[^\w]+", "_", f"{_m['nombre']}_{_m['curso']}").strip("_")
        db1, db2, _db3 = st.columns([1.5, 1.5, 3])
        if ss.get("pd_docx"):
            db1.download_button(
                "Descargar programación (Word)", data=ss.pd_docx,
                file_name=f"programacion_didactica_{_nom}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="pd_dl",
            )
        db2.download_button(
            "Descargar la plantilla por defecto", data=plantilla_por_defecto(),
            file_name="programacion_didactica_template.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="pd_tpl_dl",
            help="Para cambiarle la portada, los estilos o el orden de los capítulos en Word "
                 "y subirla después como plantilla propia. Hay que respetar las etiquetas {{ … }}.",
        )

        _pend = red_def.pendientes(ss.red, red_def.etapa_app(_m))
        if _pend:
            _por_cap: dict[str, list[str]] = {}
            for _cap_n, _etq in _pend:
                _por_cap.setdefault(_cap_n, []).append(_etq)
            st.warning(
                "Textos sin rellenar en Redacción (no saldrán en el documento):\n\n"
                + "\n".join(f"- **{c}**: {', '.join(e)}" for c, e in _por_cap.items())
            )
        else:
            st.success("Todos los textos de Redacción están rellenos.")
