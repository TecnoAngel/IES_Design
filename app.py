from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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
            build_image_copy_html,
            build_pie_png,
            build_table_copy_html,
            hsa_share,
        )

        # ───────────────── BLOQUE: SITUACIONES DE APRENDIZAJE ─────────────────
        st.markdown('<div class="block-head">Situaciones de aprendizaje</div>', unsafe_allow_html=True)

        with st.container(border=True):
            # Contenedor reservado arriba del bloque: la calculadora de horas se
            # rellena luego, cuando ya conocemos los datos editados.
            calc_box = st.container()
            st.divider()

            col_edit, col_pct, col_pie = st.columns([3, 1.1, 2.3], gap="small")

            with col_edit:
                st.markdown('<div class="mini-label">Situaciones (editable)</div>', unsafe_allow_html=True)
                edited = st.data_editor(
                    st.session_state.sa_df,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="sa_editor",
                    column_config={
                        "SA": st.column_config.NumberColumn("SA (nº)", min_value=1, step=1, format="%d"),
                        "EV": st.column_config.SelectboxColumn("EV (trim.)", options=list(TRIMESTRES)),
                        "DSA": st.column_config.TextColumn("Descripción", width="large"),
                        "HSA": st.column_config.NumberColumn("Horas", min_value=0, step=1, format="%d"),
                    },
                )

            filas = [r for _, r in edited.iterrows() if not r[COLS].isna().all()]
            sits = [
                Situacion(
                    sa=None if pd.isna(r["SA"]) else int(r["SA"]),
                    ev=None if pd.isna(r["EV"]) else int(r["EV"]),
                    dsa=str(r["DSA"] or ""),
                    hsa=None if pd.isna(r["HSA"]) else float(r["HSA"]),
                )
                for r in filas
            ]
            shares = hsa_share(sits)
            pie_png = build_pie_png(shares)
            total_h = sum(float(s.hsa) for s in sits if s.hsa)

            with col_pct:
                st.markdown('<div class="mini-label">% horas s/ total</div>', unsafe_allow_html=True)
                st.dataframe(
                    pd.DataFrame(
                        {
                            "SA": [s.sa for s in sits],
                            "%": [
                                (100 * float(s.hsa) / total_h) if (s.hsa and total_h) else 0.0
                                for s in sits
                            ],
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "SA": st.column_config.NumberColumn(format="%d", width="small"),
                        "%": st.column_config.NumberColumn(format="%.1f%%", width="small"),
                    },
                )

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
                            "Descargar PNG",
                            data=pie_png,
                            file_name="reparto_horas_SA.png",
                            mime="image/png",
                            use_container_width=True,
                        )
                else:
                    st.caption("Añade situaciones con horas para ver el gráfico.")

            # Validaciones
            errores = []
            for i, r in enumerate(filas, start=1):
                if pd.isna(r["SA"]):
                    errores.append(f"Fila {i}: falta el nº de situación (SA).")
                if not str(r["DSA"] or "").strip():
                    errores.append(f"Fila {i}: falta la descripción (DSA).")
                if pd.isna(r["HSA"]) or float(r["HSA"] or 0) < 0:
                    errores.append(f"Fila {i}: las horas (HSA) deben ser un número ≥ 0.")
                if pd.isna(r["EV"]) or int(r["EV"] or 0) not in TRIMESTRES:
                    errores.append(f"Fila {i}: la evaluación (EV) debe ser 1, 2 o 3.")
            sa_nums = [int(r["SA"]) for r in filas if not pd.isna(r["SA"])]
            duplicados = sorted({n for n in sa_nums if sa_nums.count(n) > 1})
            if duplicados:
                errores.append(f"Hay números de situación repetidos: {duplicados}.")

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
                "escribe libremente y pulsa <b>Actualizar</b> para agrupar por criterio y "
                "renumerar (los cambios no se pierden hasta entonces)</div>",
                unsafe_allow_html=True,
            )

            ac1, ac2, ac3, ac4, ac5 = st.columns([1.7, 0.8, 1.5, 1.6, 1.3])
            add_ce = ac1.selectbox("Criterio", ce_list, key="il_add_ce", label_visibility="collapsed")
            add_n = ac2.number_input("nº", 1, 20, 1, key="il_add_n", label_visibility="collapsed")
            add_click = ac3.button("Añadir al criterio", use_container_width=True)
            del_click = ac4.button("Borrar seleccionadas", use_container_width=True)
            upd_click = ac5.button("Actualizar", use_container_width=True, type="primary")

            il_df = pd.DataFrame(
                [
                    {
                        "__id": i,
                        "__shade": False,  # se calcula justo debajo
                        "CE": r["CE"], "IL": r["IL"],
                        "PIL": r["PIL"], "PIL%": r["PIL%"] * 100,
                        "DIL": r["DIL"], "DO": r["DO"], "CON": r["CON"], "CT": r["CT"],
                        "IE": r["IE"], "CC": r["CC"], "AE": r["AE"],
                        "SA": "" if r["SA"] in (None, "") else str(r["SA"]),
                        "CED": r["CED"],
                    }
                    for i, r in enumerate(st.session_state.il_rows)
                ],
                columns=["__id", "__shade", "CE", "IL", "PIL", "PIL%", "DIL", "DO",
                         "CON", "CT", "IE", "CC", "AE", "SA", "CED"],
            )
            _ce_seq = list(dict.fromkeys(r["CE"] for r in st.session_state.il_rows))
            _ce_shade = {ce: (i % 2 == 1) for i, ce in enumerate(_ce_seq)}
            il_df["__shade"] = il_df["CE"].map(lambda c: bool(_ce_shade.get(c)))

            _sel_editor = {"values": ce_col_opts}
            gb = GridOptionsBuilder.from_dataframe(il_df)
            gb.configure_default_column(editable=True, resizable=True, sortable=False, filter=False)
            gb.configure_column("__id", hide=True)
            gb.configure_column("__shade", hide=True)
            gb.configure_column("CE", width=80, cellEditor="agSelectCellEditor", cellEditorParams=_sel_editor)
            gb.configure_column("IL", editable=False, width=80)
            gb.configure_column(
                "PIL", width=80, type=["numericColumn"],
                valueFormatter=JsCode(
                    "function(p){return p.value===''||p.value==null?'':Number(p.value).toFixed(2)}"
                ),
            )
            gb.configure_column(
                "PIL%", editable=False, width=90,
                valueFormatter=JsCode(
                    "function(p){return p.value==null?'':Number(p.value).toFixed(2)+' %'}"
                ),
            )
            gb.configure_column("DIL", width=260)
            gb.configure_column("DO", width=200)
            gb.configure_column("CON", width=140)
            gb.configure_column("CT", width=90)
            gb.configure_column("IE", width=150, cellEditor="agSelectCellEditor",
                                cellEditorParams={"values": _with_existing(aux.get("IE", []), "IE")})
            gb.configure_column("CC", width=140, cellEditor="agSelectCellEditor",
                                cellEditorParams={"values": _with_existing(aux.get("CC", []), "CC")})
            gb.configure_column("AE", width=80, cellEditor="agSelectCellEditor",
                                cellEditorParams={"values": _with_existing(aux.get("AE", []), "AE")})
            gb.configure_column("SA", width=70, cellEditor="agSelectCellEditor",
                                cellEditorParams={"values": [str(x) for x in sa_col_opts]})
            gb.configure_column("CED", editable=False, width=220)
            gb.configure_selection("multiple", use_checkbox=True, header_checkbox=True)
            gb.configure_grid_options(
                getRowStyle=JsCode(
                    "function(p){return (p.data && p.data.__shade) "
                    "? {'background-color':'#ece6f9'} : null}"
                ),
                rowHeight=30,
            )

            grid = AgGrid(
                il_df,
                gridOptions=gb.build(),
                update_on=[("cellValueChanged", 400), "selectionChanged"],
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=False,
                height=430,
                theme="balham",
                key=f"il_grid_{st.session_state.il_nonce}",
            )

            # Lo que hay ahora mismo en la rejilla (en su orden actual, sin agrupar).
            grid_df = pd.DataFrame(grid["data"])
            if grid_df.empty:
                grid_df = il_df.copy()
            pending = [_parse_grid_row(r) for _, r in grid_df.iterrows()]
            st.session_state.il_pending = pending

            sel = grid["selected_rows"]
            sel_ids = set()
            if sel is not None:
                sel_records = sel.to_dict("records") if isinstance(sel, pd.DataFrame) else sel
                sel_ids = {int(s["__id"]) for s in sel_records if s.get("__id") is not None}
            grid_ids = [
                int(r["__id"]) if not pd.isna(r.get("__id")) else -1
                for _, r in grid_df.iterrows()
            ]

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

            if del_click and sel_ids:
                kept = [p for p, i in zip(pending, grid_ids) if i not in sel_ids]
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
