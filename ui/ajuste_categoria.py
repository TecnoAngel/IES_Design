"""Ajuste de pesos «por categoría» (p. ej. Destrezas): el docente fija qué % de
la programación debe pesar cada opción de la categoría y la app propone los
pesos P de los criterios (y los PIL que haga falta) para cumplirlo. Lo calcula
``tools.ajuste_pesos.sugerir_por_categoria``. No toca nada hasta que se pulsa
«Cargar» (que reutiliza ``_ipf_cargar`` de ``app.py``).

Solo widgets de Streamlit y una rejilla AgGrid pequeña para los objetivos
(como la de instrumentos; AgGrid y no ``st.data_editor`` porque las tablas
nativas salían en negro en algunos navegadores).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from tools.ajuste_pesos import sugerir_por_categoria


# Columnas propias de la rejilla de indicadores por las que también se puede
# ajustar, como si fueran categorías: (clave de la fila, nombre, clave del catálogo).
COLUMNAS_AGRUPABLES = [
    ("IE", "Instrumento de evaluación", "IE"),
    ("CC", "Criterio de calificación", "CC"),
    ("AE", "Agente evaluador", "AE"),
    ("SA", "Situación de aprendizaje", None),
]


def _txt(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip()


def agrupaciones(il_rows, categorias, aux) -> tuple[dict, list]:
    """Todo por lo que se puede ajustar: las columnas de la rejilla (IE, CC, AE,
    SA) y las categorías definidas por el docente. Devuelve ``({id: categoría},
    filas)``; las filas llevan en ``CAT`` también el valor de esas columnas, así
    ``sugerir_por_categoria`` las trata a todas igual. Los ids de las columnas son
    ``"col:IE"``…; los de las categorías, sus números."""
    cats: dict = {}
    filas = [{**r, "CAT": dict(r.get("CAT") or {})} for r in il_rows]
    for clave, titulo, catalogo in COLUMNAS_AGRUPABLES:
        valores = [_txt(r.get(clave)) for r in il_rows]
        usados = sorted({v for v in valores if v}, key=lambda s: (not s.isdigit(), int(s) if s.isdigit() else 0, s))
        extra = [v for v in (aux or {}).get(catalogo, []) if v and v not in usados] if catalogo else []
        if not usados:
            continue
        cid = f"col:{clave}"
        cats[cid] = {"id": cid, "nombre": titulo,
                     "opciones": [{"id": v, "nombre": (f"SA {v}" if clave == "SA" else v)}
                                  for v in usados + extra]}
        for f, v in zip(filas, valores):
            f["CAT"][cid] = v or None
    for c in categorias or []:
        if c["nombre"]:
            cats[c["id"]] = c
    return cats, filas


def pintar(il_rows, ce_list, ce_p, categoria, *, tabla_html, cargar) -> None:
    """``tabla_html(cabeceras, filas, alto=)`` y ``cargar(p_por_ce, pil_por_il)``
    vienen de ``app.py``."""
    from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

    from tools.situaciones_informe import AGGRID_GRID_CSS

    ss = st.session_state
    cid = categoria["id"]
    opciones = [o for o in categoria["opciones"] if o["nombre"]]
    if not opciones:
        st.info(f"La categoría «{categoria['nombre']}» todavía no tiene opciones.")
        return
    if not any((r.get("CAT") or {}).get(cid) for r in il_rows):
        st.info(
            f"Ningún indicador tiene «{categoria['nombre']}» asignada: elígela en la columna "
            "correspondiente de Indicadores de logro."
        )
        return

    nombre = {o["id"]: o["nombre"] for o in opciones}
    actual = sugerir_por_categoria(il_rows, ce_p, categoria, {})["actual"]
    clave_df = f"ipf_cat_df_{cid}"
    if clave_df not in ss or list(ss[clave_df]["Opción"]) != [o["nombre"] for o in opciones]:
        ss[clave_df] = pd.DataFrame({
            "Opción": [o["nombre"] for o in opciones],
            "Actual (%)": [round(actual.get(o["id"], 0.0), 2) for o in opciones],
            "Objetivo (%)": [round(actual.get(o["id"], 0.0), 2) for o in opciones],
        })

    col_obj, col_sug = st.columns([1, 1], gap="large")
    with col_obj:
        st.markdown(
            f'<div class="mini-label">Peso de cada «{categoria["nombre"]}» en la programación '
            "(edita el objetivo; deben sumar 100 %)</div>",
            unsafe_allow_html=True,
        )
        df = ss[clave_df].drop(columns="::auto_unique_id::", errors="ignore").copy()
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=False, resizable=True, sortable=False, filter=False)
        gb.configure_column("Opción", flex=1, minWidth=180)
        gb.configure_column(
            "Actual (%)", width=100, type=["numericColumn"],
            valueFormatter=JsCode("function(p){return p.value==null?'':Number(p.value).toFixed(2)}"),
        )
        gb.configure_column(
            "Objetivo (%)", editable=True, width=120, type=["numericColumn"],
            valueParser=JsCode(
                "function(p){var n=parseFloat(String(p.newValue).replace(',','.'));"
                "return isNaN(n)?0:Math.min(100,Math.max(0,Math.round(n*100)/100))}"
            ),
            valueFormatter=JsCode("function(p){return p.value==null?'':Number(p.value).toFixed(2)}"),
        )
        gb.configure_grid_options(rowHeight=30)
        g = AgGrid(
            df, gridOptions=gb.build(), update_on=[("cellValueChanged", 300)],
            allow_unsafe_jscode=True, fit_columns_on_grid_load=False, custom_css=AGGRID_GRID_CSS,
            height=56 + 30 * len(df), theme="balham",
            key=f"ipf_cat_grid_{cid}_" + "|".join(str(o["id"]) for o in opciones),
        )
        ed = pd.DataFrame(g["data"])
        if ed.empty or "Objetivo (%)" not in ed.columns:
            ed = ss[clave_df]
        objetivo = {
            o["id"]: 0.0 if pd.isna(v) else float(v or 0.0)
            for o, v in zip(opciones, ed["Objetivo (%)"].tolist())
        }
        suma = sum(objetivo.values())
        suma_ok = abs(suma - 100) <= 0.5
        st.caption(
            f"Σ = {suma:.2f} %" if suma_ok
            else f"Σ = {suma:.2f} % — deben sumar 100 % para poder cargar."
        )

    res = sugerir_por_categoria(il_rows, ce_p, categoria, objetivo)
    pce, pil = res["p_por_ce"], res["pil_por_il"]

    with col_sug:
        st.markdown('<div class="mini-label">Sugerencia</div>', unsafe_allow_html=True)
        t_ce, t_op = st.tabs([f"P por CE ({len(pce)})", f"Por {categoria['nombre'].lower()}"])
        t_ce.markdown(
            tabla_html(
                ["CE", categoria["nombre"], "P actual", "P sugerido"],
                [
                    [ce, res["opcion_de_ce"].get(ce, ""), f"{ce_p.get(ce, 0):g}",
                     f"{pce.get(ce, 0):.2f}".rstrip("0").rstrip(".")]
                    for ce in ce_list if ce in pce
                ],
                alto=260,
            ),
            unsafe_allow_html=True,
        )
        t_op.markdown(
            tabla_html(
                [categoria["nombre"], "Actual %", "Objetivo %", "Sugerido %"],
                [
                    [nombre[o["id"]], f"{res['actual'][o['id']]:.2f}", f"{objetivo[o['id']]:.2f}",
                     f"{res['sugerido'][o['id']]:.2f}"]
                    for o in opciones
                ],
                alto=260,
            ),
            unsafe_allow_html=True,
        )

    if res["sin_opcion"]:
        st.warning(
            f"{len(res['sin_opcion'])} indicador(es) sin «{categoria['nombre']}»: conservan su "
            "peso y el objetivo se reparte entre el resto."
        )
    if res["sin_indicadores"]:
        st.warning(
            "Sin indicadores (no se puede cumplir su objetivo): "
            + ", ".join(nombre[o] for o in res["sin_indicadores"])
        )
    if pil:
        st.caption(f"Cambian también los PIL de {len(pil)} indicadores (criterios con varias opciones).")

    b1, _ = st.columns([1.4, 5])
    if b1.button("Cargar los pesos", type="primary", disabled=not suma_ok, key=f"ipf_cat_ok_{cid}"):
        cargar(pce, pil or None)
