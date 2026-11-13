"""Actividades de la programación de aula: cálculos sobre las actividades en sesión.

Una actividad pertenece a una situación de aprendizaje (``SA``) y a un
instrumento de evaluación (``IE``), tiene título y evalúa uno o varios
indicadores de logro de esa SA con ese instrumento::

    {"id": 3, "SA": 2, "IE": "Rúbrica", "titulo": "...",
     "ils": [{"IL": "2.1.1", "PA": None}, {"IL": "2.3.1", "PA": 50.0}]}

``PA`` es el **peso** de esa actividad dentro del indicador. Si el indicador
solo está en una actividad, cuenta el 100 % y ``PA`` da igual; si está en
varias, el docente pone un peso a cada una y la parte de cada actividad es
``PA / ΣPA`` (quien prefiera trabajar en % pone pesos que sumen 100). ``PA``
vacío = sin peso todavía: mientras tanto cuenta como la media de los demás.
Los valores sobre la programación y sobre la SA replican la tabla dinámica que
tenía el antiguo Excel de programación (hoja INFORMES).
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


def nuevo_id(acts: list[dict]) -> int:
    return max((int(a.get("id") or 0) for a in acts), default=0) + 1


def enlaces_por_il(acts: list[dict]) -> dict[str, list[tuple[dict, dict]]]:
    """``{IL: [(actividad, enlace), ...]}`` en el orden de las actividades."""
    out: dict[str, list[tuple[dict, dict]]] = {}
    for a in acts:
        for e in a.get("ils", []):
            il = _s(e.get("IL"))
            if il:
                out.setdefault(il, []).append((a, e))
    return out


def fraccion_por_enlace(acts: list[dict]) -> dict[tuple[int, str], float]:
    """``{(id de actividad, IL): fracción del IL que se evalúa en ella}``
    (las de cada IL suman 1). Fracción = peso / suma de pesos del IL; un peso
    vacío cuenta como la media de los que sí están puestos (1 si no hay)."""
    out: dict[tuple[int, str], float] = {}
    for il, enlaces in enlaces_por_il(acts).items():
        pas = [_num(e.get("PA")) for _a, e in enlaces]
        puestos = [float(p) for p in pas if p is not None]
        relleno = sum(puestos) / len(puestos) if puestos else 1.0
        w = [float(p) if p is not None else relleno for p in pas]
        total = sum(w)
        for (a, _e), x in zip(enlaces, w):
            out[(a["id"], il)] = (x / total) if total else 1.0 / len(enlaces)
    return out


def reparto_pendiente(acts: list[dict]) -> list[str]:
    """IL que están en varias actividades y a los que aún les falta algún peso."""
    return [
        il for il, enlaces in enlaces_por_il(acts).items()
        if len(enlaces) > 1 and any(_num(e.get("PA")) is None for _a, e in enlaces)
    ]


def repartir_iguales(acts: list[dict], ils: list[str] | None = None) -> list[dict]:
    """Reparte a partes iguales (peso 1 a cada actividad) los IL indicados
    (por defecto, los pendientes)."""
    objetivo = set(reparto_pendiente(acts) if ils is None else ils)
    nuevas = [dict(a, ils=[dict(e) for e in a.get("ils", [])]) for a in acts]
    for il, enlaces in enlaces_por_il(nuevas).items():
        if il in objetivo and len(enlaces) > 1:
            for _a, e in enlaces:
                e["PA"] = 1
    return nuevas


def enlaces_invalidos(acts: list[dict], il_rows: list[dict]) -> list[tuple[dict, str, str]]:
    """``[(actividad, IL, motivo)]`` de los enlaces a un IL que no existe o que
    no es de la SA / del instrumento de la actividad."""
    info = {_s(r.get("IL")): r for r in il_rows if _s(r.get("IL"))}
    out = []
    for a in acts:
        for e in a.get("ils", []):
            il = _s(e.get("IL"))
            r = info.get(il)
            if r is None:
                out.append((a, il, "no existe"))
            elif _num(r.get("SA")) != _num(a.get("SA")):
                out.append((a, il, "es de otra situación de aprendizaje"))
            elif _s(r.get("IE")) != _s(a.get("IE")):
                out.append((a, il, "se evalúa con otro instrumento"))
    return out


def quitar_enlaces_invalidos(acts: list[dict], il_rows: list[dict]) -> list[dict]:
    malos = {(a["id"], il) for a, il, _m in enlaces_invalidos(acts, il_rows)}
    return [
        dict(a, ils=[e for e in a.get("ils", []) if (a["id"], _s(e.get("IL"))) not in malos])
        for a in acts
    ]


def codigos(acts: list[dict]) -> dict[int, str]:
    """Código de cada actividad, correlativo dentro de su SA: ``A1``, ``A2``…"""
    cont: dict = {}
    out = {}
    for a in acts:
        cont[a.get("SA")] = cont.get(a.get("SA"), 0) + 1
        out[a["id"]] = f"A{cont[a.get('SA')]}"
    return out


def valores_enlaces(
    acts: list[dict],
    il_rows: list[dict],
    ce_p: dict[str, float],
) -> dict[tuple[int, str], float]:
    """``{(id de actividad, IL): valor sobre la programación}`` de cada IL en
    cada actividad =
    ``(parte del IL en la actividad) · (PIL / ΣPIL del CE) · (P del CE / ΣP)``."""
    il_ce = {r["IL"]: _s(r.get("CE")) for r in il_rows}
    il_pil = {r["IL"]: float(r.get("PIL") or 0) for r in il_rows}
    sum_pil_ce: dict[str, float] = {}
    for r in il_rows:
        sum_pil_ce[_s(r.get("CE"))] = sum_pil_ce.get(_s(r.get("CE")), 0.0) + float(r.get("PIL") or 0)
    total_p = sum(ce_p.values())
    out = {}
    for (aid, il), parte in fraccion_por_enlace(acts).items():
        ce = il_ce.get(il, "")
        spil = sum_pil_ce.get(ce, 0.0)
        out[(aid, il)] = (
            parte
            * (il_pil.get(il, 0.0) / spil if spil else 0.0)
            * (ce_p.get(ce, 0.0) / total_p if total_p else 0.0)
        )
    return out


def valores_actividades(
    acts: list[dict],
    il_rows: list[dict],
    ce_p: dict[str, float],
) -> list[dict]:
    """Replica la tabla dinámica "DISTRIBUCIÓN DE PORCENTAJES ACTIVIDADES Y
    SITUACIÓN DE APRENDIZAJE" de INFORMES, ahora con actividades que evalúan
    varios IL.

    ``valor sobre la programación`` de una actividad = Σ de sus IL (ver
    ``valores_enlaces``). ``valor sobre la SA`` = ese valor / Σ de los valores
    de las actividades de la misma situación de aprendizaje.
    """
    por_enlace = valores_enlaces(acts, il_rows, ce_p)
    cod = codigos(acts)

    out = []
    for a in acts:
        valor = sum(por_enlace.get((a["id"], _s(e.get("IL"))), 0.0) for e in a.get("ils", []))
        out.append({
            "id": a["id"], "SA": a.get("SA"), "A": cod[a["id"]],
            "titulo": _s(a.get("titulo")), "IE": _s(a.get("IE")),
            "ILs": ", ".join(_s(e.get("IL")) for e in a.get("ils", [])),
            "valor_prog": valor,
        })
    total_por_sa: dict = {}
    for v in out:
        total_por_sa[v["SA"]] = total_por_sa.get(v["SA"], 0.0) + v["valor_prog"]
    for v in out:
        t = total_por_sa.get(v["SA"], 0.0)
        v["valor_sa"] = (v["valor_prog"] / t) if t else 0.0
    return out


def desde_formato_antiguo(viejas: list[dict], il_rows: list[dict]) -> list[dict]:
    """Proyectos de antes de 2026-10-26: cada actividad era de un solo IL
    (``{"IL", "DA", "PA"}``, PA relativo dentro del IL). Pasa cada una a una
    actividad de la SA y el instrumento de su IL, con PA en % del IL."""
    info = {_s(r.get("IL")): r for r in il_rows}
    suma: dict[str, float] = {}
    for v in viejas:
        suma[_s(v.get("IL"))] = suma.get(_s(v.get("IL")), 0.0) + float(_num(v.get("PA")) or 0)
    out = []
    for i, v in enumerate(viejas, start=1):
        il = _s(v.get("IL"))
        r = info.get(il, {})
        pa = _num(v.get("PA"))
        out.append({
            "id": i,
            "SA": _num(r.get("SA")),
            "IE": _s(r.get("IE")),
            "titulo": _s(v.get("DA")),
            "ils": [{
                "IL": il,
                "PA": round(100.0 * float(pa) / suma[il], 2) if pa is not None and suma.get(il) else None,
            }],
        })
    return out
