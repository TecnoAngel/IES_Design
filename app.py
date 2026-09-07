from __future__ import annotations

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
        d.rounded_rectangle((8, 8, 120, 120), radius=26, fill=(166, 24, 46, 255))
        d.rounded_rectangle((30, 54, 98, 74), radius=10, fill=(224, 162, 28, 255))
        return img
    except Exception:
        return None


st.set_page_config(page_title="IES Diseño", page_icon=_favicon(), layout="wide")

# Aviso claro si se ha lanzado con el entorno equivocado (p. ej. el venv de otro
# proyecto que VSCode dejó activo): faltarían dependencias.
import importlib.util

_faltan = [
    m for m in ("matplotlib", "openpyxl", "st_aggrid", "docxtpl")
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
    /* Paleta del tema: rojo carmín + oro. */
    :root {
        --jcyl-red: #A6182E;
        --jcyl-red-2: #C01848;
        --jcyl-gold: #E0A21C;
        --jcyl-ink: #221C18;
        --jcyl-cream: #FAF4EC;
        --jcyl-line: #E6D8C6;
    }
    .topbar {
        padding: 1.1rem 1.2rem;
        border-radius: 16px;
        background: linear-gradient(115deg, #8f1526 0%, #b41f3a 45%, #d99a1e 118%);
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 6px 18px rgba(166,24,46,0.28);
    }
    .topbar-title { font-size: 1.8rem; font-weight: 700; line-height: 1.1; }
    .topbar-sub { font-size: 0.95rem; opacity: 0.95; margin-top: 0.35rem; }
    .section-title {
        background: linear-gradient(120deg, var(--jcyl-red) 0%, var(--jcyl-gold) 100%);
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
        box-shadow: 0 2px 10px rgba(166,24,46,0.10);
        background: #ffffff;
        border: 1px solid var(--jcyl-line);
        border-left: 4px solid var(--jcyl-red);
        color: #333333;
    }
    .panel-card h3 {
        background: linear-gradient(120deg, var(--jcyl-red) 0%, var(--jcyl-gold) 100%);
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
        background: linear-gradient(100deg, #a6182e 0%, #c1304c 70%, #d99a1e 140%);
        padding: 0.5rem 0.9rem;
        border-radius: 10px;
        margin: 1.6rem 0 0.7rem 0;
        box-shadow: 0 3px 10px rgba(166,24,46,0.22);
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
        box-shadow: 0 2px 10px rgba(166,24,46,0.08);
    }
    /* Secciones colapsables de una pestaña (Situaciones, Criterios, …). */
    [class*="st-key-secc_"] { margin-top: 1.3rem; }
    [class*="st-key-secc_"] [data-testid="stExpander"] {
        border: 1px solid var(--jcyl-line) !important;
        border-left: 6px solid var(--jcyl-red) !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 10px rgba(166,24,46,0.10);
    }
    [class*="st-key-secc_"] [data-testid="stExpander"] summary {
        padding: 0.55rem 1rem !important;
        font-size: 1.5rem !important;
        font-weight: 750 !important;
    }
    [class*="st-key-secc_"] [data-testid="stExpander"] summary * {
        font-size: 1.5rem !important;
        font-weight: 750 !important;
        letter-spacing: 0.01em;
    }
    [class*="st-key-secc_"] [data-testid="stExpander"] summary:hover {
        color: var(--jcyl-red) !important;
    }
    [class*="st-key-secc_a_"] [data-testid="stExpander"] { background: #fdfaf4; }
    [class*="st-key-secc_a_"] [data-testid="stExpander"] summary { background: #f7efe1; }
    [class*="st-key-secc_b_"] [data-testid="stExpander"] { background: #ffffff; }
    /* Cabecera-botón de las secciones autónomas (_seccion_simple). */
    [class*="st-key-sechdr_"] { margin-top: 1.3rem; }
    [class*="st-key-sechdr_"] button {
        justify-content: flex-start !important;
        text-align: left !important;
        padding: 0.55rem 1rem !important;
        background: #f7efe1 !important;
        border: 1px solid var(--jcyl-line) !important;
        border-left: 6px solid var(--jcyl-red) !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 10px rgba(166,24,46,0.10) !important;
        color: var(--jcyl-ink) !important;
    }
    [class*="st-key-sechdr_"] button > div,
    [class*="st-key-sechdr_"] button [data-testid="stMarkdownContainer"] {
        justify-content: flex-start !important;
        align-items: flex-start !important;
        width: 100% !important;
        text-align: left !important;
    }
    [class*="st-key-sechdr_"] button p {
        font-size: 1.5rem !important;
        font-weight: 750 !important;
        letter-spacing: 0.01em;
        text-align: left !important;
        width: 100% !important;
    }
    [class*="st-key-sechdr_"] button:hover {
        border-left-color: var(--jcyl-gold) !important;
        color: var(--jcyl-red) !important;
    }
    .mini-label {
        font-size: 0.8rem;
        font-weight: 600;
        opacity: 0.78;
        margin-bottom: 0.2rem;
    }
    /* Navegación: pastilla activa en rojo JCyL. */
    div[data-baseweb="segmented-control"] [aria-checked="true"],
    button[kind="segmented_controlActive"] {
        background: var(--jcyl-red) !important;
        color: #fff !important;
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

# streamlit-aggrid se renderiza en un <iframe>: dentro de un st.expander puede
# montarse con ancho 0 y quedarse "en una columna". Este parche fuerza el ancho
# de esos iframes al 100 % y lanza un 'resize' para que AG-Grid recoloque las
# columnas, al abrir/cerrar cualquier sección y durante los primeros segundos.
components.html(
    """
    <script>
    (function () {
      const doc = window.parent.document;
      function nudge() {
        doc.querySelectorAll('iframe').forEach(f => {
          if (f.closest('[data-testid="stExpander"]')) {
            f.style.width = '100%';
            try { f.contentWindow.dispatchEvent(new Event('resize')); } catch (e) {}
          }
        });
        window.parent.dispatchEvent(new Event('resize'));
      }
      doc.addEventListener('click', e => {
        if (e.target.closest('summary')) { [60, 250, 600].forEach(t => setTimeout(nudge, t)); }
      }, true);
      let n = 0;
      const iv = setInterval(() => { nudge(); if (++n > 20) clearInterval(iv); }, 350);
    })();
    </script>
    """,
    height=0,
)

# st.tabs no conserva la pestaña activa entre reruns (cada clic en un botón
# devuelve la vista a la primera pestaña), así que la navegación se hace con
# un widget normal atado a session_state para que sea persistente.
PAGES = ["Inicio", "Diseño de la programación", "Contenidos", "Programación de aula"]
page = st.segmented_control(
    "Navegación",
    PAGES,
    default=PAGES[0],
    key="active_page",
    required=True,
    label_visibility="collapsed",
)

# ── Barra global del Excel de programación: cargar / descargar desde cualquier
#    pestaña. La descarga se rellena luego (dl_box), cuando la pestaña activa ya
#    ha calculado los cambios.
from tools.indicadores_logro import read_elementos_curriculares, read_indicadores
from tools.indicadores_logro import recompute as il_recompute
from tools.situaciones_aprendizaje import TRIMESTRES, read_situaciones

SA_COLS = ["SA", "EV", "DSA", "HSA"]
IL_COLS = ["CE", "CED", "IL", "PIL", "PIL%", "DIL", "DO", "CON", "CT", "IE", "CC", "AE", "SA"]

with st.container(border=True):
    ubar1, ubar2 = st.columns([3, 2])
    with ubar1:
        prog_excel = st.file_uploader(
            "Excel de programación (.xlsx)",
            type=["xlsx", "xlsm"],
            key="prog_excel_uploader",
            label_visibility="collapsed",
        )
        if st.session_state.get("prog_sello_cargado"):
            st.caption(f"Versión cargada: {st.session_state.prog_sello_cargado}")
    dl_box = ubar2.container()

def _trimestre_txt(ev):
    try:
        n = int(ev)
    except (TypeError, ValueError):
        return ""
    return f"{n}º trimestre" if n in (1, 2, 3) else ""


def _sa_datos():
    """(nº, descripción, trimestre) de cada SA, ordenados por nº. Del estado
    editado si lo hay, si no del Excel cargado."""
    ss = st.session_state
    rows = ss.get("sa_grid_rows")
    if not rows and "sa_df" in ss:
        rows = [
            {
                "SA": None if pd.isna(v[0]) else int(v[0]),
                "EV": None if pd.isna(v[1]) else v[1],
                "DSA": str(v[2] or ""),
            }
            for v in ss.sa_df.itertuples(index=False)
        ]
    return sorted(
        (r["SA"], r["DSA"], _trimestre_txt(r.get("EV")))
        for r in (rows or []) if r.get("SA") is not None
    )


def _sa_pares():
    return [(n, d) for n, d, _t in _sa_datos()]


def _estado_coherencia():
    ss = st.session_state
    sits = [{"SA": n, "DSA": d} for n, d in _sa_pares()]
    return (
        sits,
        ss.get("il_ce_list", []),
        ss.get("il_rows", []),
        ss.get("pa_acts", []),
        ss.get("pa_sa_cols", []),
    )


if prog_excel is not None and st.session_state.get("prog_loaded_name") != prog_excel.name:
    try:
        _sa = read_situaciones(prog_excel)
        st.session_state.sa_df = pd.DataFrame(
            [[s.sa, s.ev, s.dsa, s.hsa] for s in _sa.situaciones], columns=SA_COLS
        )
        st.session_state.sa_previstas = {
            t: float(_sa.horas_previstas.get(t, 0.0)) for t in TRIMESTRES
        }
        _il = read_indicadores(prog_excel)
        st.session_state.il_rows = il_recompute(_il["rows"], _il["ce_ced"], _il["ce_list"])
        st.session_state.il_ce_list = _il["ce_list"]
        st.session_state.il_ce_ced = _il["ce_ced"]
        st.session_state.il_ce_p = _il["ce_p"]
        st.session_state.il_aux = _il["aux"]
        st.session_state.elementos = read_elementos_curriculares(prog_excel)
        st.session_state.prog_loaded_name = prog_excel.name
        from tools.sellado import leer_sello

        st.session_state.prog_sello_cargado = leer_sello(prog_excel.getvalue())
        from tools.programacion_aula_editor import read_prog_aula

        _pae = read_prog_aula(prog_excel)
        st.session_state.pa_datos = dict(_pae["datos"])
        st.session_state.pa_campos_datos = [k for k, _ in _pae["datos"]]
        st.session_state.pa_sa_campos = _pae["sa_campos"]
        st.session_state.pa_sa_cols = _pae["sa_cols"]
        st.session_state.pa_acts = _pae["actividades"]
        st.session_state.pa_sa_edits = {}

        # al cambiar de archivo, se descartan los estados canónicos derivados
        for _k in (
            "prog_out", "prog_base", "sa_grid_rows", "ce_rows", "il_pending",
            "pa_docx", "consist_seen",
        ):
            st.session_state.pop(_k, None)

        from tools.consistencia import revisar as _revisar

        st.session_state.consist_issues = _revisar(*_estado_coherencia())
    except Exception as exc:
        st.error(f"No se ha podido leer el Excel: {exc}")


def _guardar_todo() -> bytes:
    """Aplica sobre el Excel subido todos los cambios en sesión (situaciones,
    criterios, indicadores y programación de aula) y devuelve los bytes."""
    from io import BytesIO as _B

    from tools.indicadores_logro import save_criterios, save_indicadores
    from tools.situaciones_aprendizaje import Situacion, save_situaciones

    ss = st.session_state
    data = ss.get("prog_base") or prog_excel.getvalue()

    if "sa_grid_rows" in ss:
        sits_g = [
            Situacion(sa=r["SA"], ev=r["EV"], dsa=r["DSA"], hsa=r["HSA"])
            for r in ss.sa_grid_rows
        ]
        prev_g = {
            t: float(ss.get(f"sa_prev_{t}", ss.get("sa_previstas", {}).get(t, 0.0)))
            for t in TRIMESTRES
        }
        data = save_situaciones(_B(data), sits_g, prev_g)

    il_g = il_recompute(
        ss.get("il_pending", ss.get("il_rows", [])), ss.il_ce_ced, ss.il_ce_list
    )
    data = save_indicadores(_B(data), il_g, ss.il_ce_ced, ss.il_ce_list)

    ce_p_g = {r["CE"]: r["P"] for r in ss.get("ce_rows", [])} or dict(ss.il_ce_p)
    data = save_criterios(_B(data), ce_p_g, ss.il_ce_list)

    if "pa_datos" in ss:
        from tools.consistencia import regenerar_p_aula_sa
        from tools.programacion_aula_editor import save_actividades, save_datos_generales

        data = save_datos_generales(_B(data), dict(ss.pa_datos))
        # P_Aula_SA se reconstruye siempre desde la lista de SA actual: las SA
        # nuevas obtienen columna, y titulo/trimestre se pisan con lo de la tabla
        # de situaciones. El resto: ediciones de sesión (por título) o lo previo.
        _sad = _sa_datos()
        data = regenerar_p_aula_sa(
            _B(data),
            [d for _, d, _t in _sad],
            edits=ss.get("pa_sa_edits", {}),
            sa_trimestres=[t for _, _d, t in _sad],
        )
        _pil = {r["IL"]: float(r["PIL"] or 0) for r in il_g}
        data = save_actividades(_B(data), ss.get("pa_acts", []), _pil)

    from tools.sellado import sellar

    data, ss.prog_sello = sellar(data)
    return data


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
                    "A": a["A"], "DA": a["DA"],
                    "valor_programacion": a["valor_prog"], "valor_sa": a["valor_sa"],
                }
                for a in val if a.get("SA") == n
            ],
        }
    return out


def _generar_docx(data_bytes) -> bytes:
    from io import BytesIO as _BD

    from tools.programacion_aula import run_programacion_aula

    return run_programacion_aula(
        _BD(data_bytes),
        st.session_state.get("pa_tpl"),
        resumen_por_sa=_resumen_por_sa_docx(),
    )


def _seccion(titulo, idx, *, abierto=False):
    """Sección colapsable de una pestaña (`st.expander`). El cuerpo se ejecuta
    siempre (aunque esté plegada) para no romper el flujo de datos entre
    secciones. `idx` fija el tono alterno vía CSS (`.st-key-secc_<par>_<idx>`)."""
    par = "a" if idx % 2 == 0 else "b"
    return st.expander(titulo, expanded=abierto, key=f"secc_{par}_{idx}")


def _seccion_simple(titulo, idx, *, abierto=True):
    """Sección colapsable para bloques autónomos (no exportan variables a otros
    bloques). Cabecera-botón grande y, si está plegada, el cuerpo NO se ejecuta
    → una tabla AgGrid solo se monta con ancho real. Devuelve el estado abierto."""
    ss = st.session_state
    k = f"secs_{idx}"
    ss.setdefault(k, abierto)
    with st.container(key=f"sechdr_{idx}"):
        if st.button(f"{'▾' if ss[k] else '▸'}  {titulo}", key=f"secs_btn_{idx}",
                     use_container_width=True):
            ss[k] = not ss[k]
            st.rerun()
    return ss[k]


def _calc_sesiones_por_evaluacion():
    """Menú colapsable (dentro de Situaciones de aprendizaje): con el calendario
    escolar oficial de Castilla y León y las sesiones de la materia por día de la
    semana, cuenta día a día los días lectivos y las sesiones de cada evaluación.
    El resultado puede volcarse a las «horas previstas» de cada trimestre."""
    from datetime import date as _date  # noqa: F401  (por si se usa en el futuro)

    ss = st.session_state
    ss.setdefault("sa_previstas", {})

    with _seccion("Calcular sesiones por evaluación (calendario oficial)", 1):
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
        dcols = st.columns(5)
        ses_dia = {
            i: dc.number_input(
                nom, min_value=0, max_value=6, step=1,
                value=int(ss.get(f"ses_d{i}", 0)), key=f"ses_d{i}",
            )
            for i, (dc, nom) in enumerate(zip(dcols, DIAS_SEMANA))
        }

        deftr = default_trimester_ranges(cal)
        st.markdown(
            '<div class="mini-label">Fechas de cada evaluación (se proponen en torno a '
            "Navidad y Semana Santa; ajústalas si hace falta)</div>",
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
                    key=f"ses_tr{i}a", format="DD/MM/YYYY",
                )
                b = st.date_input(
                    "Fin", value=ss.get(f"ses_tr{i}b", deftr[i][1]),
                    min_value=cal.course_start, max_value=cal.course_end,
                    key=f"ses_tr{i}b", format="DD/MM/YYYY",
                )
                rangos.append((a, b))

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

        loc = None
        if st.checkbox("Añadir fiesta local", value=ss.get("ses_loc_on", False), key="ses_loc_on"):
            loc = st.date_input(
                "Fecha de la fiesta local", value=ss.get("ses_loc", cal.course_start),
                min_value=cal.course_start, max_value=cal.course_end,
                key="ses_loc", format="DD/MM/YYYY",
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
        ed = st.data_editor(
            ss.ipf_obj_df, hide_index=True, use_container_width=True, key="ipf_obj_ed",
            column_config={
                "Instrumento": st.column_config.TextColumn(disabled=True),
                "Objetivo (%)": st.column_config.NumberColumn(
                    min_value=0.0, max_value=100.0, step=0.5, format="%.1f"
                ),
            },
        )
        obj = {r["Instrumento"]: float(r["Objetivo (%)"] or 0.0) for _, r in ed.iterrows()}
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
        _tab_p.dataframe(
            pd.DataFrame([{"CE": ce, "P sugerido": pce.get(ce, 0)} for ce in ce_list]),
            hide_index=True, use_container_width=True, height=240,
        )
        _tab_il.dataframe(
            pd.DataFrame([
                {"IL": il, "CE": _info.get(il, {}).get("CE", ""), "PIL sugerido": v}
                for il, v in pil.items()
            ]),
            hide_index=True, use_container_width=True, height=240,
        )

    b1, b2, b3 = st.columns(3)
    if b1.button("Cargar P y PIL", type="primary", use_container_width=True,
                 disabled=not suma_ok, key="ipf_all"):
        _ipf_cargar(pce, pil, ce_ced, ce_list)
    if b2.button("Cargar solo P", use_container_width=True,
                 disabled=not suma_ok, key="ipf_p"):
        _ipf_cargar(pce, None, ce_ced, ce_list)
    if b3.button("Cargar solo PIL", use_container_width=True,
                 disabled=not suma_ok, key="ipf_pil"):
        _ipf_cargar(None, pil, ce_ced, ce_list)


def _aplicar_regeneracion(issues):
    """Aplica en sesión los arreglos automáticos de los desajustes fixables:
    1 IL en blanco por CE sin indicador, quita actividades huérfanas y regenera
    las columnas de P_Aula_SA (deja `prog_base` con ese Excel de partida)."""
    ss = st.session_state
    from io import BytesIO as _B2

    from tools.consistencia import add_il_para_ce, quitar_actividades_huerfanas, regenerar_p_aula_sa
    from tools.programacion_aula_editor import read_prog_aula

    _ce_sin = next((it["datos"] for it in issues if it["clave"] == "ce_sin_il"), [])
    if _ce_sin:
        ss.il_rows = il_recompute(
            add_il_para_ce(ss.il_rows, _ce_sin), ss.il_ce_ced, ss.il_ce_list
        )
        ss.pop("il_pending", None)
    if any(it["clave"] == "act_huerfanas" for it in issues):
        ss.pa_acts = quitar_actividades_huerfanas(ss.get("pa_acts", []), ss.il_rows)
    if any(it["clave"] == "pasa_desajuste" for it in issues):
        _base = ss.get("prog_base") or prog_excel.getvalue()
        _sad = _sa_datos()
        _reg = regenerar_p_aula_sa(
            _B2(_base), [d for _, d, _t in _sad], sa_trimestres=[t for _, _d, t in _sad]
        )
        ss.prog_base = _reg
        ss.pa_sa_cols = read_prog_aula(_B2(_reg))["sa_cols"]
        ss.pa_sa_edits = {}
    ss.pop("consist_issues", None)
    ss.pop("prog_out", None)
    ss.pop("pa_docx", None)


@st.dialog("Revisión de coherencia con las situaciones de aprendizaje", width="large")
def _dlg_coherencia(issues, contexto="carga"):
    ss = st.session_state
    _txt = {
        "carga": "Al cargar el Excel se ha revisado su contenido. La tabla de "
        "**situaciones de aprendizaje** manda (SA → CE → IL → actividades) y hay "
        "desajustes:",
        "guardar": "La tabla de **situaciones de aprendizaje** manda. Antes de "
        "guardar hay desajustes:",
        "generar": "La tabla de **situaciones de aprendizaje** manda. Antes de "
        "generar la programación hay desajustes:",
    }[contexto]
    st.write(_txt)
    for it in issues:
        st.warning(f"**{it['titulo']}**\n\n{it['detalle']}")
    _manual = [it for it in issues if not it.get("autofix")]
    if _manual:
        st.error(
            "Alguno no se puede arreglar solo (los criterios de evaluación tienen "
            "que estar bien). Corrígelo en el Excel y vuelve a subirlo."
        )

    _accion = "Regenerar en blanco lo que haga falta"
    if contexto == "guardar":
        _accion += " y guardar"
    elif contexto == "generar":
        _accion += " y generar"

    c1, c2 = st.columns(2)
    if c1.button("Parar — lo arreglo a mano en Excel", use_container_width=True, key="dlg_abort"):
        ss.consist_seen = True
        st.rerun()
    if c2.button(_accion, type="primary", use_container_width=True,
                 disabled=bool(_manual), key="dlg_regen"):
        try:
            _aplicar_regeneracion(issues)
            ss.consist_seen = True
            ss.prog_msg = ""
            if contexto in ("guardar", "generar"):
                _data = _guardar_todo()
                ss.prog_out = _data
                if contexto == "generar":
                    ss.pa_docx = _generar_docx(_data)
        except Exception as exc:
            ss.prog_msg = f"Error al regenerar: {exc}"
        st.rerun()


# ── Al cargar el Excel: si algo no cuadra con las situaciones de aprendizaje,
#    salta el aviso (una vez, hasta que se decida qué hacer).
if (
    prog_excel is not None
    and st.session_state.get("consist_issues")
    and not st.session_state.get("consist_seen")
):
    _dlg_coherencia(st.session_state.consist_issues, contexto="carga")

# ── Botón global "Guardar Excel" en la barra de arriba (todas las pestañas).
with dl_box:
    if prog_excel is not None:
        if st.button("Guardar Excel", type="primary", use_container_width=True, key="btn_save_all"):
            from tools.consistencia import revisar

            _iss = revisar(*_estado_coherencia())
            if _iss:
                _dlg_coherencia(_iss, contexto="guardar")
            else:
                try:
                    st.session_state.prog_out = _guardar_todo()
                    st.session_state.prog_msg = ""
                except Exception as exc:
                    st.session_state.prog_msg = f"Error al generar el Excel: {exc}"
                    st.session_state.pop("prog_out", None)
        if st.session_state.get("prog_msg"):
            st.caption(f"⚠️ {st.session_state.prog_msg}")
        if st.session_state.get("prog_out"):
            from tools.sellado import etiqueta_archivo

            _sello = st.session_state.get("prog_sello", "")
            _base = prog_excel.name.rsplit(".", 1)[0]
            _fname = f"{etiqueta_archivo(_sello)}_{_base}.xlsx" if _sello else f"{_base}_actualizado.xlsx"
            st.download_button(
                "Descargar .xlsx",
                data=st.session_state.prog_out,
                file_name=_fname,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="dlb_prog",
            )
            if _sello:
                st.caption(f"Guardado: {_sello}")

# PÁGINA: INICIO
if page == "Inicio":
    st.markdown('<div class="panel-card"><h3>Bienvenido</h3><p>Elige una sección arriba para empezar.</p></div>', unsafe_allow_html=True)

# PÁGINA: DISEÑO DE LA PROGRAMACIÓN
elif page == "Diseño de la programación":
    st.caption(
        "Edita las tablas curriculares del Excel de programación sin romper el libro. "
        "Carga y descarga el archivo en la barra de arriba."
    )

    COLS = SA_COLS

    if prog_excel is None:
        st.info("Sube el Excel de programación en la barra de arriba para empezar.")
    elif "sa_df" in st.session_state:
        from io import BytesIO

        from tools.indicadores_logro import save_indicadores
        from tools.situaciones_aprendizaje import (
            Situacion,
            acumulado_por_trimestre,
            save_situaciones,
        )
        from tools.situaciones_informe import (
            AGGRID_GRID_CSS,
            AGGRID_LINES_CSS,
            build_image_copy_html,
            build_pie_png,
            build_table_copy_html,
            hsa_share,
            zebra_styler,
        )

        # ───────────────── SECCIÓN: SITUACIONES DE APRENDIZAJE ─────────────────
        with _seccion("Situaciones de aprendizaje", 0, abierto=True):
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
            sc1, sc2, sc3, _sc = st.columns([1.3, 1.5, 1.2, 3])
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

        # ───────────────── SECCIÓN: CALCULADORA DE SESIONES ─────────────────
        _calc_sesiones_por_evaluacion()

        ce_list = st.session_state.il_ce_list
        ce_ced = st.session_state.il_ce_ced
        aux = st.session_state.il_aux
        sa_options = sorted({s.sa for s in sits if s.sa})

        # ───────────────── SECCIÓN: CRITERIOS DE EVALUACIÓN ─────────────────
        with _seccion("Criterios de evaluación", 2, abierto=True):
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
                )
                for r in rows
            ]

        from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

        st.session_state.setdefault("il_nonce", 0)

        def _parse_grid_row(r):
            return {
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

        with _seccion("Indicadores de logro", 3, abierto=True):
            st.markdown(
                '<div class="mini-label">CE se elige de la lista · CED e IL (4.2.1, 4.2.2…) '
                "son automáticos · PIL a mano, PIL% automático · SA solo entre las de arriba · "
                "pasa el ratón por CED/DIL para ver el texto completo · marca la casilla de la "
                "izquierda y pulsa <b>Borrar</b> · escribe y pulsa <b>Actualizar</b> para agrupar "
                "por criterio y renumerar (nada se pierde hasta entonces)</div>",
                unsafe_allow_html=True,
            )

            ac1, ac2, ac3, ac4, ac5 = st.columns([1.7, 0.8, 1.5, 1.6, 1.3])
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
                        "__shade": False,  # se calcula justo debajo
                    }
                    for r in st.session_state.il_rows
                ],
                columns=["X", "CE", "CED", "IL", "PIL", "PIL%", "DIL", "DO",
                         "CON", "CT", "IE", "CC", "AE", "SA", "__shade"],
            )
            _ce_seq = list(dict.fromkeys(r["CE"] for r in st.session_state.il_rows))
            _ce_shade = {ce: (i % 2 == 1) for i, ce in enumerate(_ce_seq)}
            il_df["__shade"] = il_df["CE"].map(lambda c: bool(_ce_shade.get(c)))
            il_df["X"] = il_df["X"].astype(bool)

            gb = GridOptionsBuilder.from_dataframe(il_df)
            gb.configure_default_column(editable=True, resizable=True, sortable=False, filter=False)
            gb.configure_column("__shade", hide=True)
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
            gb.configure_column("DO", width=180, tooltipField="DO")
            gb.configure_column("CON", width=130, tooltipField="CON")
            gb.configure_column("CT", width=80, tooltipField="CT")
            gb.configure_column("IE", width=140, cellEditor="agSelectCellEditor",
                                cellEditorParams={"values": _with_existing(aux.get("IE", []), "IE")})
            gb.configure_column("CC", width=130, cellEditor="agSelectCellEditor",
                                cellEditorParams={"values": _with_existing(aux.get("CC", []), "CC")})
            gb.configure_column("AE", width=70, cellEditor="agSelectCellEditor",
                                cellEditorParams={"values": _with_existing(aux.get("AE", []), "AE")})
            gb.configure_column("SA", width=62, cellEditor="agSelectCellEditor",
                                cellEditorParams={"values": [str(x) for x in sa_col_opts]})
            gb.configure_grid_options(
                enableBrowserTooltips=True,
                tooltipShowDelay=300,
                getRowStyle=JsCode(
                    "function(p){return (p.data && p.data.__shade) "
                    "? {'background-color':'#f6ead6'} : null}"
                ),
                rowHeight=30,
            )

            grid = AgGrid(
                il_df,
                gridOptions=gb.build(),
                update_on=[("cellValueChanged", 300)],
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=False,
                custom_css=AGGRID_LINES_CSS,
                height=430,
                theme="balham",
                key=f"il_grid_{st.session_state.il_nonce}",
            )

            # Lo que hay ahora mismo en la rejilla (en su orden actual, sin agrupar).
            grid_df = pd.DataFrame(grid["data"])
            if grid_df.empty or "CE" not in grid_df.columns:
                grid_df = il_df.copy()
            pending = [_parse_grid_row(r) for _, r in grid_df.iterrows()]
            # para consumidores externos (Elementos, Programación de aula) se guarda
            # ya recalculado: con IL/CED/PIL% rellenos.
            st.session_state.il_pending = il_recompute(pending, ce_ced, ce_list)

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
                            "CE": add_ce, "CED": "", "IL": "", "PIL": 1,
                            "DIL": "", "DO": "", "CON": "", "CT": "",
                            "IE": "", "CC": "", "AE": "", "SA": None,
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
                    il_errores.append(f"Fila {i}: el criterio {r['CE']} no existe en la tabla de criterios.")
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

        # ─── SECCIÓN: AJUSTE DE PESOS ───
        with _seccion("Ajuste de pesos (objetivo por instrumento + reparto horario)", 4):
            _ajuste_pesos_ipf(
                il_recompute(pending, ce_ced, ce_list), ce_list, ce_ced, ce_p, sits
            )

        # ─────── SECCIÓN: DISTRIBUCIÓN DE PORCENTAJES POR CE Y SA ───────
        with _seccion(
            "Distribución de porcentajes por criterios de evaluación y "
            "situaciones de aprendizaje", 5, abierto=True,
        ):
            from st_aggrid import AgGrid, ColumnsAutoSizeMode, GridOptionsBuilder
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
                    minWidth=64, cellStyle={"textAlign": "center"},
                )
                _gb.configure_column("Título", hide=True)
                _gb.configure_column("SA", pinned="left", width=56, tooltipField="Título",
                                     cellStyle={"fontWeight": "600", "textAlign": "center"})
                _gb.configure_column("Total (IL)", pinned="right", width=92,
                                     cellStyle={"fontWeight": "600", "textAlign": "center"})
                _gb.configure_column("% SA (horas)", pinned="right", width=104,
                                     cellStyle={"fontWeight": "600", "textAlign": "center"})
                _gb.configure_grid_options(
                    enableBrowserTooltips=True, tooltipShowDelay=300, rowHeight=28,
                    suppressColumnVirtualisation=True,
                )
                AgGrid(
                    _mx_df, gridOptions=_gb.build(), allow_unsafe_jscode=True,
                    fit_columns_on_grid_load=False,
                    columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
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

        # ─────── SECCIÓN: PESO FINAL POR INSTRUMENTO DE EVALUACIÓN ───────
        with _seccion("Peso final por instrumento de evaluación", 6):
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
                st.dataframe(
                    pd.DataFrame(_ie_rows, columns=_ie_headers),
                    use_container_width=True, hide_index=True,
                )
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
        "<p>Contenidos de la materia y contenidos transversales (hoja "
        "<code>LOMLOE</code>). Se marca en verde cada elemento que ya está "
        "asignado a algún indicador de logro (en su columna CON o CT), igual que "
        "el aviso de la hoja de Excel.</p></div>",
        unsafe_allow_html=True,
    )

    if prog_excel is None or "elementos" not in st.session_state:
        st.info("Sube el Excel de programación en la barra de arriba.")
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
                rows.append({"__ok": ok, "●": "🟢" if ok else "🔴",
                             header_cod: cod, "Descripción": it[label_field]})
            n_ok = sum(1 for r in rows if r["__ok"])
            st.caption(f"🟢 {n_ok} asignados · 🔴 {len(rows) - n_ok} sin asignar · {len(rows)} en total")
            if _solo_falta:
                rows = [r for r in rows if not r["__ok"]]
            if not rows:
                st.success("Todos asignados.")
                return
            df = pd.DataFrame(rows, columns=["__ok", "●", header_cod, "Descripción"])
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_default_column(editable=False, resizable=True, sortable=True, filter=False)
            gb.configure_column("__ok", hide=True)
            gb.configure_column("●", headerName="", width=46, pinned="left",
                                cellStyle={"textAlign": "center"})
            gb.configure_column(header_cod, width=88, pinned="left")
            gb.configure_column("Descripción", flex=1, minWidth=280, tooltipField="Descripción")
            gb.configure_grid_options(enableBrowserTooltips=True, tooltipShowDelay=300,
                                      rowHeight=28, getRowStyle=_rowstyle)
            AgGrid(df, gridOptions=gb.build(), allow_unsafe_jscode=True,
                   fit_columns_on_grid_load=False, custom_css=AGGRID_GRID_CSS,
                   height=min(460, 44 + 28 * len(df)), theme="balham",
                   update_on=[], key=grid_key)

        if _seccion_simple("Contenidos de la materia", "con_mat", abierto=True):
            _render(_el["contenidos"], "cod", "desc", "Código", _con_used, "ec_grid_con")

        if _seccion_simple("Contenidos transversales", "con_tr", abierto=True):
            _render(_el["transversales"], "num", "desc", "Nº", _ct_used, "ec_grid_ct")

# PÁGINA: PROGRAMACIÓN DE AULA
elif page == "Programación de aula":
    st.markdown(
        '<div class="panel-card"><h3>Programación de aula</h3>'
        "<p>Datos generales del grupo, actividades por situación de aprendizaje y "
        "campos de la programación de aula. Genera el documento Word con la "
        "plantilla por defecto o con una tuya.</p></div>",
        unsafe_allow_html=True,
    )

    if prog_excel is None:
        st.info("Sube el Excel de programación en la barra de arriba para empezar.")
    else:
        from io import BytesIO

        from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
        from tools.programacion_aula_editor import recompute_actividades, valores_actividades
        from tools.programacion_aula_editor import read_prog_aula
        from tools.situaciones_informe import (
            AGGRID_GRID_CSS,
            build_html_table_copy_html,
            render_word_table_html,
        )

        ss = st.session_state
        if "pa_datos" not in ss:
            _pa = read_prog_aula(prog_excel)
            ss.pa_datos = dict(_pa["datos"])
            ss.pa_campos_datos = [k for k, _ in _pa["datos"]]
            ss.pa_sa_campos = _pa["sa_campos"]
            ss.pa_sa_cols = _pa["sa_cols"]
            ss.pa_acts = _pa["actividades"]
            ss.pa_sa_edits = {}
        ss.setdefault("pa_nonce", 0)

        # Indicadores de logro ya recalculados (IL/SA/PIL rellenos). Se toma el
        # estado canónico (il_rows); si hay edición reciente en Diseño con IL
        # válidos, esa.
        _il_state = ss.get("il_rows") or []
        _ilp = ss.get("il_pending")
        if _ilp and all(r.get("IL") for r in _ilp):
            _il_state = _ilp
        _il_sa = {r["IL"]: r["SA"] for r in _il_state}
        _pil_por_il = {r["IL"]: float(r["PIL"] or 0) for r in _il_state}
        _ce_p = {r["CE"]: r["P"] for r in ss.get("ce_rows", [])} or dict(ss.get("il_ce_p", {}))

        _src = ss.get("sa_grid_rows")
        if _src:
            _sa_opts = [(r["SA"], r["DSA"]) for r in _src if r["SA"] is not None]
        else:
            _sa_opts = [
                (int(v[0]), str(v[2] or ""))
                for v in ss.sa_df.itertuples(index=False) if not pd.isna(v[0])
            ]

        def _hum(k):
            return k.replace("_", " ").strip().capitalize()

        # ── Generar programación de aula
        gc1, gc2 = st.columns([2.2, 1.6])
        _tpl = gc1.file_uploader("Plantilla Word (opcional)", type=["docx"], key="pa_tpl")
        if gc2.button("Generar programación de aula", use_container_width=True, type="primary", key="pa_gen"):
            from tools.consistencia import revisar

            _iss = revisar(*_estado_coherencia())
            if _iss:
                _dlg_coherencia(_iss, contexto="generar")
            else:
                try:
                    _upd = _guardar_todo()
                    ss.pa_docx = _generar_docx(_upd)
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

        # ── SECCIÓN: Datos generales
        _LARGOS = {
            "alumnos_atencion_individualizada", "caracteristicas_fisicas_cognitivas_afectivas",
            "nivel_competencia_curricular", "otras_caracteristicas_grupo",
            "resultados_evaluacion_inicial", "conclusiones_evaluacion_inicial",
            "resultados_evaluacion_aprendizajes", "revision_programacion",
        }
        if _seccion_simple("Datos generales", "pa_datos", abierto=True):
            _cortos = [k for k in ss.pa_campos_datos if k not in _LARGOS]
            _cc = st.columns(2)
            for i, k in enumerate(_cortos):
                ss.pa_datos[k] = _cc[i % 2].text_input(_hum(k), value=ss.pa_datos.get(k, ""), key=f"pad_{k}")
            for k in ss.pa_campos_datos:
                if k in _LARGOS:
                    ss.pa_datos[k] = st.text_area(_hum(k), value=ss.pa_datos.get(k, ""), key=f"pad_{k}", height=90)

        # ── SECCIÓN: Actividades por situación de aprendizaje
        if _seccion_simple("Diseño de actividades por situación de aprendizaje", "pa_act", abierto=True):
            _lbl = {sa: f"{sa}: {d}" for sa, d in _sa_opts}
            sa_sel = st.selectbox(
                "Situación de aprendizaje", [sa for sa, _ in _sa_opts],
                format_func=lambda s: _lbl.get(s, str(s)), key="pa_sa_sel",
            )
            _ils_sa = [r["IL"] for r in _il_state if r["SA"] == sa_sel]

            _acts_sa = [a for a in ss.pa_acts if a.get("IL") in _ils_sa]
            _acts_otras = [a for a in ss.pa_acts if a.get("IL") not in _ils_sa]

            # Cada IL de la SA debe tener al menos una fila: si no hay ninguna
            # actividad para ese IL, se muestra una en blanco para rellenar
            # (peso vacío = fila de plantilla que no se guarda hasta tocarla).
            _con_act = {a["IL"] for a in _acts_sa}
            _acts_sa_disp = _acts_sa + [
                {"IL": il, "A": "", "DA": "", "PA": None}
                for il in _ils_sa if il not in _con_act
            ]

            st.markdown(
                f'<div class="mini-label">Actividades de los IL de esta SA '
                f"({', '.join(_ils_sa) or '—'}) · cada IL trae al menos una fila para rellenar "
                "· A (código) y PA%/FACTOR se recalculan al pulsar Actualizar</div>",
                unsafe_allow_html=True,
            )
            pc1, pc2, pc3, pc4 = st.columns([1.4, 1.3, 1.2, 3])
            _add_il = pc1.selectbox("IL", _ils_sa or ["—"], key="pa_add_il", label_visibility="collapsed")
            _pa_add = pc2.button("Añadir actividad", use_container_width=True, key="pa_add")
            _pa_del = pc3.button("Borrar marcadas", use_container_width=True, key="pa_del")
            _pa_upd = pc4.button("Actualizar", use_container_width=True, type="primary", key="pa_upd")

            _rc = recompute_actividades(_acts_sa_disp, _pil_por_il)
            _adf = pd.DataFrame(
                [
                    {"X": False, "IL": r["IL"], "A": r["A"], "DA": r["DA"],
                     "PA": r["PA"],
                     "PA%": None if r["PA%"] is None else r["PA%"] * 100,
                     "FACTOR": r["FACTOR"]}
                    for r in _rc
                ],
                columns=["X", "IL", "A", "DA", "PA", "PA%", "FACTOR"],
            )
            _adf["X"] = _adf["X"].astype(bool)
            _agb = GridOptionsBuilder.from_dataframe(_adf)
            _agb.configure_default_column(editable=True, resizable=True, sortable=False, filter=False)
            _agb.configure_column("X", headerName="", width=44, pinned="left",
                                  cellRenderer="agCheckboxCellRenderer",
                                  cellEditor="agCheckboxCellEditor", cellDataType="boolean")
            _agb.configure_column("IL", width=84, cellDataType="text", cellEditor="agSelectCellEditor",
                                  cellEditorParams={"values": _ils_sa})
            _agb.configure_column("A", editable=False, width=96)
            _agb.configure_column("DA", headerName="Descripción", flex=1, minWidth=240,
                                  cellDataType="text", tooltipField="DA")
            _agb.configure_column("PA", headerName="Peso", width=80, cellDataType="number", type=["numericColumn"])
            _agb.configure_column("PA%", editable=False, width=84,
                                  valueFormatter=JsCode("function(p){return p.value==null?'':Number(p.value).toFixed(1)+' %'}"))
            _agb.configure_column("FACTOR", editable=False, width=90,
                                  valueFormatter=JsCode("function(p){return p.value==null?'':Number(p.value).toFixed(3)}"))
            _agb.configure_grid_options(enableBrowserTooltips=True, rowHeight=30)
            _agrid = AgGrid(
                _adf, gridOptions=_agb.build(), update_on=[("cellValueChanged", 300)],
                allow_unsafe_jscode=True, fit_columns_on_grid_load=False,
                custom_css=AGGRID_GRID_CSS,
                height=max(190, min(430, 95 + 33 * max(len(_adf), 1))),
                theme="balham", key=f"pa_acts_grid_{sa_sel}_{ss.pa_nonce}",
            )
            _ag = pd.DataFrame(_agrid["data"])
            if _ag.empty or "IL" not in _ag.columns:
                _ag = _adf.copy()
            _pend = [
                {
                    "IL": "" if pd.isna(r.get("IL")) else str(r.get("IL")),
                    "A": "" if pd.isna(r.get("A")) else str(r.get("A")),
                    "DA": "" if pd.isna(r.get("DA")) else str(r.get("DA")),
                    "PA": None if r.get("PA") in (None, "") or pd.isna(r.get("PA")) else float(r.get("PA")),
                }
                for _, r in _ag.iterrows()
            ]
            _delf = [str(r.get("X")).strip().lower() in ("true", "1", "yes") for _, r in _ag.iterrows()]

            def _real(r):
                return bool(str(r.get("DA") or "").strip()) or r.get("PA") not in (None, "", 0)

            def _fold(pend):
                return _acts_otras + [
                    {"IL": p["IL"], "DA": p["DA"], "PA": p["PA"], "A": ""}
                    for p in pend if str(p.get("IL") or "").strip() and _real(p)
                ]

            def _sig(rows):
                return [(a.get("IL"), a.get("DA"), a.get("PA")) for a in rows]

            def _commit_acts(nuevas_sa):
                ss.pa_acts = _fold(nuevas_sa)
                ss.pa_nonce += 1
                ss.pop("prog_out", None)
                ss.pop("pa_docx", None)
                st.rerun()

            if _pa_add and _ils_sa:
                _commit_acts(_pend + [{"IL": _add_il, "A": "", "DA": "", "PA": 1}])
            elif _pa_del and any(_delf):
                _commit_acts([p for p, d in zip(_pend, _delf) if not d])
            elif _pa_upd:
                _commit_acts(_pend)
            else:
                # Guarda en vivo lo que se va escribiendo (sin remontar la rejilla).
                _folded = _fold(_pend)
                if _sig(_folded) != _sig(ss.pa_acts):
                    ss.pa_acts = _folded
                    ss.pop("prog_out", None)
                    ss.pop("pa_docx", None)

            # Campos de la programación de aula para esta SA. Se emparejan por
            # título; una SA nueva sin columna se edita igual (la columna se crea
            # al guardar). Las ediciones se guardan por título de SA.
            import re as _re

            _dsa_sel = next((d for n, d in _sa_opts if n == sa_sel), "")
            _norm = lambda s: _re.sub(r"\s+", " ", str(s or "")).strip().lower()
            _base = {}
            for _e in ss.pa_sa_cols:
                if _norm(_e.get("valores", {}).get("titulo")) == _norm(_dsa_sel):
                    _base = _e["valores"]
                    break
            _nueva = not _base
            _tri_sel = next((t for n, _d, t in _sa_datos() if n == sa_sel), "")
            st.markdown("**Campos de la programación de aula para esta SA**")
            if _nueva:
                st.caption("Situación nueva: su columna en P_Aula_SA se creará al guardar.")
            _cur = ss.pa_sa_edits.get(_dsa_sel, dict(_base))
            # titulo y trimestre son automáticos (de la tabla de situaciones)
            _cur["titulo"] = _dsa_sel
            _cur["trimestre"] = _tri_sel
            _cc = st.columns(2)
            _cc[0].text_input("Título", value=_dsa_sel, disabled=True, key=f"pasa_tit_{sa_sel}")
            _cc[1].text_input("Trimestre", value=_tri_sel or "—", disabled=True, key=f"pasa_tri_{sa_sel}")
            st.caption("Título y trimestre se toman de la tabla de situaciones de aprendizaje.")
            for campo in ss.pa_sa_campos:
                if campo in ("titulo", "trimestre"):
                    continue
                _cur[campo] = st.text_area(
                    _hum(campo), value=_cur.get(campo, ""),
                    key=f"pasa_{sa_sel}_{campo}", height=70,
                )
            ss.pa_sa_edits[_dsa_sel] = _cur

            # ── Resumen de actividades de esta SA (dinámica de INFORMES)
            st.divider()
            st.markdown(
                '<div class="mini-label">Resumen de actividades de esta situación de '
                "aprendizaje (valor de cada actividad sobre la programación y sobre la SA)</div>",
                unsafe_allow_html=True,
            )
            _val = valores_actividades(ss.pa_acts, _il_state, _ce_p)
            _val_sa = [a for a in _val if a.get("SA") == sa_sel]
            _rheaders = ["A", "Descripción", "Valor s/ programación", "Valor s/ SA"]
            _rrows = [
                [
                    a["A"], a["DA"],
                    f"{a['valor_prog'] * 100:.2f}".replace(".", ",") + " %",
                    f"{a['valor_sa'] * 100:.2f}".replace(".", ",") + " %",
                ]
                for a in _val_sa
            ]
            if _rrows:
                st.dataframe(pd.DataFrame(_rrows, columns=_rheaders),
                            use_container_width=True, hide_index=True)
                components.html(
                    build_html_table_copy_html(
                        render_word_table_html(_rheaders, _rrows),
                        btn_id="pa-res-copy", fn="paResCopy", label="Copiar tabla (Word)",
                    ),
                    height=40,
                )
            else:
                st.caption("Aún no hay actividades para esta situación de aprendizaje.")
