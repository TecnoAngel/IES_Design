"""Pestaña «Actividades por situación de aprendizaje» (Programación de aula).

Todo lo que se ve en la pestaña está en este archivo, en el orden en que
aparece en pantalla:

    pintar()               ← lo llama app.py con la SA elegida en el selector
      ├─ _cuadro_actividades()   Cuadro 1: una fila por actividad
      ├─ _cuadro_pesos()         Cuadro 2: una fila por indicador y actividad
      └─ _cuadro_cuaderno()      Cuadro 3: vista en el cuaderno (iDoceo / Additio)

Los cálculos (%, factores…) no están aquí sino en
``tools/programacion_aula_editor.py``.

Cómo funciona la edición (el mismo patrón en todos los campos):

1. Las actividades viven en ``st.session_state.pa_acts`` (lista de dicts, ver
   ``tools/programacion_aula_editor.py``). Eso es lo que se guarda en el proyecto.
2. Antes de pintar un campo se copia a su ``key`` el valor que hay en
   ``pa_acts``; así el campo siempre enseña lo que hay guardado.
3. Cuando el docente lo cambia, Streamlit llama a la función ``on_change``
   (``_al_cambiar_…``), que escribe el valor nuevo en ``pa_acts`` con
   ``_guardar()``.

Para cambiar anchos de columna: las listas ``ANCHOS_…`` de aquí abajo.
Para cambiar colores de las actividades: ``TONOS``.
"""

from __future__ import annotations

from html import escape

import streamlit as st

from tools.programacion_aula_editor import (
    codigos,
    enlaces_por_il,
    fraccion_por_enlace,
    nuevo_id,
    reparto_pendiente,
    valores_actividades,
    valores_enlaces,
)

# Anchos relativos de las columnas de cada cuadro (st.columns).
#                     código  nombre  borrar  IL   instrumento  % prog  % SA
ANCHOS_ACTIVIDADES = [0.55,   3.0,    0.45,   3.8, 2.0,         1.0,    1.0]
#               actividad  peso  %    % prog  % SA  factor
ANCHOS_PESOS = [4.4,       1.2,  1.0, 1.0,    1.0,  1.0]

# Un color pastel por actividad (por su posición en la SA), el mismo en los
# tres cuadros: (fondo, fondo suave, franja, texto). Texto ≥ 4,5:1 sobre blanco.
TONOS = [
    ("#FCE8EC", "#FEF5F7", "#E9A3B1", "#8A2A3C"),
    ("#E3EEF9", "#F2F7FC", "#93B8DE", "#2A557F"),
    ("#E5F1E8", "#F3F8F4", "#9CC9A8", "#2E6640"),
    ("#FDEBDD", "#FEF6EF", "#EDB48A", "#8A4A1C"),
    ("#EEE7F7", "#F7F3FB", "#B9A3DB", "#553A80"),
    ("#FBF3D5", "#FDFAEC", "#E2C766", "#6E5A10"),
]

# Estilos propios de esta pestaña (las etiquetas .pa-tag y la tabla .cuad del
# cuaderno están en el CSS general de app.py). Streamlit pone a cada
# st.container(key="x") la clase «st-key-x»: así se da color a cuadros y filas.
#   actbox_N   cada uno de los tres cuadros      actcab_N   fila de títulos de columna
#   actfila_ID fila de una actividad (cuadro 1)  actpie_1   fila de totales
#   actil_N    bloque de un indicador (cuadro 2) actpeso_ID_N  fila de una actividad en él
CSS = """
<style>
/* Streamlit resta 1rem por debajo a cada texto (espera un párrafo); con
   nuestras celdas eso descuadra las filas: se anula dentro de los cuadros. */
[class*="st-key-actbox_"] [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }

/* Los tres cuadros: franja carmín arriba (recta: va como sombra interior, un
   borde grueso se afila en las esquinas redondeadas) y título con su número.
   «gap» es la separación entre las filas del cuadro. */
[class*="st-key-actbox_"] { border-radius: 10px !important; background: #fff; gap: 0.4rem !important;
                            box-shadow: inset 0 3px 0 #A6182E, 0 2px 10px rgba(34,28,24,0.06) !important; }
[class*="st-key-actil_"] { gap: 0.3rem !important; }
.act-titulo { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.1rem; }
.act-n    { flex: none; width: 1.6rem; height: 1.6rem; border-radius: 50%; background: #A6182E; color: #fff;
            font-weight: 700; font-size: 0.92rem; display: flex; align-items: center; justify-content: center; }
.act-t    { font-size: 1.12rem; font-weight: 700; color: #7d1022; line-height: 1.2; }
.act-sub  { font-size: 0.85rem; color: #5c524a; margin: 0 0 0.2rem 2.2rem; line-height: 1.4; }

/* Fila de títulos de columna, filas y totales: mismo margen para que todo quede en columna */
[class*="st-key-actcab_"], [class*="st-key-actfila_"], [class*="st-key-actpeso_"], .st-key-actpie_1 {
    padding: 0.25rem 0.7rem; border-left: 4px solid transparent; border-radius: 6px; }
[class*="st-key-actcab_"] { background: #5c524a; }
.act-cab  { font-size: 0.74rem; font-weight: 700; color: #fff; text-transform: uppercase;
            letter-spacing: 0.05em; white-space: nowrap; }
.st-key-actpie_1 { border-top: 2px solid #e3d5c3; border-radius: 0; }
/* (en el cuadro 2 las filas van dentro del bloque de su indicador, que tiene su propio margen) */
.st-key-actcab_2 { padding-left: calc(1.15rem + 1px); padding-right: calc(1.15rem + 1px); }

/* Fila de una actividad: fondo y franja de su color (variables --suave/--franja, una por actividad) */
[class*="st-key-actfila_"], [class*="st-key-actpeso_"] { background: var(--suave); border-left-color: var(--franja); }
[class*="st-key-actfila_"] [data-baseweb="input"], [class*="st-key-actfila_"] [data-baseweb="input"] > div,
[class*="st-key-actfila_"] input, [class*="st-key-actfila_"] [data-testid="stMultiSelect"] [role="group"],
[class*="st-key-actpeso_"] [data-testid="stNumberInputContainer"],
[class*="st-key-actpeso_"] [data-testid="stNumberInputContainer"] * { background: #fff !important; }
[class*="st-key-actfila_"] input { font-weight: 600; }

/* Bloque de un indicador en el cuadro 2 */
[class*="st-key-actil_"] { border: 1px solid #e3d5c3; border-radius: 8px; background: #fbf6ef; padding: 0.45rem; }
.act-il-cab { display: flex; align-items: baseline; gap: 0.6rem; padding: 0.1rem 0.3rem; }
.act-il   { flex: none; font-weight: 700; color: #fff; background: #221c18; border-radius: 6px; padding: 0.05rem 0.5rem; }
.act-il-txt { flex: 1; font-size: 0.92rem; font-weight: 600; color: #221c18; line-height: 1.3; }
.act-il-ie { flex: none; }

/* Textos de las celdas */
.act-num  { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.act-total { font-weight: 700; }
.act-fuerte { font-weight: 700; font-size: 1.02rem; }
.act-cod  { display: inline-block; min-width: 2.3rem; text-align: center; font-weight: 700;
            font-size: 0.9rem; border-radius: 6px; padding: 0.1rem 0.4rem; border: 1px solid; }
.act-nombre { font-weight: 600; }
.act-ie   { display: inline-block; font-size: 0.82rem; font-weight: 600; color: #221c18; background: #fff;
            border: 1px solid #cdbba5; border-radius: 999px; padding: 0.1rem 0.65rem; }
/* Selector de indicadores: una etiqueta por línea con el código y el texto
   del indicador; si no cabe se corta con «…» y se ve entero al pasar el ratón.
   La etiqueta va sin borde (fondo crema) y sin los márgenes de Streamlit, con
   el mismo hueco de 4px por arriba, abajo e izquierda: así queda centrada con
   la «x» y la flecha y no hay una caja dentro de otra. */
[class*="st-key-paact_ils_"] [data-testid="stMultiSelect"] [role="group"] {
    height: auto !important; max-height: none !important; }
[class*="st-key-paact_ils_"] [data-testid="stMultiSelectTagsContainer"] {
    overflow: hidden !important; padding: 4px 0 4px 4px !important; }
[class*="st-key-paact_ils_"] [data-testid="stMultiSelectTagsContainer"] > [role="group"] {
    display: flex; flex-direction: column; align-items: stretch; gap: 3px; flex: 1 1 auto; min-width: 0; }
[class*="st-key-paact_ils_"] [data-testid="stMultiSelectTagsContainer"] input { margin: 0 !important; }
[class*="st-key-paact_ils_"] [data-testid="stMultiSelect"] [role="group"] span[data-tag] {
    display: flex; max-width: 100% !important; min-width: 0; margin: 0 !important;
    background: #f4ece1 !important; border: none; border-radius: 5px !important; }
[class*="st-key-paact_ils_"] [data-tag] > span {
    flex: 1 1 auto; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    color: #221c18 !important; cursor: help; }
[class*="st-key-paact_ils_"] [data-tag] * { color: #221c18 !important; }
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades pequeñas
# ─────────────────────────────────────────────────────────────────────────────
def _pct(x: float) -> str:
    """0.1234 → «12,34 %»."""
    return f"{x * 100:.2f}".replace(".", ",") + " %"


def _numero(x: float) -> str:
    """1.50 → «1,5» · 2.00 → «2»."""
    return f"{x:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def _html(texto: str) -> None:
    st.markdown(texto, unsafe_allow_html=True)


def _celda(col, texto: str, clase: str = "") -> None:
    """Escribe un texto (HTML) en una columna, con una clase CSS opcional."""
    col.markdown(f'<div class="{clase}">{texto}</div>', unsafe_allow_html=True)


def _cabecera(n: int, anchos: list[float], titulos: list[str], desde_num: int) -> None:
    """Fila de títulos de columna del cuadro `n`; las columnas desde
    `desde_num` son numéricas y van alineadas a la derecha."""
    with st.container(key=f"actcab_{n}"):
        for i, (col, titulo) in enumerate(zip(st.columns(anchos), titulos)):
            _celda(col, titulo, "act-cab act-num" if i >= desde_num else "act-cab")


def _titulo(n: int, texto: str, sub: str) -> None:
    """Título de un cuadro: número en un círculo, título y línea explicativa."""
    _html(f'<div class="act-titulo" role="heading" aria-level="3"><span class="act-n">{n}</span>'
          f'<span class="act-t">{escape(texto)}</span></div>'
          f'<div class="act-sub">{escape(sub)}</div>')


def _instrumento(texto) -> str:
    return f'<span class="act-ie">{escape(str(texto))}</span>' if texto else "—"


def _etiqueta_actividad(act: dict, cod: dict, tono: dict) -> str:
    """Código de la actividad (A1, A2…) en su color."""
    if act["id"] not in tono:  # actividad de otra SA: en gris
        return f'<span class="pa-tag info">{cod[act["id"]]} (SA {act.get("SA")})</span>'
    fondo, _suave, franja, tinta = tono[act["id"]]
    return (f'<span class="act-cod" style="background:{fondo};border-color:{franja};'
            f'color:{tinta}">{cod[act["id"]]}</span>')


def _guardar(actividades: list[dict]) -> None:
    """Deja la lista nueva de actividades en la sesión y marca que el proyecto
    y el Word ya generados han quedado anticuados."""
    ss = st.session_state
    ss.pa_acts = actividades
    ss.pop("prog_out", None)
    ss.pop("pa_docx", None)


# ─────────────────────────────────────────────────────────────────────────────
# Funciones on_change: pasan lo que ha tocado el docente a pa_acts
# ─────────────────────────────────────────────────────────────────────────────
def _al_cambiar_actividad(aid: int, il_info: dict) -> None:
    """Nombre o indicadores de la actividad `aid`. El instrumento es siempre
    el de sus indicadores."""
    ss = st.session_state
    titulo = str(ss.get(f"paact_tit_{aid}") or "").strip()
    elegidos = list(ss.get(f"paact_ils_{aid}") or [])
    nuevas = []
    for a in ss.pa_acts:
        if a["id"] == aid:
            pesos = {e["IL"]: e.get("PA") for e in a.get("ils", [])}
            instrumento = str(il_info.get(elegidos[0], {}).get("IE") or "") if elegidos else ""
            a = dict(a, titulo=titulo, IE=instrumento,
                     ils=[{"IL": il, "PA": pesos.get(il)} for il in elegidos])
        nuevas.append(a)
    _guardar(nuevas)


def _al_cambiar_peso(aid: int, il: str) -> None:
    """Peso de la actividad `aid` dentro del indicador `il`."""
    ss = st.session_state
    peso = ss.get(f"paact_pa_{aid}_{il}")
    _guardar([
        dict(a, ils=[dict(e, PA=peso) if e["IL"] == il else e for e in a.get("ils", [])])
        if a["id"] == aid else a
        for a in ss.pa_acts
    ])


def _borrar_actividad(aid: int) -> None:
    _guardar([a for a in st.session_state.pa_acts if a["id"] != aid])


def _anadir_actividad(sa) -> None:
    acts = st.session_state.pa_acts
    _guardar(acts + [{"id": nuevo_id(acts), "SA": sa, "IE": "", "titulo": "", "ils": []}])


# ─────────────────────────────────────────────────────────────────────────────
# Punto de entrada
# ─────────────────────────────────────────────────────────────────────────────
def pintar(sa, il_rows: list[dict], ce_p: dict[str, float]) -> None:
    """Pinta los tres cuadros de la situación de aprendizaje `sa`.

    `il_rows`: indicadores de logro ya recalculados (dicts con IL, CE, PIL,
    DIL, IE, SA…). `ce_p`: peso P de cada criterio de evaluación."""
    ss = st.session_state
    _html(CSS)

    ils_sa = [r for r in il_rows if r.get("SA") == sa]   # indicadores de esta SA
    il_info = {r["IL"]: r for r in il_rows}               # IL → su fila

    if not ils_sa:
        st.info("Esta situación de aprendizaje aún no tiene indicadores de logro "
                "(se asignan en «Diseño de la programación» › Indicadores de logro).")
        return

    # SA sin actividades: se empieza con una actividad vacía por indicador.
    if not any(a.get("SA") == sa for a in ss.pa_acts):
        nuevas = list(ss.pa_acts)
        for r in ils_sa:
            nuevas.append({"id": nuevo_id(nuevas), "SA": sa, "IE": str(r.get("IE") or ""),
                           "titulo": "", "ils": [{"IL": r["IL"], "PA": None}]})
        _guardar(nuevas)

    acts_sa = [a for a in ss.pa_acts if a.get("SA") == sa]
    # Datos calculados que comparten los tres cuadros
    d = {
        "sa": sa,
        "ils_sa": ils_sa,
        "il_info": il_info,
        "acts_sa": acts_sa,
        "cod": codigos(ss.pa_acts),                    # id → «A1»
        "tono": {a["id"]: TONOS[i % len(TONOS)] for i, a in enumerate(acts_sa)},
        "enlaces": enlaces_por_il(ss.pa_acts),         # IL → [(actividad, enlace)]
        "parte": fraccion_por_enlace(ss.pa_acts),      # (id, IL) → parte del IL (0-1)
        "pendientes": set(reparto_pendiente(ss.pa_acts)),  # IL a los que les falta algún peso
        "valor_enlace": valores_enlaces(ss.pa_acts, il_rows, ce_p),  # (id, IL) → valor s/ programación
        "valor_act": {v["id"]: v for v in valores_actividades(ss.pa_acts, il_rows, ce_p)},
    }
    # Valor de toda la SA sobre la programación (para los % sobre la SA)
    d["total_sa"] = sum(d["valor_act"][a["id"]]["valor_prog"] for a in acts_sa)

    # Color de las filas de cada actividad (cuadros 1 y 2)
    _html("<style>" + "".join(
        f'.st-key-actfila_{aid}, [class*="st-key-actpeso_{aid}_"] '
        f"{{ --suave:{suave}; --franja:{franja}; }}"
        for aid, (_fondo, suave, franja, _tinta) in d["tono"].items()
    ) + "</style>")

    with st.container(border=True, key="actbox_1"):
        _cuadro_actividades(d)
    with st.container(border=True, key="actbox_2"):
        _cuadro_pesos(d)
    with st.container(border=True, key="actbox_3"):
        _cuadro_cuaderno(d)


# ─────────────────────────────────────────────────────────────────────────────
# Cuadro 1 · Actividades
# ─────────────────────────────────────────────────────────────────────────────
def _cuadro_actividades(d: dict) -> None:
    ss = st.session_state
    il_info = d["il_info"]

    def etiqueta_il(il: str) -> str:
        """«1.2.1 · texto del indicador» (lo que se ve en el selector)."""
        texto = str(il_info.get(il, {}).get("DIL") or "")
        return f"{il} · {texto}" if texto else il

    _titulo(1, "Actividades",
            "Pon nombre a cada actividad y elige el indicador de logro que evalúa (pueden ser "
            "varios si comparten instrumento). El instrumento es el del indicador. «% prog.» y "
            "«% SA»: valor sobre la programación y sobre la situación de aprendizaje.")
    _cabecera(1, ANCHOS_ACTIVIDADES,
              ["", "Actividad", "", "Indicador de logro", "Instrumento",
               "% prog.", "% SA"], desde_num=5)

    for a in d["acts_sa"]:
        aid = a["id"]
        elegidos = [e["IL"] for e in a.get("ils", [])]
        with st.container(key=f"actfila_{aid}"):
            c_cod, c_nom, c_del, c_il, c_ie, c_prog, c_sa = st.columns(
                ANCHOS_ACTIVIDADES, vertical_alignment="center")

            _celda(c_cod, _etiqueta_actividad(a, d["cod"], d["tono"]))

            ss[f"paact_tit_{aid}"] = a.get("titulo", "")
            c_nom.text_input(
                "Nombre de la actividad", key=f"paact_tit_{aid}",
                placeholder="Nombre de la actividad", label_visibility="collapsed",
                on_change=_al_cambiar_actividad, args=(aid, il_info),
            )

            c_del.button(
                "", key=f"paact_del_{aid}", icon=":material/delete:", type="tertiary",
                help=f"Eliminar la actividad {d['cod'][aid]}",
                on_click=_borrar_actividad, args=(aid,),
            )

            # Indicadores que se ofrecen: todos los de la SA si aún no hay
            # ninguno elegido; si ya hay, solo los del mismo instrumento.
            if elegidos:
                opciones = [r["IL"] for r in d["ils_sa"]
                            if str(r.get("IE") or "") == str(a.get("IE") or "")]
                opciones += [il for il in elegidos if il not in opciones]
            else:
                opciones = [r["IL"] for r in d["ils_sa"]]
            ss[f"paact_ils_{aid}"] = elegidos
            c_il.multiselect(
                "Indicador de logro", opciones, key=f"paact_ils_{aid}",
                format_func=etiqueta_il, placeholder="Elige el indicador",
                label_visibility="collapsed",
                on_change=_al_cambiar_actividad, args=(aid, il_info),
            )
            if not elegidos:
                _celda(c_ie, '<span class="pa-tag warn">Sin indicador</span>')
            else:
                _celda(c_ie, _instrumento(a.get("IE")))
            valor = d["valor_act"][aid]
            _celda(c_prog, _pct(valor["valor_prog"]), "act-num act-fuerte")
            _celda(c_sa, _pct(valor["valor_sa"]), "act-num act-fuerte")

    # Fila de totales
    with st.container(key="actpie_1"):
        c = st.columns(ANCHOS_ACTIVIDADES, vertical_alignment="center")
        c[1].button("Añadir actividad", key=f"paact_add_{d['sa']}", icon=":material/add:",
                    type="primary", on_click=_anadir_actividad, args=(d["sa"],))
        _celda(c[4], "Total", "act-total")
        _celda(c[5], _pct(d["total_sa"]), "act-num act-fuerte")
        _celda(c[6], _pct(1.0 if d["total_sa"] else 0.0), "act-num act-fuerte")


# ─────────────────────────────────────────────────────────────────────────────
# Cuadro 2 · Peso de las actividades dentro de cada indicador
# ─────────────────────────────────────────────────────────────────────────────
def _cuadro_pesos(d: dict) -> None:
    ss = st.session_state

    _titulo(2, "Peso de cada actividad en su indicador",
            "Solo se escribe la columna «Peso». Si un indicador se evalúa en varias "
            "actividades, su peso se reparte en proporción (pesos 2 y 1 → 66,67 % y 33,33 %); "
            "si prefieres trabajar en %, pon pesos que sumen 100. El factor es el que se pone en "
            "iDoceo o Additio.")
    _cabecera(2, ANCHOS_PESOS,
              ["Actividad", "Peso", "%", "% prog.", "% SA", "Factor"], desde_num=2)

    # Un bloque por indicador de la SA: su código, su texto y su instrumento
    # arriba y, debajo, una fila por cada actividad que lo evalúa.
    for n, r in enumerate(d["ils_sa"]):
        il = r["IL"]
        enlaces = d["enlaces"].get(il, [])        # [(actividad, enlace)] de este IL
        pendiente = il in d["pendientes"]

        with st.container(key=f"actil_{n}"):
            aviso = ""
            if not enlaces:
                aviso = '<span class="pa-tag warn">Sin actividad</span>'
            elif pendiente:
                aviso = '<span class="pa-tag warn">Faltan pesos</span>'
            _html(f'<div class="act-il-cab"><span class="act-il">{escape(il)}</span>'
                  f'<span class="act-il-txt">{escape(str(r.get("DIL") or ""))}</span>'
                  f'<span class="act-il-ie">{aviso} {_instrumento(r.get("IE"))}</span></div>')

            for a, enlace in enlaces:
                aid = a["id"]
                with st.container(key=f"actpeso_{aid}_{n}"):
                    c_act, c_peso, c_pct, c_prog, c_sa, c_fac = st.columns(
                        ANCHOS_PESOS, vertical_alignment="center")

                    _celda(c_act, _etiqueta_actividad(a, d["cod"], d["tono"])
                           + f' <span class="act-nombre">{escape(a.get("titulo") or "Sin nombre")}</span>')

                    clave = f"paact_pa_{aid}_{il}"
                    ss[clave] = None if enlace.get("PA") is None else float(enlace["PA"])
                    c_peso.number_input(
                        f"Peso de {d['cod'][aid]} en el indicador {il}", key=clave,
                        min_value=0.0, step=1.0, format="%g", placeholder="Peso",
                        label_visibility="collapsed",
                        on_change=_al_cambiar_peso, args=(aid, il),
                    )

                    parte = d["parte"].get((aid, il), 0.0)
                    valor = d["valor_enlace"].get((aid, il), 0.0)
                    _celda(c_pct, _pct(parte), "act-num act-fuerte")
                    _celda(c_prog, _pct(valor), "act-num")
                    _celda(c_sa, _pct(valor / d["total_sa"] if d["total_sa"] else 0.0), "act-num")
                    # Factor = PIL · parte del IL que se evalúa en esta actividad
                    factor = "?" if pendiente else _numero(float(r.get("PIL") or 0) * parte)
                    _celda(c_fac, factor, "act-num act-fuerte")


# ─────────────────────────────────────────────────────────────────────────────
# Cuadro 3 · Vista en el cuaderno (solo de consulta)
# ─────────────────────────────────────────────────────────────────────────────
def _cuadro_cuaderno(d: dict) -> None:
    """Una columna por actividad con los criterios (CE) que evalúa y el factor
    por el que se multiplica cada uno = Σ de los factores del cuadro 2 de sus
    indicadores de ese CE."""
    _titulo(3, "Vista en el cuaderno",
            "Así quedan las columnas de esta situación de aprendizaje en iDoceo o Additio: "
            "cada actividad con los criterios que evalúa y el factor de cada uno.")

    cabeceras, criterios, fondos = [], [], []
    for a in d["acts_sa"]:
        fondo, suave, franja, tinta = d["tono"][a["id"]]
        fondos.append(suave)

        factor_ce: dict[str, float | None] = {}   # CE → factor (None = faltan pesos)
        for e in a.get("ils", []):
            il = e["IL"]
            info = d["il_info"].get(il, {})
            ce = info.get("CE") or il.rsplit(".", 1)[0]
            if il in d["pendientes"]:
                factor_ce[ce] = None
            elif factor_ce.get(ce, 0) is not None:
                factor_ce[ce] = factor_ce.get(ce, 0) + (
                    float(info.get("PIL") or 0) * d["parte"].get((a["id"], il), 0))

        chips = "".join(
            f'<span class="ce warn" title="Faltan pesos">CE {escape(ce)}<span class="x">×</span>?</span>'
            if f is None else
            f'<span class="ce">CE {escape(ce)}<span class="x">×</span>{_numero(f)}</span>'
            for ce, f in factor_ce.items()
        ) or '<span class="vacio">Sin criterios</span>'

        colores = f"--bg:{fondo};--franja:{franja};--tinta:{tinta}"
        cabeceras.append(
            f'<th scope="col" class="act" style="{colores}"><div class="cab">'
            f'<div class="cod">{d["cod"][a["id"]]}</div>'
            f'<div class="tit">{escape(a.get("titulo") or "Sin nombre")}</div>'
            f'<div class="ie">{escape(a.get("IE") or "")}</div></div></th>'
        )
        criterios.append(f'<td class="act" style="{colores}"><div class="ces">{chips}</div></td>')

    alumnos = "".join(
        f'<tr><th scope="row" class="alum">Alumno/a {n}</th>'
        + "".join(f'<td class="cel" style="--soft:{s}"></td>' for s in fondos) + "</tr>"
        for n in (1, 2, 3)
    )
    _html(
        '<div class="cuad-wrap"><table class="cuad"><thead><tr>'
        '<th scope="col" rowspan="2" class="alum esq">Alumnado</th>' + "".join(cabeceras)
        + "</tr><tr>" + "".join(criterios)
        + f"</tr></thead><tbody>{alumnos}</tbody></table></div>"
    )
