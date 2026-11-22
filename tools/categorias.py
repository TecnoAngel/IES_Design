"""Categorías opcionales de los indicadores de logro (p. ej. «Destrezas»).

Cada departamento puede definir las categorías que quiera, cada una con su
lista de opciones, y asignar a cada indicador (como mucho) una opción por
categoría. Si no se define ninguna, nada de esto aparece ni se guarda.

Formato en sesión y en el estado de ``tools.proyecto``::

    categorias   [{"id": 1, "nombre": "Destrezas",
                   "opciones": [{"id": 2, "nombre": "Analizar"}, ...]}]
    fila["CAT"]  {id_categoria: id_opcion}      (en cada fila de ``il_rows``)

Se guardan **ids**, no nombres: renombrar una categoría u opción no toca las
asignaciones; borrar una opción las quita de los indicadores. Los ids son
únicos en todo el proyecto (categorías y opciones comparten contador) y no
cambian al reordenar. Todas las funciones devuelven datos nuevos.
"""

from __future__ import annotations


def _s(v) -> str:
    return "" if v is None else str(v).strip()


def siguiente_id(categorias: list[dict]) -> int:
    ids = [0]
    for c in categorias:
        ids.append(int(c["id"]))
        ids += [int(o["id"]) for o in c.get("opciones", [])]
    return max(ids) + 1


def normalizar(categorias) -> list[dict]:
    """Limpia lo que venga (de un archivo o de la sesión): ids enteros y únicos,
    nombres sin espacios sobrantes, sin opciones repetidas por nombre."""
    out: list[dict] = []
    usados: set[int] = set()
    for c in categorias or []:
        try:
            cid = int(c["id"])
        except (KeyError, TypeError, ValueError):
            continue
        if cid in usados:
            continue
        usados.add(cid)
        opciones, nombres = [], set()
        for o in c.get("opciones", []):
            try:
                oid = int(o["id"])
            except (KeyError, TypeError, ValueError):
                continue
            nombre = _s(o.get("nombre"))
            if oid in usados or not nombre or nombre.lower() in nombres:
                continue
            usados.add(oid)
            nombres.add(nombre.lower())
            opciones.append({"id": oid, "nombre": nombre})
        out.append({"id": cid, "nombre": _s(c.get("nombre")), "opciones": opciones})
    return out


def añadir_categoria(categorias: list[dict], nombre: str = "") -> list[dict]:
    return normalizar(categorias) + [
        {"id": siguiente_id(categorias), "nombre": _s(nombre), "opciones": []}
    ]


def añadir_opcion(categorias: list[dict], cat_id: int, nombre: str = "") -> list[dict]:
    nuevo = siguiente_id(categorias)
    out = []
    for c in categorias:
        c = {**c, "opciones": list(c.get("opciones", []))}
        if c["id"] == cat_id:
            c["opciones"].append({"id": nuevo, "nombre": _s(nombre)})
        out.append(c)
    return out


def quitar_categoria(categorias: list[dict], filas: list[dict], cat_id: int):
    """(categorías sin ella, filas sin esa asignación)."""
    return (
        [c for c in categorias if c["id"] != cat_id],
        [_con_cat(r, {k: v for k, v in (r.get("CAT") or {}).items() if int(k) != cat_id})
         for r in filas],
    )


def quitar_opcion(categorias: list[dict], filas: list[dict], opcion_id: int):
    """(categorías sin la opción, filas que la tenían puesta, ahora sin ella)."""
    cats = [
        {**c, "opciones": [o for o in c.get("opciones", []) if o["id"] != opcion_id]}
        for c in categorias
    ]
    return cats, [
        _con_cat(r, {k: v for k, v in (r.get("CAT") or {}).items() if int(v) != opcion_id})
        for r in filas
    ]


def _con_cat(fila: dict, cat: dict) -> dict:
    return {**fila, "CAT": cat}


def limpiar_filas(categorias: list[dict], filas: list[dict]) -> list[dict]:
    """Quita de las filas toda asignación a una categoría u opción que no
    existe (o cuya opción es de otra categoría)."""
    validas = {int(c["id"]): {int(o["id"]) for o in c.get("opciones", [])} for c in categorias}
    out = []
    for r in filas:
        cat = {}
        for k, v in (r.get("CAT") or {}).items():
            try:
                k, v = int(k), int(v)
            except (TypeError, ValueError):
                continue
            if v in validas.get(k, ()):
                cat[k] = v
        out.append(_con_cat(r, cat))
    return out


def columna(cat_id: int) -> str:
    """Nombre del campo de la rejilla para una categoría (el rótulo es su nombre)."""
    return f"cat_{cat_id}"


def nombre_de_opcion(categoria: dict, opcion_id) -> str:
    for o in categoria.get("opciones", []):
        if o["id"] == opcion_id:
            return o["nombre"]
    return ""


def id_de_opcion(categoria: dict, nombre) -> int | None:
    nombre = _s(nombre).lower()
    for o in categoria.get("opciones", []):
        if o["nombre"].lower() == nombre and nombre:
            return o["id"]
    return None


def tabla_por_niveles(il_rows, categorias, ce_p: dict) -> list[dict]:
    """Resumen jerárquico de los indicadores por categorías. El **orden** de las
    categorías son los niveles: la primera es el nivel 1 y cada una a su derecha
    subdivide la anterior; un indicador sin opción en una categoría se queda en
    el nivel anterior (si no tiene en ninguna, va a «Sin categoría»).

    Devuelve una lista (en orden de aparición) de grupos de nivel 1::

        {"nombre": "Reading", "peso": 15.0,
         "lineas": [{"sub": "", "peso": 10.0, "ce": ["1.2", ...]},
                    {"sub": "Readers", "peso": 5.0, "ce": ["6.2", ...]}]}

    ``peso`` en % de la programación (Σ de (PIL/ΣPIL del CE)·(P/ΣP) de sus
    indicadores, normalizado a 100). ``sub`` es el resto de niveles unidos con
    « · » (vacío = solo el nivel 1)."""
    from tools.ajuste_pesos import pesos_globales

    cats = [c for c in categorias or [] if _s(c.get("nombre"))]
    filas = [r for r in il_rows if _s(r.get("IL"))]
    w = pesos_globales(filas, ce_p)
    total = sum(w.values()) or 1.0
    nombres = [{o["id"]: _s(o["nombre"]) for o in c.get("opciones", [])} for c in cats]

    def clave(r):
        asign = r.get("CAT") or {}
        return tuple(nombres[i].get(asign.get(c["id"]), "") for i, c in enumerate(cats))

    def num(ce):
        return tuple(int(p) if p.isdigit() else 0 for p in ce.split("."))

    grupos: dict[str, dict] = {}
    for r in filas:
        k = clave(r)
        nivel1 = k[0] if k else ""
        sub = " · ".join(x for x in k[1:] if x)
        g = grupos.setdefault(nivel1 or "Sin categoría", {"lineas": {}})
        ln = g["lineas"].setdefault(sub, {"peso": 0.0, "ce": set()})
        ln["peso"] += w[_s(r["IL"])] / total * 100
        ln["ce"].add(_s(r.get("CE")))

    orden = [o["nombre"] for o in (cats[0].get("opciones", []) if cats else [])]
    claves = sorted(grupos, key=lambda n: (orden.index(n) if n in orden else len(orden), n))
    out = []
    for n in claves:
        lineas = [
            {"sub": s, "peso": round(v["peso"], 4), "ce": sorted(v["ce"], key=num)}
            for s, v in sorted(grupos[n]["lineas"].items(), key=lambda kv: (kv[0] != "", kv[0]))
        ]
        out.append({"nombre": n, "peso": round(sum(x["peso"] for x in lineas), 4), "lineas": lineas})
    return out
