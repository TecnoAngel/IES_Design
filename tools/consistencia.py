"""Revisión de coherencia del proyecto.

La tabla de **situaciones de aprendizaje** manda dentro del proyecto, y el
**currículo** (``curriculo.db``) manda sobre los códigos. Antes de guardar /
generar se comprueba que:

* hay al menos una situación de aprendizaje;
* cada criterio de evaluación de la materia tiene al menos un indicador;
* los indicadores usan criterios, contenidos (CON), transversales (CT) y
  descriptores operativos (DO) que existen en el currículo de la materia;
* las actividades apuntan a indicadores de logro que existen.

Si algo no cuadra, la app avisa y deja elegir: revisarlo a mano o aplicar los
arreglos automáticos (``aplicar_arreglos``).
"""

from __future__ import annotations

import re
from typing import Any


def _s(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _cod(t: str) -> str:
    """Código normalizado para comparar ("A. 1.2" -> "A.1.2")."""
    return re.sub(r"\s+", "", t)


def _tokens(v: Any) -> list[str]:
    return [t.strip() for t in str(v or "").split(",") if t.strip()]


# Columnas de códigos de un IL -> (clave del aviso, nombre para el aviso)
CAMPOS_CODIGO = {
    "CON": ("codigos_con", "contenidos"),
    "CT": ("codigos_ct", "contenidos transversales"),
    "DO": ("codigos_do", "descriptores operativos"),
}


def revisar(
    situaciones: list[dict],
    ce_list: list[str],
    il_rows: list[dict],
    actividades: list[dict],
    codigos: dict[str, set[str]] | None = None,
) -> list[dict]:
    """Devuelve la lista de incoherencias. Cada una:
    ``{clave, titulo, detalle, autofix, datos}``. ``codigos`` =
    ``{"CON": {...}, "CT": {...}, "DO": {...}}`` válidos para la materia."""
    issues: list[dict] = []

    sa_nums = [s["SA"] for s in situaciones if s.get("SA") not in (None, "")]
    if not sa_nums:
        issues.append({
            "clave": "sin_sa",
            "titulo": "No hay situaciones de aprendizaje",
            "detalle": "Crea al menos una situación de aprendizaje antes de continuar.",
            "autofix": None,
        })
        return issues

    # 1) cada CE con ≥ 1 IL
    ce_con_il = {_s(r.get("CE")) for r in il_rows if _s(r.get("CE"))}
    ce_sin_il = [c for c in ce_list if c not in ce_con_il]
    if ce_sin_il:
        issues.append({
            "clave": "ce_sin_il",
            "titulo": f"{len(ce_sin_il)} criterio(s) de evaluación sin indicador de logro",
            "detalle": "Sin IL: " + ", ".join(ce_sin_il)
            + ". Cada criterio necesita al menos un indicador; el arreglo añade uno en blanco.",
            "autofix": "add_il",
            "datos": ce_sin_il,
        })

    # 2) IL con un CE que no existe en el currículo de la materia
    il_ce_malo = sorted({
        _s(r.get("CE")) for r in il_rows
        if _s(r.get("CE")) and _s(r.get("CE")) not in set(ce_list)
    })
    if il_ce_malo:
        issues.append({
            "clave": "il_ce_malo",
            "titulo": "Indicadores con un criterio que no existe en el currículo",
            "detalle": "Criterios no encontrados: " + ", ".join(il_ce_malo)
            + ". El arreglo quita esos indicadores (y sus actividades); si prefieres "
            "conservarlos, cámbiales el criterio en «Indicadores de logro».",
            "autofix": "drop_il",
            "datos": il_ce_malo,
        })

    # 3) códigos de CON / CT / DO que no existen en el currículo
    for campo, (clave, nombre) in CAMPOS_CODIGO.items():
        validos = (codigos or {}).get(campo)
        if validos is None:
            continue
        malos = sorted({t for r in il_rows for t in _tokens(r.get(campo)) if _cod(t) not in validos})
        if malos:
            issues.append({
                "clave": clave,
                "titulo": f"Códigos de {nombre} que no existen en el currículo",
                "detalle": f"No encontrados en la columna {campo}: " + ", ".join(f"«{m}»" for m in malos)
                + ". El arreglo los quita de los indicadores.",
                "autofix": "limpiar_codigos",
                "datos": {campo: malos},
            })

    # 4) actividades cuyo IL ya no existe
    ils = {_s(r.get("IL")) for r in il_rows if _s(r.get("IL"))}
    act_huerf = sorted({
        _s(a.get("IL")) for a in actividades
        if _s(a.get("IL")) and _s(a.get("IL")) not in ils
    })
    if act_huerf:
        issues.append({
            "clave": "act_huerfanas",
            "titulo": "Actividades apuntando a indicadores inexistentes",
            "detalle": "IL sin indicador: " + ", ".join(act_huerf) + ". El arreglo las quita.",
            "autofix": "drop_acts",
            "datos": act_huerf,
        })

    return issues


# ---------------------------------------------------------------------------
# Auto-arreglos en memoria
# ---------------------------------------------------------------------------
def add_il_para_ce(il_rows: list[dict], ce_faltantes: list[str], ce_do: dict | None = None) -> list[dict]:
    """Añade una fila de IL en blanco por cada CE sin indicador (con los
    descriptores operativos del criterio, si se pasan)."""
    nuevos = list(il_rows)
    for ce in ce_faltantes:
        nuevos.append({
            "CE": ce, "CED": "", "IL": "", "PIL": 1,
            "DIL": "", "DO": ", ".join((ce_do or {}).get(ce, [])), "CON": "", "CT": "",
            "IE": "", "CC": "", "AE": "", "SA": None,
        })
    return nuevos


def quitar_il_de_ce(il_rows: list[dict], ces: list[str]) -> list[dict]:
    malos = set(ces)
    return [r for r in il_rows if _s(r.get("CE")) not in malos]


def limpiar_codigos(il_rows: list[dict], malos: dict[str, list[str]]) -> list[dict]:
    """Quita de las columnas CON/CT/DO de cada IL los códigos de ``malos``."""
    out = []
    for r in il_rows:
        r2 = dict(r)
        for campo, cods in malos.items():
            fuera = {_cod(c) for c in cods}
            r2[campo] = ", ".join(t for t in _tokens(r.get(campo)) if _cod(t) not in fuera)
        out.append(r2)
    return out


def quitar_actividades_huerfanas(acts: list[dict], il_rows: list[dict]) -> list[dict]:
    ils = {_s(r.get("IL")) for r in il_rows if _s(r.get("IL"))}
    return [a for a in acts if _s(a.get("IL")) in ils]
