from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))


st.set_page_config(page_title="IES Manager", page_icon="🗂️", layout="wide")

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
        "Desde `IES_Manager`, ejecútala con su propio venv:\n\n"
        "```\n.\\.venv\\Scripts\\python.exe -m streamlit run app.py --server.port 8502\n```\n\n"
        "o directamente `.\\run_app.bat`. Si falta el venv: "
        "`python -m venv .venv ; .venv\\Scripts\\python.exe -m pip install -r requirements.txt`."
    )
    st.stop()

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
    .panel-card {
        background: #ffffff;
        border: 1px solid #e7e2f2;
        color: #333333;
    }
    /* Cabecera de bloque dentro de una pestaña con varios apartados apilados. */
    .block-head {
        font-size: 1.12rem;
        font-weight: 700;
        color: #ffffff;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0.5rem 0.9rem;
        border-radius: 10px;
        margin: 1.6rem 0 0.7rem 0;
        box-shadow: 0 3px 10px rgba(102,126,234,0.25);
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
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }
    .mini-label {
        font-size: 0.8rem;
        font-weight: 600;
        opacity: 0.75;
        margin-bottom: 0.2rem;
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
PAGES = ["Inicio", "Diseño de la programación", "LOMLOE", "Actividades", "Programación de aula"]
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
from tools.indicadores_logro import read_indicadores
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
        st.session_state.prog_loaded_name = prog_excel.name
        st.session_state.pop("prog_out", None)
    except Exception as exc:
        st.error(f"No se ha podido leer el Excel: {exc}")

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
                            "SA": r["SA"], "EV": r["EV"], "DSA": r["DSA"],
                            "HSA": r["HSA"], "% horas": r["PCT"],
                        }
                        for r in st.session_state.sa_grid_rows
                    ],
                    columns=["X", "SA", "EV", "DSA", "HSA", "% horas"],
                )
                _sa_df["X"] = _sa_df["X"].astype(bool)
                _gb = GridOptionsBuilder.from_dataframe(_sa_df)
                _gb.configure_default_column(editable=True, resizable=True, sortable=False, filter=False)
                _gb.configure_column("X", headerName="", editable=True, width=44, pinned="left",
                                     cellRenderer="agCheckboxCellRenderer",
                                     cellEditor="agCheckboxCellEditor", cellDataType="boolean")
                _gb.configure_column("SA", headerName="SA (nº)", width=82, type=["numericColumn"])
                _gb.configure_column("EV", headerName="EV (trim.)", width=96,
                                     cellEditor="agSelectCellEditor",
                                     cellEditorParams={"values": [str(t) for t in TRIMESTRES]})
                _gb.configure_column("DSA", headerName="Descripción", flex=1, minWidth=220, tooltipField="DSA")
                _gb.configure_column("HSA", headerName="Horas", width=82, type=["numericColumn"])
                _gb.configure_column(
                    "% horas", editable=False, width=94,
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

        # ───────────────── BLOQUE: INDICADORES DE LOGRO ─────────────────
        st.markdown('<div class="block-head">Indicadores de logro</div>', unsafe_allow_html=True)

        ce_list = st.session_state.il_ce_list
        ce_ced = st.session_state.il_ce_ced
        ce_p = st.session_state.get("il_ce_p", {})
        aux = st.session_state.il_aux
        sa_options = sorted({s.sa for s in sits if s.sa})

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
                    "? {'background-color':'#ece6f9'} : null}"
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

        # ───────────────── DESCARGA GLOBAL (barra de arriba) ─────────────────
        with dl_box:
            if st.button("Guardar Excel", type="primary", use_container_width=True, key="btn_save_all"):
                probs = errores + il_errores
                if probs:
                    st.session_state.prog_msg = "Corrige los avisos antes de guardar."
                    st.session_state.pop("prog_out", None)
                else:
                    try:
                        _data = save_situaciones(prog_excel, sits, previstas)
                        _il = il_recompute(
                            st.session_state.get("il_pending", st.session_state.il_rows),
                            ce_ced, ce_list,
                        )
                        _data = save_indicadores(BytesIO(_data), _il, ce_ced, ce_list)
                        st.session_state.prog_out = _data
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

# PÁGINA: LOMLOE
elif page == "LOMLOE":
    st.markdown(
        '<div class="panel-card"><h3>LOMLOE</h3>'
        "<p>Consulta y edición de los elementos curriculares LOMLOE de la hoja "
        "<code>LOMLOE</code> del Excel. En construcción.</p></div>",
        unsafe_allow_html=True,
    )

# PÁGINA: ACTIVIDADES
elif page == "Actividades":
    st.markdown(
        '<div class="panel-card"><h3>Actividades</h3>'
        "<p>Editor de la tabla <code>TablaActividades</code> (actividades por "
        "situación de aprendizaje y su peso). En construcción.</p></div>",
        unsafe_allow_html=True,
    )

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
