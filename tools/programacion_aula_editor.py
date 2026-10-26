"""Actividades de la programación de aula: cálculos sobre las filas en sesión.

Cada actividad pertenece a un indicador de logro (``IL``) y tiene descripción
(``DA``) y peso (``PA``); el código ``A`` (``<IL>.n``), ``PA%`` y ``FACTOR`` se
calculan. Los valores sobre la programación y sobre la SA replican la tabla
dinámica que tenía el antiguo Excel de programación (hoja INFORMES).
"""

from __future__ import annotations

from typing import Any


def _s(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _num(v: Any):
    if v in (None, ""):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return int(f) if f.is_integer() else f


def recompute_actividades(rows: list[dict], pil_por_il: dict[str, float]) -> list[dict]:
    """Numera el código A por IL (``<IL>.1``, ``<IL>.2``…) y calcula PA%
    (PA / ΣPA del IL) y FACTOR_IDOCEO (PIL·PA%). Agrupa las filas por IL en el
    orden en que aparece cada IL."""
    limpio = [
        r for r in rows
        if _s(r.get("IL")) or _s(r.get("DA")) or r.get("PA") not in (None, "")
    ]
    orden_il = list(dict.fromkeys(_s(r.get("IL")) for r in limpio if _s(r.get("IL"))))
    rank = {il: i for i, il in enumerate(orden_il)}
    limpio = sorted(limpio, key=lambda r: rank.get(_s(r.get("IL")), 10**9))

    suma_pa: dict[str, float] = {}
    for r in limpio:
        il = _s(r.get("IL"))
        pa = _num(r.get("PA")) or 0
        suma_pa[il] = suma_pa.get(il, 0.0) + float(pa)

    cont: dict[str, int] = {}
    out = []
    for r in limpio:
        il = _s(r.get("IL"))
        pa = _num(r.get("PA"))
        cont[il] = cont.get(il, 0) + 1
        total = suma_pa.get(il, 0.0)
        if pa is None:
            pa_pct = None
            factor = None
        else:
            pa_pct = (float(pa) / total) if total else 0.0
            factor = pil_por_il.get(il, 0.0) * pa_pct
        out.append(
            {
                "IL": il,
                "A": f"{il}.{cont[il]}" if il else "",
                "DA": _s(r.get("DA")),
                "PA": pa,
                "PA%": pa_pct,
                "FACTOR": factor,
            }
        )
    return out


def valores_actividades(
    acts: list[dict],
    il_rows: list[dict],
    ce_p: dict[str, float],
) -> list[dict]:
    """Replica la tabla dinámica "DISTRIBUCIÓN DE PORCENTAJES ACTIVIDADES Y
    SITUACIÓN DE APRENDIZAJE" de INFORMES.

    ``valor sobre la programación`` de una actividad =
    ``(PA / ΣPA del IL) · (PIL / ΣPIL del CE) · (P del CE / ΣP)``.
    ``valor sobre la SA`` = ese valor / Σ de los valores de las actividades de la
    misma situación de aprendizaje.
    """
    il_ce = {r["IL"]: _s(r.get("CE")) for r in il_rows}
    il_pil = {r["IL"]: float(r.get("PIL") or 0) for r in il_rows}
    il_sa = {r["IL"]: r.get("SA") for r in il_rows}
    sum_pil_ce: dict[str, float] = {}
    for r in il_rows:
        sum_pil_ce[_s(r.get("CE"))] = sum_pil_ce.get(_s(r.get("CE")), 0.0) + float(r.get("PIL") or 0)
    total_p = sum(ce_p.values())

    rc = recompute_actividades(acts, il_pil)
    for a in rc:
        il = a["IL"]
        ce = il_ce.get(il, "")
        spil = sum_pil_ce.get(ce, 0.0)
        pce = ce_p.get(ce, 0.0)
        a["SA"] = il_sa.get(il)
        a["valor_prog"] = (
            (a["PA%"] or 0.0)
            * (il_pil.get(il, 0.0) / spil if spil else 0.0)
            * (pce / total_p if total_p else 0.0)
        )
    total_por_sa: dict = {}
    for a in rc:
        total_por_sa[a["SA"]] = total_por_sa.get(a["SA"], 0.0) + a["valor_prog"]
    for a in rc:
        t = total_por_sa.get(a["SA"], 0.0)
        a["valor_sa"] = (a["valor_prog"] / t) if t else 0.0
    return rc
