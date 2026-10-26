"""Indicadores de logro (IL): cálculos sobre las filas en sesión.

Cada IL tiene:

    CE   criterio de evaluación (p.ej. "4.2")   -> de los criterios de la materia (curriculo.db)
    CED  descripción del criterio               -> automático (lookup por CE)
    IL   indicador de logro ("4.2.1", "4.2.2")  -> automático, correlativo dentro del CE
    PIL  peso del indicador                     -> a mano (número)
    PIL% PIL / Σ PIL del mismo CE               -> automático
    DIL  descripción del indicador              -> a mano
    DO   descriptores operativos                -> ticks (los del CE en curriculo.db)
    CON  contenidos de la materia               -> ticks (curriculo.db)
    CT   contenidos transversales               -> ticks (curriculo.db, de la etapa)
    IE   instrumento de evaluación              -> catálogo (curriculo.db)
    CC   criterio de calificación               -> catálogo (curriculo.db)
    AE   agente evaluador                       -> catálogo (curriculo.db)
    SA   situación de aprendizaje               -> las SA del proyecto

Los cálculos replican las tablas dinámicas / medidas DAX que tenía el antiguo
Excel de programación (hojas INFORMES y RESUMEN).
"""

from __future__ import annotations

import re
from typing import Any

COLUMNS = ["CE", "CED", "IL", "PIL", "PIL%", "DIL", "DO", "CON", "CT", "IE", "CC", "AE", "SA"]


def _s(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _split_tokens(value: Any) -> list[str]:
    """Divide "A.1.1, A 1 2 ,B.3.1" en ['A.1.1', 'A.1.2', 'B.3.1'] (espacios
    internos -> puntos, como hace la hoja RESUMEN con SUBSTITUTE)."""
    out = []
    for tok in str(value or "").split(","):
        tok = re.sub(r"\s+", ".", tok.strip()).strip(".")
        if tok:
            out.append(tok)
    return out


def _norm_token(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def usados_en_il(rows: list[dict], field: str) -> set[str]:
    """Conjunto de códigos (sin espacios) que aparecen en la columna `field`
    (``CON`` o ``CT``) de algún indicador de logro. Réplica del check que hace
    el formato condicional de la hoja LOMLOE."""
    out: set[str] = set()
    for r in rows:
        for tok in str(r.get(field) or "").split(","):
            tok = _norm_token(tok)
            if tok:
                out.add(tok)
    return out


def matriz_sa_ce(
    rows: list[dict],
    ce_list: list[str],
    ce_p: dict[str, float] | None = None,
) -> dict:
    """Réplica de la tabla dinámica "DISTRIBUCIÓN DE PORCENTAJES POR CRITERIOS DE
    EVALUACIÓN Y SITUACIONES DE APRENDIZAJE" de la hoja INFORMES.

    Para cada indicador de logro, su peso sobre TODA la programación es
    ``(PIL / ΣPIL del CE) × (P del CE / ΣP)``. La matriz agrupa esos pesos por
    (SA, CE). Los totales por fila dan el peso de cada SA según los IL asignados.
    """
    ce_p = ce_p or {}
    total_p = sum(ce_p.values())

    sum_pil: dict[str, float] = {}
    for r in rows:
        ce = _s(r.get("CE"))
        pil = r.get("PIL")
        pil = 0.0 if pil in (None, "") else float(pil)
        sum_pil[ce] = sum_pil.get(ce, 0.0) + pil

    matrix: dict[tuple[int, str], float] = {}
    sa_set: set[int] = set()
    for r in rows:
        ce = _s(r.get("CE"))
        sa = r.get("SA")
        if sa in (None, "") or not ce:
            continue
        sa = int(sa)
        pil = r.get("PIL")
        pil = 0.0 if pil in (None, "") else float(pil)
        spil = sum_pil.get(ce, 0.0)
        pce = ce_p.get(ce, 0.0)
        w = (pil / spil if spil else 0.0) * (pce / total_p if total_p else 0.0)
        matrix[(sa, ce)] = matrix.get((sa, ce), 0.0) + w
        sa_set.add(sa)

    sa_rows = sorted(sa_set)
    ce_cols = [c for c in ce_list if c in sum_pil] or list(sum_pil.keys())
    sa_total = {sa: sum(matrix.get((sa, c), 0.0) for c in ce_cols) for sa in sa_rows}
    ce_total = {c: sum(matrix.get((sa, c), 0.0) for sa in sa_rows) for c in ce_cols}
    grand = sum(sa_total.values())
    return {
        "matrix": matrix,
        "sa_rows": sa_rows,
        "ce_cols": ce_cols,
        "sa_total": sa_total,
        "ce_total": ce_total,
        "grand_total": grand,
    }


def peso_por_ie(rows: list[dict], ce_p: dict[str, float] | None = None) -> list[tuple[str, float]]:
    """Peso acumulado por instrumento de evaluación (IE), como la dinámica
    ``Medida_porcentajes_IE`` de INFORMES: para cada IL su peso sobre toda la
    programación (``PIL%_CE · %CE``), sumado por IE. Ordenado de mayor a menor."""
    ce_p = ce_p or {}
    total_p = sum(ce_p.values())
    sum_pil_ce: dict[str, float] = {}
    for r in rows:
        sum_pil_ce[_s(r.get("CE"))] = sum_pil_ce.get(_s(r.get("CE")), 0.0) + float(r.get("PIL") or 0)

    por_ie: dict[str, float] = {}
    for r in rows:
        ie = _s(r.get("IE"))
        if not ie:
            continue
        ce = _s(r.get("CE"))
        spil = sum_pil_ce.get(ce, 0.0)
        pce = ce_p.get(ce, 0.0)
        w = (float(r.get("PIL") or 0) / spil if spil else 0.0) * (pce / total_p if total_p else 0.0)
        por_ie[ie] = por_ie.get(ie, 0.0) + w
    return sorted(por_ie.items(), key=lambda kv: -kv[1])


def resumen_por_ce(
    rows: list[dict],
    ce_list: list[str],
    ce_ced: dict[str, str],
    ce_p: dict[str, float] | None = None,
) -> list[dict]:
    """Resumen por criterio de evaluación, equivalente a la hoja RESUMEN:
    por cada CE, su %CE (P/ΣP), y la lista única de contenidos (CON), CT y SA
    de todos sus indicadores de logro."""
    ce_p = ce_p or {}
    total_p = sum(ce_p.values())

    por_ce: dict[str, dict] = {}
    orden: list[str] = []
    for r in rows:
        ce = _s(r.get("CE"))
        if not ce:
            continue
        if ce not in por_ce:
            por_ce[ce] = {"CON": [], "CT": [], "SA": [], "IL": []}
            orden.append(ce)
        d = por_ce[ce]
        d["CON"] += _split_tokens(r.get("CON"))
        d["CT"] += _split_tokens(r.get("CT"))
        if r.get("SA") not in (None, ""):
            d["SA"].append(str(int(r["SA"])) if isinstance(r["SA"], (int, float)) else str(r["SA"]))
        if _s(r.get("IL")):
            d["IL"].append(_s(r["IL"]))

    secuencia = [c for c in ce_list if c in por_ce] + [c for c in orden if c not in ce_list]

    def _uniq(seq):
        return list(dict.fromkeys(seq))

    out = []
    for ce in secuencia:
        d = por_ce[ce]
        p = ce_p.get(ce, 0.0)
        out.append(
            {
                "CE": ce,
                "CED": ce_ced.get(ce, ""),
                "pct": (p / total_p) if total_p else 0.0,
                "IL": ", ".join(_uniq(d["IL"])),
                "CONTENIDOS": ", ".join(_uniq(d["CON"])),
                "CT": ", ".join(_uniq(d["CT"])),
                "SA": ", ".join(_uniq(d["SA"])),
            }
        )
    return out


def recompute(
    rows: list[dict],
    ce_ced: dict[str, str],
    ce_order: list[str] | None = None,
) -> list[dict]:
    """Agrupa las filas por CE (en el orden de `ce_order`, o de aparición si no se
    pasa), rellena CED (lookup por CE), numera IL correlativo dentro de cada CE
    (4.2.1, 4.2.2…) y calcula PIL% = PIL / ΣPIL del CE.

    Al agrupar por CE, una fila nueva de "3.2" se coloca junto a las demás de
    "3.2" y recibe el siguiente número (3.2.4, 3.2.5…); dentro de un mismo CE se
    respeta el orden en que estaban las filas."""
    limpio = [r for r in rows if _row_has_content(r)]

    orden = list(ce_order or [])
    rank_cache: dict[str, int] = {}

    def _rank(ce: str) -> int:
        if ce in rank_cache:
            return rank_cache[ce]
        if ce in orden:
            rank_cache[ce] = orden.index(ce)
        elif ce:
            rank_cache[ce] = len(orden) + len(rank_cache)
        else:
            rank_cache[ce] = 10**9  # filas sin CE, al final
        return rank_cache[ce]

    # sorted() es estable: dentro de un mismo CE se mantiene el orden previo.
    limpio = sorted(limpio, key=lambda r: _rank(_s(r.get("CE"))))

    contador: dict[str, int] = {}
    suma_pil: dict[str, float] = {}
    for r in limpio:
        ce = _s(r.get("CE"))
        pil = r.get("PIL")
        pil = 1 if pil in (None, "") else pil
        try:
            suma_pil[ce] = suma_pil.get(ce, 0.0) + float(pil)
        except (TypeError, ValueError):
            pass

    out: list[dict] = []
    for r in limpio:
        ce = _s(r.get("CE"))
        pil = r.get("PIL")
        pil = 1 if pil in (None, "") else pil
        contador[ce] = contador.get(ce, 0) + 1
        try:
            pil_f = float(pil)
        except (TypeError, ValueError):
            pil_f = 0.0
        total = suma_pil.get(ce, 0.0)
        out.append(
            {
                **r,
                "CE": ce,
                "CED": ce_ced.get(ce, _s(r.get("CED"))),
                "IL": f"{ce}.{contador[ce]}" if ce else "",
                "PIL": pil,
                "PIL%": (pil_f / total) if total else 0.0,
            }
        )
    return out


def _row_has_content(r: dict) -> bool:
    return any(
        _s(r.get(c)) for c in ("CE", "DIL", "DO", "CON", "CT", "IE", "CC", "AE")
    ) or r.get("PIL") not in (None, "") or r.get("SA") not in (None, "")
