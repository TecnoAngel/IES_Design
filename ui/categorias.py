"""Desplegable «Categorías de los indicadores (opcional)» de la pestaña
Indicadores de logro: el departamento define las categorías que quiera (p. ej.
«Destrezas») y las opciones de cada una; luego, en la rejilla de indicadores,
cada categoría es una columna con un desplegable con esas opciones.

Solo widgets de Streamlit. Los widgets se rellenan desde ``il_categorias`` en
cada ejecución y su ``on_change`` / ``on_click`` escribe en ella (mismo patrón
que ``ui/actividades.py``). Cualquier cambio cambia las columnas de la rejilla,
así que antes consolida lo que haya tecleado en ella y la remonta
(``il_nonce``). La lógica de datos está en ``tools/categorias.py``.
"""

from __future__ import annotations

import streamlit as st

from tools import categorias as cat


def pintar(recalcular) -> None:
    """``recalcular(filas)`` = ``il_recompute`` con el criterio de la materia."""
    ss = st.session_state
    cats = ss.get("il_categorias", [])

    def _filas() -> list[dict]:
        return list(ss.get("il_pending") or ss.get("il_rows", []))

    def _aplicar(nuevas: list[dict], filas: list[dict] | None = None) -> None:
        ss.il_categorias = nuevas
        ss.il_rows = recalcular(_filas() if filas is None else filas)
        ss.pop("il_pending", None)
        ss.il_nonce = ss.get("il_nonce", 0) + 1
        ss.pop("prog_out", None)

    def _renombrar_categoria(cid: int) -> None:
        txt = ss.get(f"ilcat_n_{cid}", "").strip()
        _aplicar([{**c, "nombre": txt} if c["id"] == cid else c for c in ss.il_categorias])

    def _renombrar_opcion(oid: int) -> None:
        txt = ss.get(f"ilcat_o_{oid}", "").strip()
        _aplicar([
            {**c, "opciones": [{**o, "nombre": txt} if o["id"] == oid else o for o in c["opciones"]]}
            for c in ss.il_categorias
        ])

    def _nueva_categoria() -> None:
        _aplicar(cat.añadir_categoria(ss.il_categorias, ""))

    def _nueva_opcion(cid: int) -> None:
        _aplicar(cat.añadir_opcion(ss.il_categorias, cid, ""))

    def _borrar_categoria(cid: int) -> None:
        nuevas, filas = cat.quitar_categoria(ss.il_categorias, _filas(), cid)
        _aplicar(nuevas, filas)

    def _borrar_opcion(oid: int) -> None:
        nuevas, filas = cat.quitar_opcion(ss.il_categorias, _filas(), oid)
        _aplicar(nuevas, filas)

    titulo = "Categorías de los indicadores (opcional)"
    nombres = [c["nombre"] for c in cats if c["nombre"]]
    if nombres:
        titulo += " · " + ", ".join(nombres)
    with st.expander(titulo, expanded=False):
        st.caption(
            "Para clasificar los indicadores como quiera el departamento (p. ej. una categoría "
            "«Destrezas» con sus opciones). Cada categoría pasa a ser una columna de la tabla de "
            "indicadores, con un desplegable con estas opciones. Si no defines ninguna, no "
            "aparece nada. Borrar una categoría o una opción la quita también de los "
            "indicadores que la tuvieran."
        )
        for c in cats:
            with st.container(border=True, key=f"ilcat_box_{c['id']}"):
                ss[f"ilcat_n_{c['id']}"] = c["nombre"]
                a, b = st.columns([6, 1])
                a.text_input(
                    "Categoría", key=f"ilcat_n_{c['id']}", placeholder="Nombre de la categoría",
                    on_change=_renombrar_categoria, args=(c["id"],),
                )
                b.markdown("<div style='height:1.7rem'></div>", unsafe_allow_html=True)
                b.button("Borrar", key=f"ilcat_bc_{c['id']}", on_click=_borrar_categoria,
                         args=(c["id"],), help="Borra la categoría y sus opciones")
                for o in c["opciones"]:
                    ss[f"ilcat_o_{o['id']}"] = o["nombre"]
                    x, y = st.columns([6, 1])
                    x.text_input(
                        "Opción", key=f"ilcat_o_{o['id']}", label_visibility="collapsed",
                        placeholder="Opción del desplegable",
                        on_change=_renombrar_opcion, args=(o["id"],),
                    )
                    y.button("🗑", key=f"ilcat_bo_{o['id']}", on_click=_borrar_opcion,
                             args=(o["id"],), help="Quitar esta opción")
                st.button("Añadir opción", key=f"ilcat_ao_{c['id']}", on_click=_nueva_opcion,
                          args=(c["id"],))
        st.button("Añadir categoría", key="ilcat_ac", on_click=_nueva_categoria)
