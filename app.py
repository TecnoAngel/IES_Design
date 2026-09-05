from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
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
PAGES = ["Inicio", "Situaciones de aprendizaje", "Programación de aula"]
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

# PÁGINA: SITUACIONES DE APRENDIZAJE
elif page == "Situaciones de aprendizaje":
    st.markdown(
        '<div class="panel-card"><h3>Situaciones de aprendizaje</h3>'
        "<p>Sube tu copia del Excel de programación, edita la tabla de situaciones "
        "de aprendizaje (añadir, quitar o modificar filas) y descarga el Excel "
        "actualizado. No se toca nada más del libro: el modelo de datos, las tablas "
        "dinámicas y el formato condicional se conservan y se recalculan al abrirlo.</p></div>",
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

    st.markdown("### Archivo")
    sa_excel = st.file_uploader(
        "Excel de programación (.xlsx con la hoja 'SituacionesAprendizaje')",
        type=["xlsx", "xlsm"],
        key="sa_excel_uploader",
    )

    # Al cambiar de archivo, se recarga la tabla desde cero.
    if sa_excel is not None and st.session_state.get("sa_loaded_name") != sa_excel.name:
        try:
            data = read_situaciones(sa_excel)
            st.session_state.sa_df = pd.DataFrame(
                [[s.sa, s.ev, s.dsa, s.hsa] for s in data.situaciones], columns=COLS
            )
            st.session_state.sa_previstas = {
                t: float(data.horas_previstas.get(t, 0.0)) for t in TRIMESTRES
            }
            st.session_state.sa_loaded_name = sa_excel.name
            st.session_state.pop("sa_out", None)
        except Exception as exc:
            st.error(f"No se ha podido leer el Excel: {exc}")

    if sa_excel is None:
        st.info("Sube el Excel para empezar a editar.")
    elif "sa_df" in st.session_state:
        st.divider()
        st.markdown("### Situaciones de aprendizaje")
        st.caption(
            "SA = nº de situación · EV = evaluación/trimestre (1, 2 o 3) · "
            "DSA = descripción · HSA = horas previstas para la situación."
        )

        edited = st.data_editor(
            st.session_state.sa_df,
            num_rows="dynamic",
            use_container_width=True,
            key="sa_editor",
            column_config={
                "SA": st.column_config.NumberColumn("SA (nº)", min_value=1, step=1, format="%d"),
                "EV": st.column_config.SelectboxColumn("EV (trimestre)", options=list(TRIMESTRES)),
                "DSA": st.column_config.TextColumn("Descripción", width="large"),
                "HSA": st.column_config.NumberColumn("Horas (HSA)", min_value=0, step=1, format="%d"),
            },
        )

        # Validaciones
        errores = []
        filas = [r for _, r in edited.iterrows() if not r[COLS].isna().all()]
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

        # Panel de horas: previstas vs acumuladas
        st.divider()
        st.markdown("### Horas por trimestre")
        st.caption(
            "Las horas previstas se toman del propio Excel; ajústalas a mano si quieres. "
            "(Calcularlas desde el calendario oficial de Castilla y León, como en IES Creator, "
            "queda para el siguiente paso.)"
        )

        sits_para_calculo = [
            Situacion(
                sa=None if pd.isna(r["SA"]) else int(r["SA"]),
                ev=None if pd.isna(r["EV"]) else int(r["EV"]),
                dsa=str(r["DSA"] or ""),
                hsa=None if pd.isna(r["HSA"]) else float(r["HSA"]),
            )
            for r in filas
        ]
        acumulado = acumulado_por_trimestre(sits_para_calculo)

        prev_cols = st.columns(3)
        previstas = {}
        for col, tri in zip(prev_cols, TRIMESTRES):
            with col:
                previstas[tri] = st.number_input(
                    f"{tri}º trimestre — horas previstas",
                    min_value=0.0,
                    step=1.0,
                    value=float(st.session_state.sa_previstas.get(tri, 0.0)),
                    key=f"sa_prev_{tri}",
                )
                acc = acumulado.get(tri, 0.0)
                desv = previstas[tri] - acc
                st.metric(
                    "Acumulado (suma HSA)",
                    f"{acc:g} h",
                    delta=f"{desv:+g} h de desviación",
                    delta_color="normal" if desv >= 0 else "inverse",
                )
                if desv < 0:
                    st.error(f"Te pasas {abs(desv):g} h en el {tri}º trimestre.")

        total_prev = sum(previstas.values())
        total_acc = sum(acumulado.values())
        st.markdown(
            f"**Total curso:** {total_acc:g} h planificadas de {total_prev:g} h previstas "
            f"(**{total_prev - total_acc:+g} h**)."
        )

        # Guardar
        st.divider()
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("Guardar y preparar descarga", use_container_width=True, type="primary", key="btn_save_sa"):
                if errores:
                    st.error("Corrige los avisos antes de guardar:\n\n- " + "\n- ".join(errores))
                else:
                    try:
                        st.session_state.sa_out = save_situaciones(sa_excel, sits_para_calculo, previstas)
                        st.success("Excel actualizado. Descárgalo abajo.")
                    except Exception as exc:
                        st.error(f"Error al guardar el Excel: {exc}")
        with col2:
            if st.button("Descartar cambios", use_container_width=True, key="btn_reset_sa"):
                for k in ("sa_df", "sa_previstas", "sa_loaded_name", "sa_out"):
                    st.session_state.pop(k, None)
                st.rerun()

        if errores:
            st.warning("Avisos:\n\n- " + "\n- ".join(errores))

        if st.session_state.get("sa_out"):
            nombre = sa_excel.name.rsplit(".", 1)[0] + "_actualizado.xlsx"
            st.download_button(
                "Descargar Excel actualizado",
                data=st.session_state.sa_out,
                file_name=nombre,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
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
