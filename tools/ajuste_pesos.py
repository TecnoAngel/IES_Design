"""Ajuste de pesos por IPF (Iterative Proportional Fitting / RAS / Sinkhorn).

Réplica en Python de la hoja ``Ajuste_Pesos_IPF`` del Excel, con convergencia
real (se itera hasta tolerancia, no un nº fijo de veces).

Idea: se construye una matriz SA × instrumento de evaluación sembrada con el
recuento actual de indicadores de logro por celda y se ajusta iterativamente
para que:

* la suma de cada **fila** (SA) sea su cuota horaria  (HSA / ΣHSA · 100), y
* la suma de cada **columna** (IE) sea el % objetivo que fija el profesor
  (deben sumar ~100; si no, se normalizan).

Del resultado se derivan:

* ``PIL sugerido`` de cada indicador = peso de su celda / nº de indicadores en
  esa celda  (mínimo 1, redondeado).
* ``P sugerido`` de cada criterio = Σ de los PIL sugeridos de sus indicadores.

No modifica ninguna tabla: la app enseña la propuesta y el profesor decide.
"""

from __future__ import annotations

import math
from typing import Any


def _s(v: Any) -> str:
    return "" if v is None else str(v).strip()


def hamilton(weights: dict[Any, float], total: int, *, minimo: int = 0) -> dict[Any, int]:
    """Reparte ``total`` unidades enteras entre las claves de ``weights`` de forma
    proporcional (método de Hamilton / mayores restos), con un mínimo por clave.
    La suma del resultado es exactamente ``max(total, minimo·nº claves)``."""
    keys = list(weights)
    if not keys:
        return {}
    total = max(int(round(total)), minimo * len(keys))
    sw = sum(max(0.0, w) for w in weights.values())
    if sw <= 0:
        q = {k: minimo for k in keys}
        for i in range(total - minimo * len(keys)):
            q[keys[i % len(keys)]] += 1
        return q
    exact = {k: max(0.0, weights[k]) / sw * total for k in keys}
    out = {k: max(minimo, math.floor(exact[k])) for k in keys}
    resto = total - sum(out.values())
    if resto > 0:
        for k in sorted(keys, key=lambda k: exact[k] - math.floor(exact[k]), reverse=True)[:resto]:
            out[k] += 1
    elif resto < 0:
        ajustables = sorted(
            (k for k in keys if out[k] > minimo),
            key=lambda k: exact[k] - math.floor(exact[k]),
        )
        i = 0
        while resto < 0 and ajustables:
            k = ajustables[i % len(ajustables)]
            if out[k] > minimo:
                out[k] -= 1
                resto += 1
            i += 1
            if i > len(ajustables) * 50:
                break
    return out


def _sa_hsa(sits) -> list[tuple[int, float]]:
    pares: list[tuple[int, float]] = []
    for s in sits:
        if isinstance(s, dict):
            sa, hsa = s.get("SA", s.get("sa")), s.get("HSA", s.get("hsa"))
        else:
            sa, hsa = getattr(s, "sa", None), getattr(s, "hsa", None)
        try:
            sa_i, hsa_f = int(sa), float(hsa)
        except (TypeError, ValueError):
            continue
        if hsa_f > 0:
            pares.append((sa_i, hsa_f))
    return pares


def reparto_horario(sits) -> dict[int, float]:
    """% de cada SA = HSA / ΣHSA · 100."""
    pares = _sa_hsa(sits)
    total = sum(h for _, h in pares)
    return {sa: (h / total * 100 if total else 0.0) for sa, h in pares}


def instrumentos_presentes(il_rows) -> list[str]:
    """Instrumentos de evaluación que aparecen en los indicadores, en orden."""
    vistos: list[str] = []
    for r in il_rows:
        ie = _s(r.get("IE"))
        if ie and ie not in vistos:
            vistos.append(ie)
    return vistos


def reparto_ie_actual(il_rows, ce_p: dict[str, float]) -> dict[str, float]:
    """% actual por IE (peso ``PIL%_CE · %CE`` sumado por IE), normalizado a 100."""
    from tools.indicadores_logro import peso_por_ie

    pares = peso_por_ie(il_rows, ce_p or {})
    total = sum(v for _, v in pares)
    return {ie: (v / total * 100 if total else 0.0) for ie, v in pares}


def ipf(
    seed: dict[tuple[Any, Any], float],
    row_targets: dict[Any, float],
    col_targets: dict[Any, float],
    *,
    max_iter: int = 1000,
    tol: float = 1e-9,
) -> tuple[dict[tuple[Any, Any], float], int, float]:
    """Ajuste proporcional iterativo. Devuelve ``(matriz, nº iteraciones, residuo)``."""
    rows, cols = list(row_targets), list(col_targets)
    M = {(r, c): float(seed.get((r, c), 0.0)) for r in rows for c in cols}

    # Columna con objetivo > 0 pero sin ninguna semilla: se siembra minúscula y
    # uniforme para que el ajuste pueda repartir su masa.
    for c in cols:
        if col_targets[c] > 0 and sum(M[(r, c)] for r in rows) == 0:
            for r in rows:
                M[(r, c)] = 1e-12

    n_iter, residuo = 0, float("inf")
    for n_iter in range(1, max_iter + 1):
        for r in rows:
            s = sum(M[(r, c)] for c in cols)
            if s > 0:
                f = row_targets[r] / s
                for c in cols:
                    M[(r, c)] *= f
        for c in cols:
            s = sum(M[(r, c)] for r in rows)
            if s > 0:
                f = col_targets[c] / s
                for r in rows:
                    M[(r, c)] *= f
        residuo = max(
            (abs(sum(M[(r, c)] for c in cols) - row_targets[r]) for r in rows),
            default=0.0,
        )
        if residuo < tol:
            break
    return M, n_iter, residuo


def sugerir_pesos(il_rows, sits, ie_objetivo: dict[str, float], *, max_iter: int = 1000) -> dict:
    """Corre el IPF y devuelve la matriz ajustada + los pesos P y PIL sugeridos."""
    filas = [r for r in il_rows if _s(r.get("IL"))]

    def _sa_of(r):
        try:
            return int(r.get("SA"))
        except (TypeError, ValueError):
            return None

    # Semilla: recuento de indicadores por (SA, IE).
    seed: dict[tuple[int, str], float] = {}
    n_celda: dict[tuple[int | None, str], int] = {}
    for r in filas:
        sa, ie = _sa_of(r), _s(r.get("IE"))
        n_celda[(sa, ie)] = n_celda.get((sa, ie), 0) + 1
        if sa is not None and ie:
            seed[(sa, ie)] = seed.get((sa, ie), 0.0) + 1.0

    # Filas = SA con indicadores; su cuota horaria renormalizada a 100.
    rh_full = reparto_horario(sits)
    sas = sorted({sa for (sa, _ie) in seed})
    sub = {sa: rh_full.get(sa, 0.0) for sa in sas}
    tot_sub = sum(sub.values())
    row_targets = {sa: (v / tot_sub * 100 if tot_sub else 0.0) for sa, v in sub.items()}
    sa_sin_horas = [sa for sa in sas if sa not in rh_full]
    sa_con_horas_sin_il = [sa for sa in rh_full if sa not in sas]

    # Columnas = instrumentos con objetivo; objetivos normalizados a 100.
    ie_obj = {k: max(0.0, float(v or 0)) for k, v in ie_objetivo.items()}
    tot_ie = sum(ie_obj.values())
    col_targets = {ie: (v / tot_ie * 100 if tot_ie else 0.0) for ie, v in ie_obj.items()}
    ies = list(col_targets)
    ie_sin_objetivo = [ie for ie in instrumentos_presentes(filas) if ie not in col_targets]

    M, n_iter, residuo = ipf(seed, row_targets, col_targets, max_iter=max_iter)

    # Peso "crudo" (real) de cada indicador = peso de su celda / nº de indicadores
    # de esa celda. Los que no caen en una celda válida conservan su PIL actual.
    raw: dict[str, float] = {}
    il_por_sa: dict[int | None, list[str]] = {}
    avisos_il: list[str] = []
    for r in filas:
        il, sa, ie = _s(r.get("IL")), _sa_of(r), _s(r.get("IE"))
        il_por_sa.setdefault(sa, []).append(il)
        celda = M.get((sa, ie))
        n = n_celda.get((sa, ie), 0)
        if celda is None or n == 0:
            raw[il] = max(0.0, float(r.get("PIL") or 1))
            avisos_il.append(il)
        else:
            raw[il] = celda / n

    # Redondeo a enteros preservando sumas: primero el "presupuesto" entero de
    # cada SA (∝ su cuota horaria, Σ = 100) y luego, dentro de cada SA, se reparte
    # ese presupuesto entre sus indicadores según el peso crudo (mín. 1 por IL).
    # Así el peso por SA queda lo más pegado posible al reparto de horas.
    sa_presupuesto = hamilton(row_targets, 100, minimo=0)
    pil_por_il: dict[str, int] = {}
    for sa, ils in il_por_sa.items():
        w = {il: raw.get(il, 1.0) for il in ils}
        objetivo_sa = max(sa_presupuesto.get(sa, 0), len(ils))  # mín. 1 por IL
        pil_por_il.update(hamilton(w, objetivo_sa, minimo=1))

    p_por_ce: dict[str, int] = {}
    for r in filas:
        ce, il = _s(r.get("CE")), _s(r.get("IL"))
        if ce:
            p_por_ce[ce] = p_por_ce.get(ce, 0) + pil_por_il.get(il, 0)

    # Comparación por SA: peso resultante (Σ PIL de la SA / Σ PIL total) vs cuota
    # horaria; es lo que compara el gráfico de barras.
    tot_pil = sum(pil_por_il.values()) or 1
    comparacion_sa = []
    for sa in sas:
        peso = sum(pil_por_il.get(il, 0) for il in il_por_sa.get(sa, [])) / tot_pil * 100
        comparacion_sa.append(
            {"sa": sa, "peso_pct": peso, "horas_pct": row_targets.get(sa, 0.0)}
        )

    return {
        "matriz": M,
        "sas": sas,
        "instrumentos": ies,
        "row_targets": row_targets,
        "col_targets": col_targets,
        "pil_por_il": pil_por_il,
        "p_por_ce": p_por_ce,
        "comparacion_sa": comparacion_sa,
        "iteraciones": n_iter,
        "residuo": residuo,
        "avisos_il": avisos_il,
        "ie_sin_objetivo": ie_sin_objetivo,
        "sa_con_horas_sin_il": sa_con_horas_sin_il,
        "sa_sin_horas": sa_sin_horas,
    }
