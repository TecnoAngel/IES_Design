from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))


def _favicon():
    """Escudo (corona + blasón) de la Junta como icono de pestaña."""
    fav = ROOT / "logo_favicon.png"
    if fav.exists():
        return str(fav)
    logo = ROOT / "logo_junta.jpg"
    if not logo.exists():
        return "🗂️"
    try:
        from PIL import Image, ImageDraw

        e = Image.open(logo).convert("RGBA").crop((50, 8, 178, 212))
        w, h = e.size
        seeds = [(x, 0) for x in range(0, w, 6)] + [(x, h - 1) for x in range(0, w, 6)]
        seeds += [(0, y) for y in range(0, h, 6)] + [(w - 1, y) for y in range(0, h, 6)]
        for s in seeds:
            try:
                ImageDraw.floodfill(e, s, (255, 255, 255, 0), thresh=42)
            except Exception:
                pass
        e = e.crop(e.getbbox())
        side = max(e.size) + 8
        square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        square.paste(e, ((side - e.width) // 2, (side - e.height) // 2), e)
        return square.resize((128, 128), Image.LANCZOS)
    except Exception:
        return "🗂️"


st.set_page_config(page_title="IES Diseño", page_icon=_favicon(), layout="wide")

if (ROOT / "logo_junta.jpg").exists():
    try:
        st.logo(str(ROOT / "logo_junta.jpg"))
    except Exception:
        pass

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
    /* Paleta Junta de Castilla y León (del logo): rojo carmín + oro. */
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
        <div class="topbar-sub">Diseño y revisión de la programación sobre tu propio Excel.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("")

# st.tabs no conserva la pestaña activa entre reruns (cada clic en un botón
# devuelve la vista a la primera pestaña), así que la navegación se hace con
# un widget normal atado a session_state para que sea persistente.
PAGES = ["Inicio", "Diseño de la programación", "Elementos curriculares", "Programación de aula"]
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
    dl_box = ubar2.container()

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
        # al cambiar de archivo, se descartan los estados canónicos derivados
        for _k in (
            "prog_out", "sa_grid_rows", "ce_rows", "il_pending",
            "pa_datos", "pa_sa_edits", "pa_acts", "pa_docx",
        ):
            st.session_state.pop(_k, None)
    except Exception as exc:
        st.error(f"No se ha podido leer el Excel: {exc}")


def _guardar_todo() -> bytes:
    """Aplica sobre el Excel subido todos los cambios en sesión (situaciones,
    criterios, indicadores y programación de aula) y devuelve los bytes."""
    from io import BytesIO as _B

    from tools.indicadores_logro import save_criterios, save_indicadores
    from tools.situaciones_aprendizaje import Situacion, save_situaciones

    ss = st.session_state
    data = prog_excel.getvalue()

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
        from tools.programacion_aula_editor import (
            save_actividades,
            save_datos_generales,
            save_p_aula_sa,
        )

        data = save_datos_generales(_B(data), dict(ss.pa_datos))
        for _col, _vals in ss.get("pa_sa_edits", {}).items():
            data = save_p_aula_sa(_B(data), _col, _vals)
        _pil = {r["IL"]: float(r["PIL"] or 0) for r in il_g}
        data = save_actividades(_B(data), ss.get("pa_acts", []), _pil)

    return data


# ── Botón global "Guardar Excel" en la barra de arriba (todas las pestañas).
with dl_box:
    if prog_excel is not None:
        if st.button("Guardar Excel", type="primary", use_container_width=True, key="btn_save_all"):
            try:
                st.session_state.prog_out = _guardar_todo()
                st.session_state.prog_msg = ""
            except Exception as exc:
                st.session_state.prog_msg = f"Error al generar el Excel: {exc}"
                st.session_state.pop("prog_out", None)
        if st.session_state.get("prog_msg"):
            st.caption(f"⚠️ {st.session_state.prog_msg}")
        if st.session_state.get("prog_out"):
            st.download_button(
                "Descargar .xlsx",
                data=st.session_state.prog_out,
                file_name=prog_excel.name.rsplit(".", 1)[0] + "_actualizado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="dlb_prog",
            )

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

        # ───────────────── BLOQUE: SITUACIONES DE APRENDIZAJE ─────────────────
        st.markdown('<div class="block-head">Situaciones de aprendizaje</div>', unsafe_allow_html=True)

        with st.container(border=True):
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

        ce_list = st.session_state.il_ce_list
        ce_ced = st.session_state.il_ce_ced
        aux = st.session_state.il_aux
        sa_options = sorted({s.sa for s in sits if s.sa})

        # ───────────────── BLOQUE: CRITERIOS DE EVALUACIÓN ─────────────────
        st.markdown('<div class="block-head">Criterios de evaluación</div>', unsafe_allow_html=True)

        with st.container(border=True):
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

        # ───────────────── BLOQUE: INDICADORES DE LOGRO ─────────────────
        st.markdown('<div class="block-head">Indicadores de logro</div>', unsafe_allow_html=True)

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

        with st.container(border=True):
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
            st.session_state.il_pending = pending

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
            with st.expander("Ver resumen por criterio", expanded=False):
                st.dataframe(
                    zebra_styler(pd.DataFrame(_res_rows, columns=_res_headers)),
                    use_container_width=True,
                    hide_index=True,
                )

        # ─────── BLOQUE: DISTRIBUCIÓN DE PORCENTAJES POR CE Y SA ───────
        st.markdown(
            '<div class="block-head">Distribución de porcentajes por criterios de '
            "evaluación y situaciones de aprendizaje</div>",
            unsafe_allow_html=True,
        )
        with st.container(border=True):
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

# PÁGINA: ELEMENTOS CURRICULARES
elif page == "Elementos curriculares":
    st.markdown(
        '<div class="panel-card"><h3>Elementos curriculares</h3>'
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

        st.markdown('<div class="block-head">Contenidos de la materia</div>', unsafe_allow_html=True)
        with st.container(border=True):
            _render(_el["contenidos"], "cod", "desc", "Código", _con_used, "ec_grid_con")

        st.markdown('<div class="block-head">Contenidos transversales</div>', unsafe_allow_html=True)
        with st.container(border=True):
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
        from tools.programacion_aula import run_programacion_aula
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

        _il_state = ss.get("il_pending") or ss.get("il_rows") or []
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
            try:
                _upd = _guardar_todo()
                ss.pa_docx = run_programacion_aula(BytesIO(_upd), _tpl)
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

        # ── BLOQUE: Datos generales
        st.markdown('<div class="block-head">Datos generales</div>', unsafe_allow_html=True)
        _LARGOS = {
            "alumnos_atencion_individualizada", "caracteristicas_fisicas_cognitivas_afectivas",
            "nivel_competencia_curricular", "otras_caracteristicas_grupo",
            "resultados_evaluacion_inicial", "conclusiones_evaluacion_inicial",
            "resultados_evaluacion_aprendizajes", "revision_programacion",
        }
        with st.container(border=True):
            _cortos = [k for k in ss.pa_campos_datos if k not in _LARGOS]
            _cc = st.columns(2)
            for i, k in enumerate(_cortos):
                ss.pa_datos[k] = _cc[i % 2].text_input(_hum(k), value=ss.pa_datos.get(k, ""), key=f"pad_{k}")
            for k in ss.pa_campos_datos:
                if k in _LARGOS:
                    ss.pa_datos[k] = st.text_area(_hum(k), value=ss.pa_datos.get(k, ""), key=f"pad_{k}", height=90)

        # ── BLOQUE: Actividades por situación de aprendizaje
        st.markdown(
            '<div class="block-head">Diseño de actividades por situación de aprendizaje</div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
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
                     "PA": r["PA"], "PA%": r["PA%"] * 100, "FACTOR": r["FACTOR"]}
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
                custom_css=AGGRID_GRID_CSS, height=min(360, 42 + 30 * max(len(_adf), 1)),
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

            # Campos de la programación de aula para esta SA (columna de P_Aula_SA)
            _col = None
            if 1 <= sa_sel <= len(ss.pa_sa_cols):
                _entry = ss.pa_sa_cols[sa_sel - 1]
                _col = _entry["col"]
                _base = _entry["valores"]
            if _col:
                st.markdown("**Campos de la programación de aula para esta SA**")
                _cur = ss.pa_sa_edits.get(_col, dict(_base))
                for campo in ss.pa_sa_campos:
                    _cur[campo] = st.text_area(
                        _hum(campo), value=_cur.get(campo, ""),
                        key=f"pasa_{_col}_{campo}", height=70,
                    )
                ss.pa_sa_edits[_col] = _cur
            else:
                st.caption("Esta SA no tiene columna en la tabla P_Aula_SA del Excel.")

        # ── BLOQUE: Resumen de actividades por SA (tabla dinámica de INFORMES)
        st.markdown(
            '<div class="block-head">Resumen de actividades por situación de aprendizaje</div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
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
