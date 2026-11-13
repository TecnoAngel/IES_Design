"""Página «Redacción» (Programación didáctica): una pestaña por capítulo.

Qué capítulos hay y qué lleva cada uno NO está aquí sino en
``tools/redaccion.py`` (lista ``CAPITULOS``): para añadir un párrafo o una
tabla a un capítulo se toca allí, y esta pantalla lo pinta sola.

Aquí está cómo se pinta cada tipo de elemento:

    pintar()                 ← lo llama app.py con las pestañas ya creadas
      └─ _capitulo()           título, «qué pide la guía» y sus elementos
           ├─ _texto()           párrafo que escribe el docente
           ├─ _tabla()           tabla de añadir y quitar filas
           ├─ _auto()            tabla que se genera sola (casilla «aparece»)
           └─ _grafica()         gráfica que se genera sola (casilla «aparece»)

Cómo funciona la edición (el mismo patrón que en ``ui/actividades.py``):

1. Todo vive en ``st.session_state.red``:
   ``{"textos": {clave: texto}, "tablas": {clave: [fila]}, "opciones": {clave: bool}}``.
   Eso es lo que se guarda en el proyecto.
2. Antes de pintar un campo se copia a su ``key`` (``redw_…``) lo que hay en
   ``red``; así el campo siempre enseña lo guardado.
3. Cuando el docente lo cambia, Streamlit llama a su ``on_change``
   (``_al_cambiar_…``), que escribe el valor nuevo en ``red`` y avisa de que
   hay cambios (``_tocado``).
"""

from __future__ import annotations

from html import escape
from typing import Callable

import streamlit as st

from tools import redaccion as red

MAX_FILAS_VISTA = 12  # filas que enseña la vista previa de una tabla automática

CSS = """
<style>
/* Tabla que rellena el docente */
[class*="st-key-redbox_tabla_"] {
    background: #fff; border: 1px solid var(--jcyl-line); border-radius: 8px;
    padding: 0.7rem 0.8rem 0.6rem 0.8rem; margin: 0.3rem 0 0.9rem 0;
    box-shadow: inset 0 3px 0 var(--jcyl-red);
}
/* Lo que se genera solo: tabla (crema) y gráfica (borde discontinuo) */
[class*="st-key-redbox_auto_"], [class*="st-key-redbox_grafica_"] {
    background: var(--jcyl-cream); border: 1px solid var(--jcyl-line); border-radius: 8px;
    padding: 0.55rem 0.8rem 0.5rem 0.8rem; margin: 0.3rem 0 0.9rem 0;
}
[class*="st-key-redbox_grafica_"] { border: 2px dashed #c9b8a3; }
[class*="st-key-redbox_"] [data-testid="stMarkdownContainer"] { margin-bottom: 0; }
.red-tit { font-weight: 700; font-size: 0.98rem; color: #2b2622; }
.red-ayuda { font-size: 0.85rem; color: #5c524a; margin-top: 0.1rem; }
.red-col {
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
    color: #5c524a;
}
.red-guia { font-size: 0.92rem; color: #3d352f; }
.red-vista { overflow-x: auto; }
.red-vista table { font-size: 0.78rem; }
/* Papelera de cada fila: discreta y a la altura de su campo */
[class*="st-key-redw_del_"] button { min-height: 2.4rem; padding: 0.2rem 0.5rem; }
</style>
"""


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------
def _tocado() -> None:
    """Algo ha cambiado: hay que volver a calcular el proyecto que se guarda
    y el Word ya generado deja de valer."""
    st.session_state.pop("prog_out", None)
    st.session_state.pop("pd_docx", None)


def _al_cambiar_texto(clave: str, key: str) -> None:
    st.session_state.red["textos"][clave] = st.session_state[key]
    _tocado()


def _al_cambiar_opcion(clave: str, key: str) -> None:
    st.session_state.red["opciones"][clave] = bool(st.session_state[key])
    _tocado()


def _al_cambiar_celda(clave: str, fila: int, columna: str, key: str) -> None:
    st.session_state.red["tablas"][clave][fila][columna] = st.session_state[key]
    _tocado()


def _anadir_fila(elem: dict) -> None:
    st.session_state.red["tablas"].setdefault(elem["clave"], []).append(red.fila_vacia(elem))
    _tocado()


def _quitar_fila(clave: str, fila: int) -> None:
    del st.session_state.red["tablas"][clave][fila]
    _tocado()


# ---------------------------------------------------------------------------
# Elementos
# ---------------------------------------------------------------------------
def _alto(texto: str) -> int:
    """Alto del cuadro de texto según lo que tiene escrito."""
    lineas = sum(1 + len(l) // 110 for l in (texto or "").split("\n"))
    return max(100, min(420, 40 + 24 * lineas))


def _texto(elem: dict) -> None:
    ss = st.session_state
    clave = elem["clave"]
    key = f"redw_t_{clave}"
    ss[key] = ss.red["textos"].get(clave, "")
    etiqueta = elem["etiqueta"]
    if elem.get("rotulo"):
        ayuda = (elem["ayuda"] + " " if elem["ayuda"] else "") + (
            f"En el documento va precedido del rótulo «{elem['rotulo']}:»."
        )
    else:
        ayuda = elem["ayuda"] or None
    comun = dict(key=key, help=ayuda, placeholder=elem["ayuda"] or "",
                 on_change=_al_cambiar_texto, args=(clave, key))
    if elem.get("corto"):
        st.text_input(etiqueta, **comun)
    else:
        st.text_area(etiqueta, height=_alto(ss[key]), **comun)


def _cabecera(elem: dict, tipo: str) -> None:
    st.markdown(
        f'<div class="red-tit">{escape(elem["etiqueta"])} '
        f'<span class="pa-tag info">{tipo}</span></div>'
        + (f'<div class="red-ayuda">{escape(elem["ayuda"])}</div>' if elem["ayuda"] else ""),
        unsafe_allow_html=True,
    )


def _tabla(elem: dict) -> None:
    ss = st.session_state
    clave = elem["clave"]
    filas = ss.red["tablas"].setdefault(clave, [])
    anchos = [c[1] for c in elem["columnas"]] + [0.45]
    with st.container(key=f"redbox_tabla_{clave}"):
        _cabecera(elem, "Tabla")
        if filas:
            cab = st.columns(anchos)
            for j, (nombre, _a, _l) in enumerate(elem["columnas"]):
                cab[j].markdown(f'<div class="red-col">{escape(nombre)}</div>', unsafe_allow_html=True)
        for i, fila in enumerate(filas):
            cols = st.columns(anchos)
            for j, (nombre, _a, largo) in enumerate(elem["columnas"]):
                key = f"redw_c_{clave}_{i}_{j}"
                ss[key] = fila.get(nombre, "")
                comun = dict(key=key, label_visibility="collapsed",
                             on_change=_al_cambiar_celda, args=(clave, i, nombre, key))
                if largo:
                    cols[j].text_area(nombre, height=_alto(ss[key]) if ss[key] else 68, **comun)
                else:
                    cols[j].text_input(nombre, **comun)
            cols[-1].button(":material/delete:", key=f"redw_del_{clave}_{i}", help="Quitar esta fila",
                            on_click=_quitar_fila, args=(clave, i))
        if not filas:
            st.caption("Sin filas: esta tabla no saldrá en el documento.")
        st.button("Añadir fila", key=f"redw_add_{clave}", icon=":material/add:",
                  on_click=_anadir_fila, args=(elem,))


def _casilla(elem: dict, texto: str) -> bool:
    ss = st.session_state
    clave = elem["clave"]
    key = f"redw_o_{clave}"
    ss[key] = bool(ss.red["opciones"].get(clave, elem["activo"]))
    return st.checkbox(texto, key=key, on_change=_al_cambiar_opcion, args=(clave, key))


def _vista_tabla(headers: list[str], rows: list[list[str]]) -> str:
    from tools.situaciones_informe import render_word_table_html

    resto = len(rows) - MAX_FILAS_VISTA
    html = render_word_table_html(headers, rows[:MAX_FILAS_VISTA])
    pie = f'<div class="red-ayuda">… y {resto} filas más.</div>' if resto > 0 else ""
    return f'<div class="red-vista">{html}</div>{pie}'


def _auto(elem: dict, datos: Callable[[], dict]) -> None:
    with st.container(key=f"redbox_auto_{elem['clave']}"):
        _cabecera(elem, "Se genera sola")
        _casilla(elem, "Aparece en el documento")
        with st.expander("Ver cómo queda"):
            headers, rows = red.tabla_auto(elem["clave"], datos())
            if rows:
                st.markdown(_vista_tabla(headers, rows), unsafe_allow_html=True)
            else:
                st.caption("Todavía no hay datos en «Diseño de la programación» para generarla.")


def _grafica(elem: dict, datos: Callable[[], dict]) -> None:
    clave = elem["clave"]
    with st.container(key=f"redbox_grafica_{clave}"):
        _cabecera(elem, "Aquí va una gráfica")
        c1, c2 = st.columns([1, 1])
        with c1:
            _casilla(elem, "Aparece esta gráfica en el documento")
        # La gráfica solo se dibuja si se pide verla (tarda un poco).
        if c2.toggle("Ver la gráfica", key=f"redw_v_{clave}"):
            png = red.grafica_png(clave, datos())
            if png:
                st.image(png, width=560)
            else:
                st.caption("Todavía no hay datos en «Diseño de la programación» para dibujarla.")


# ---------------------------------------------------------------------------
# Capítulo y página
# ---------------------------------------------------------------------------
def _capitulo(cap: dict, etapa: str, datos: Callable[[], dict]) -> None:
    ss = st.session_state
    elems = red.elementos(cap, etapa)
    vacios = sum(
        1 for e in elems
        if e["tipo"] == "texto" and not str(ss.red["textos"].get(e["clave"], "")).strip()
    )
    estado = (
        f'<span class="pa-tag warn">{vacios} texto{"s" if vacios != 1 else ""} sin rellenar</span>'
        if vacios else '<span class="pa-tag ok">Textos rellenos</span>'
    )
    st.markdown(
        f'<div class="pa-sec" role="heading" aria-level="3">{escape(cap["titulo"])} {estado}</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Qué pide la guía de la Junta en este apartado"):
        st.markdown(f'<div class="red-guia">{escape(cap["guia"])}</div>', unsafe_allow_html=True)
    for e in elems:
        if e["tipo"] == "texto":
            _texto(e)
        elif e["tipo"] == "tabla":
            _tabla(e)
        elif e["tipo"] == "auto":
            _auto(e, datos)
        else:
            _grafica(e, datos)


def pintar(pestanas, preparar_datos: Callable[[], dict]) -> None:
    """``pestanas``: una por capítulo de ``red.CAPITULOS``, en su orden.
    ``preparar_datos``: función que devuelve ``red.preparar(...)`` con lo que
    hay ahora en «Diseño de la programación» (solo se llama si hace falta)."""
    ss = st.session_state
    etapa = red.etapa_app(ss.proy_materia)
    cache: dict = {}

    def datos() -> dict:
        if "d" not in cache:
            cache["d"] = preparar_datos()
        return cache["d"]

    st.markdown(CSS, unsafe_allow_html=True)
    for cap, pestana in zip(red.CAPITULOS, pestanas):
        with pestana:
            if pestana.open:
                _capitulo(cap, etapa, datos)
