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

# PÁGINA: INICIO
if page == "Inicio":
    st.markdown('<div class="panel-card"><h3>Bienvenido</h3><p>Elige una sección arriba para empezar.</p></div>', unsafe_allow_html=True)

# PÁGINA: DISEÑO DE LA PROGRAMACIÓN
elif page == "Diseño de la programación":
    st.markdown(
        '<div class="panel-card"><h3>Diseño de la programación</h3>'
        "<p>Sube tu copia del Excel de programación y edita sus tablas curriculares "
        "(situaciones de aprendizaje, indicadores de logro…) sin riesgo de romper el "
        "libro: el modelo de datos, las tablas dinámicas y el formato condicional se "
        "conservan y se recalculan al abrirlo.</p></div>",
        unsafe_allow_html=True,
    )

    from tools.situaciones_aprendizaje import (
        TRIMESTRES,
        Situacion,
        acumulado_por_trimestre,
        read_situaciones,
        save_situaciones,
    )

    COLS = ["SA", "EV", "DSA", "HSA"]

    prog_excel = st.file_uploader(
        "Excel de programación (.xlsx)",
        type=["xlsx", "xlsm"],
        key="prog_excel_uploader",
    )

    # Al cambiar de archivo, se recargan las tablas desde cero.
    if prog_excel is not None and st.session_state.get("prog_loaded_name") != prog_excel.name:
        try:
            data = read_situaciones(prog_excel)
            st.session_state.sa_df = pd.DataFrame(
                [[s.sa, s.ev, s.dsa, s.hsa] for s in data.situaciones], columns=COLS
            )
            st.session_state.sa_previstas = {
                t: float(data.horas_previstas.get(t, 0.0)) for t in TRIMESTRES
            }
            st.session_state.prog_loaded_name = prog_excel.name
            st.session_state.pop("sa_out", None)
        except Exception as exc:
            st.error(f"No se ha podido leer el Excel: {exc}")

    if prog_excel is None:
        st.info("Sube el Excel para empezar a editar.")
    elif "sa_df" in st.session_state:
        from tools.situaciones_informe import (
            build_image_copy_html,
            build_pie_png,
            build_table_copy_html,
            hsa_share,
        )

        # ───────────────── BLOQUE: SITUACIONES DE APRENDIZAJE ─────────────────
        st.markdown(
            '<div class="block-head">Situaciones de aprendizaje'
            '<span class="block-sub">tabla <code>tablaSAprendizaje</code> · '
            "reparto de horas y control de desviación por trimestre</span></div>",
            unsafe_allow_html=True,
        )

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
                st.warning("Avisos:\n\n- " + "\n- ".join(errores))

            gcol1, gcol2 = st.columns([2, 1])
            with gcol1:
                if st.button("Guardar y preparar descarga", use_container_width=True, type="primary", key="btn_save_sa"):
                    if errores:
                        st.error("Corrige los avisos antes de guardar.")
                    else:
                        try:
                            st.session_state.sa_out = save_situaciones(prog_excel, sits, previstas)
                            st.success("Excel actualizado. Descárgalo abajo.")
                        except Exception as exc:
                            st.error(f"Error al generar el Excel: {exc}")
            with gcol2:
                if st.button("Descartar cambios", use_container_width=True, key="btn_reset_sa"):
                    for k in ("sa_df", "sa_previstas", "prog_loaded_name", "sa_out"):
                        st.session_state.pop(k, None)
                    st.rerun()

            if st.session_state.get("sa_out"):
                nombre = prog_excel.name.rsplit(".", 1)[0] + "_actualizado.xlsx"
                st.download_button(
                    "Descargar Excel actualizado",
                    data=st.session_state.sa_out,
                    file_name=nombre,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

        # ───────────────── BLOQUE: INDICADORES DE LOGRO ─────────────────
        st.markdown(
            '<div class="block-head">Indicadores de logro'
            '<span class="block-sub">tabla <code>TablaIndicadoresLogro</code> · en construcción</span></div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.caption(
                "Aquí irá el editor de la tabla de indicadores de logro (CE, IL, pesos…), "
                "con el mismo esquema: editar filas y guardar sin romper el Excel."
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
