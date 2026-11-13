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
ANCHOS_ACTIVIDADES = [0.55,   3.6,    0.45,   3.4, 1.8,         1.0,    1.0]
#              IL   instrumento  actividad  peso  %    % prog  % SA  factor
ANCHOS_PESOS = [2.6, 1.6,         2.8,       1.1,  0.9, 1.0,    1.0,  1.0]

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

# Estilos propios de esta pestaña (las etiquetas .pa-tag, los títulos .pa-sec
# y la tabla .cuad del cuaderno están en el CSS general de app.py).
CSS = """
<style>
.act-cab  { font-size: 0.74rem; font-weight: 700; color: #5c524a;
            text-transform: uppercase; letter-spacing: 0.05em; }
.act-num  { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.act-total { font-weight: 700; }
.act-cod  { display: inline-block; min-width: 2.3rem; text-align: center; font-weight: 700;
            font-size: 0.9rem; border-radius: 6px; padding: 0.1rem 0.4rem; border: 1px solid; }
.act-il   { font-weight: 700; }
.act-desc { font-size: 0.8rem; color: #5c524a; line-height: 1.25; }
.act-raya { border-top: 1px solid #eadfd2; margin: 0.1rem 0 0.5rem 0; }
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


def _cabecera(anchos: list[float], titulos: list[str], desde_num: int) -> None:
    """Fila de títulos de un cuadro; las columnas desde `desde_num` son
    numéricas y van alineadas a la derecha."""
    for i, (col, titulo) in enumerate(zip(st.columns(anchos), titulos)):
        _celda(col, titulo, "act-cab act-num" if i >= desde_num else "act-cab")
    _html('<div class="act-raya"></div>')


def _titulo(texto: str, sub: str) -> None:
    _html(f'<div class="pa-sec" style="margin-top:0">{escape(texto)}</div>'
          f'<div class="pa-sec-sub">{escape(sub)}</div>')


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

    with st.container(border=True):
        _cuadro_actividades(d)
    with st.container(border=True):
        _cuadro_pesos(d)
    with st.container(border=True):
        _cuadro_cuaderno(d)


# ─────────────────────────────────────────────────────────────────────────────
# Cuadro 1 · Actividades
# ─────────────────────────────────────────────────────────────────────────────
def _cuadro_actividades(d: dict) -> None:
    ss = st.session_state
    il_info = d["il_info"]
    _titulo("1 · Actividades",
            "Pon nombre a cada actividad y elige el indicador que evalúa (pueden ser varios "
            "si comparten instrumento; su texto está en el cuadro 2). El instrumento es el del "
            "indicador. «% prog.» y «% SA»: valor sobre la programación y sobre la situación "
            "de aprendizaje.")
    _cabecera(ANCHOS_ACTIVIDADES,
              ["", "Actividad", "", "Indicador de logro", "Instrumento",
               "% prog.", "% SA"], desde_num=5)

    for a in d["acts_sa"]:
        aid = a["id"]
        elegidos = [e["IL"] for e in a.get("ils", [])]
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

        # Indicadores que se ofrecen: todos los de la SA si aún no hay ninguno
        # elegido; si ya hay, solo los del mismo instrumento.
        if elegidos:
            opciones = [r["IL"] for r in d["ils_sa"] if str(r.get("IE") or "") == str(a.get("IE") or "")]
            opciones += [il for il in elegidos if il not in opciones]
        else:
            opciones = [r["IL"] for r in d["ils_sa"]]
        ss[f"paact_ils_{aid}"] = elegidos
        c_il.multiselect(
            "Indicador de logro", opciones, key=f"paact_ils_{aid}",
            placeholder="Elige el indicador",
            label_visibility="collapsed",
            on_change=_al_cambiar_actividad, args=(aid, il_info),
        )

        if not elegidos:
            _celda(c_ie, '<span class="pa-tag warn">Sin indicador</span>')
        else:
            _celda(c_ie, escape(a.get("IE") or "—"))
        valor = d["valor_act"][aid]
        _celda(c_prog, _pct(valor["valor_prog"]), "act-num")
        _celda(c_sa, _pct(valor["valor_sa"]), "act-num")

    # Fila de totales
    _html('<div class="act-raya"></div>')
    c = st.columns(ANCHOS_ACTIVIDADES, vertical_alignment="center")
    c[1].button("Añadir actividad", key=f"paact_add_{d['sa']}", icon=":material/add:",
                on_click=_anadir_actividad, args=(d["sa"],))
    _celda(c[4], "Total", "act-total")
    _celda(c[5], _pct(d["total_sa"]), "act-num act-total")
    _celda(c[6], _pct(1.0 if d["total_sa"] else 0.0), "act-num act-total")


# ─────────────────────────────────────────────────────────────────────────────
# Cuadro 2 · Peso de las actividades dentro de cada indicador
# ─────────────────────────────────────────────────────────────────────────────
def _cuadro_pesos(d: dict) -> None:
    ss = st.session_state

    _titulo("2 · Peso de cada actividad en su indicador",
            "Solo se escribe la columna «Peso». Si un indicador se evalúa en varias "
            "actividades, su peso se reparte en proporción (pesos 2 y 1 → 66,67 % y 33,33 %); "
            "si prefieres trabajar en %, pon pesos que sumen 100. El factor es el que se pone "
            "en iDoceo o Additio.")
    _cabecera(ANCHOS_PESOS,
              ["Indicador de logro", "Instrumento", "Actividad", "Peso", "%",
               "% prog.", "% SA", "Factor"], desde_num=4)

    for n, r in enumerate(d["ils_sa"]):
        il = r["IL"]
        enlaces = d["enlaces"].get(il, [])        # [(actividad, enlace)] de este IL
        pendiente = il in d["pendientes"]
        if n:
            _html('<div class="act-raya"></div>')

        desc = str(r.get("DIL") or "")
        celda_il = (f'<span class="act-il">{escape(il)}</span>'
                    + (' <span class="pa-tag warn">Faltan pesos</span>' if pendiente else "")
                    + f'<div class="act-desc" title="{escape(desc)}">'
                    + escape(desc[:90] + "…" if len(desc) > 90 else desc) + "</div>")

        if not enlaces:  # indicador que aún no evalúa ninguna actividad
            c = st.columns(ANCHOS_PESOS, vertical_alignment="center")
            _celda(c[0], celda_il)
            _celda(c[1], escape(str(r.get("IE") or "—")))
            _celda(c[2], '<span class="pa-tag warn">Sin actividad</span>')
            continue

        for i, (a, enlace) in enumerate(enlaces):
            aid = a["id"]
            c_il, c_ie, c_act, c_peso, c_pct, c_prog, c_sa, c_fac = st.columns(
                ANCHOS_PESOS, vertical_alignment="center")
            if i == 0:  # el indicador y su instrumento, solo en su primera fila
                _celda(c_il, celda_il)
                _celda(c_ie, escape(str(r.get("IE") or "—")))

            _celda(c_act, _etiqueta_actividad(a, d["cod"], d["tono"]) + " "
                   + escape(a.get("titulo") or "Sin nombre"))

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
            _celda(c_pct, _pct(parte), "act-num act-total")
            _celda(c_prog, _pct(valor), "act-num")
            _celda(c_sa, _pct(valor / d["total_sa"] if d["total_sa"] else 0.0), "act-num")
            # Factor = PIL · parte del IL que se evalúa en esta actividad
            factor = "?" if pendiente else _numero(float(r.get("PIL") or 0) * parte)
            _celda(c_fac, factor, "act-num act-total")


# ─────────────────────────────────────────────────────────────────────────────
# Cuadro 3 · Vista en el cuaderno (solo de consulta)
# ─────────────────────────────────────────────────────────────────────────────
def _cuadro_cuaderno(d: dict) -> None:
    """Una columna por actividad con los criterios (CE) que evalúa y el factor
    por el que se multiplica cada uno = Σ de los factores del cuadro 2 de sus
    indicadores de ese CE."""
    _titulo("3 · Vista en el cuaderno",
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
