"""Revisión de coherencia entre las tablas de la programación.

La tabla de **situaciones de aprendizaje** manda. Antes de guardar / generar se
comprueba que lo demás encaje:

* cada criterio de evaluación tiene al menos un indicador de logro;
* la tabla ``P_Aula_SA`` tiene una columna por cada SA, con su título;
* las actividades apuntan a indicadores de logro que existen.

Si algo no cuadra, la app avisa y deja elegir: abortar (y arreglarlo en Excel) o
regenerar automáticamente lo que haga falta.
"""

from __future__ import annotations

import re
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from openpyxl import load_workbook

SA_SHEET = "P_Aula_SA"
SA_TABLE = "Tabla9"


def _s(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _norm(v: Any) -> str:
    return re.sub(r"\s+", " ", _s(v)).lower()


def revisar(
    situaciones: list[dict],
    ce_list: list[str],
    il_rows: list[dict],
    actividades: list[dict],
    pa_sa_cols: list[dict],
) -> list[dict]:
    """Devuelve la lista de incoherencias. Cada una:
    ``{clave, titulo, detalle, autofix}`` (autofix ∈ {"add_il", "regen_pasa",
    "drop_acts", None})."""
    issues: list[dict] = []

    _pares = sorted(
        (int(s["SA"]), _s(s.get("DSA")))
        for s in situaciones if s.get("SA") not in (None, "")
    )
    sa_nums = [n for n, _ in _pares]
    sa_titulos = [t for _, t in _pares]  # en orden de nº de SA (SA 1, 2, 3…)

    if not sa_nums:
        issues.append(
            {
                "clave": "sin_sa",
                "titulo": "No hay situaciones de aprendizaje",
                "detalle": "Crea al menos una situación de aprendizaje antes de continuar.",
                "autofix": None,
            }
        )
        return issues

    # 1) cada CE con ≥ 1 IL
    ce_con_il = {_s(r.get("CE")) for r in il_rows if _s(r.get("CE"))}
    ce_sin_il = [c for c in ce_list if c not in ce_con_il]
    if ce_sin_il:
        issues.append(
            {
                "clave": "ce_sin_il",
                "titulo": f"{len(ce_sin_il)} criterio(s) de evaluación sin indicador de logro",
                "detalle": "Sin IL: " + ", ".join(ce_sin_il)
                + ". Cada criterio necesita al menos un indicador.",
                "autofix": "add_il",
                "datos": ce_sin_il,
            }
        )

    # 2) IL con un CE que no existe en la tabla de criterios
    il_ce_malo = sorted({
        _s(r.get("CE")) for r in il_rows
        if _s(r.get("CE")) and _s(r.get("CE")) not in set(ce_list)
    })
    if il_ce_malo:
        issues.append(
            {
                "clave": "il_ce_malo",
                "titulo": "Indicadores con un criterio que no existe",
                "detalle": "Criterios no encontrados: " + ", ".join(il_ce_malo)
                + ". Corrige el CE de esos indicadores o el criterio en el Excel.",
                "autofix": None,
            }
        )

    # 3) P_Aula_SA: una columna por SA, con su título
    n_sa = len(sa_nums)
    n_col = len(pa_sa_cols)
    titulos_col = [_s(c.get("valores", {}).get("titulo")) for c in pa_sa_cols]
    desajuste = n_col != n_sa or any(
        _norm(a) != _norm(b) for a, b in zip(titulos_col, sa_titulos)
    )
    if desajuste:
        issues.append(
            {
                "clave": "pasa_desajuste",
                "titulo": "La tabla P_Aula_SA no coincide con las situaciones de aprendizaje",
                "detalle": (
                    f"Situaciones: {n_sa}. Columnas en P_Aula_SA: {n_col}. "
                    "Regenerar creará una columna por SA con su título "
                    "(se conserva el contenido de las que ya cuadran por posición)."
                ),
                "autofix": "regen_pasa",
                "datos": sa_titulos,
            }
        )

    # 4) actividades cuyo IL ya no existe
    ils = {_s(r.get("IL")) for r in il_rows if _s(r.get("IL"))}
    act_huerf = sorted({
        _s(a.get("IL")) for a in actividades
        if _s(a.get("IL")) and _s(a.get("IL")) not in ils
    })
    if act_huerf:
        issues.append(
            {
                "clave": "act_huerfanas",
                "titulo": "Actividades apuntando a indicadores inexistentes",
                "detalle": "IL sin indicador: " + ", ".join(act_huerf)
                + ". Regenerar las quita.",
                "autofix": "drop_acts",
                "datos": act_huerf,
            }
        )

    return issues


# ---------------------------------------------------------------------------
# Auto-arreglos en memoria
# ---------------------------------------------------------------------------
def add_il_para_ce(il_rows: list[dict], ce_faltantes: list[str]) -> list[dict]:
    """Añade una fila de IL en blanco por cada CE sin indicador."""
    nuevos = list(il_rows)
    for ce in ce_faltantes:
        nuevos.append(
            {
                "CE": ce, "CED": "", "IL": "", "PIL": 1,
                "DIL": "", "DO": "", "CON": "", "CT": "",
                "IE": "", "CC": "", "AE": "", "SA": None,
            }
        )
    return nuevos


def quitar_actividades_huerfanas(acts: list[dict], il_rows: list[dict]) -> list[dict]:
    ils = {_s(r.get("IL")) for r in il_rows if _s(r.get("IL"))}
    return [a for a in acts if _s(a.get("IL")) in ils]


# ---------------------------------------------------------------------------
# Regenerar P_Aula_SA (escritura quirúrgica sobre el ZIP)
# ---------------------------------------------------------------------------
def _read_bytes(source: Any) -> bytes:
    if isinstance(source, (str, Path)):
        return Path(source).expanduser().resolve().read_bytes()
    if hasattr(source, "getvalue"):
        return source.getvalue()
    if hasattr(source, "read"):
        return source.read()
    raise TypeError("origen no válido")


def _col_letter(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _find_sheet_path(zf: zipfile.ZipFile, name: str) -> str:
    wb = zf.read("xl/workbook.xml").decode("utf-8")
    rid = re.search(rf'<sheet[^>]*name="{re.escape(name)}"[^>]*r:id="([^"]+)"', wb).group(1)
    rels = zf.read("xl/_rels/workbook.xml.rels").decode("utf-8")
    tgt = re.search(
        rf'<Relationship[^>]*Id="{re.escape(rid)}"[^>]*Target="([^"]+)"', rels
    ).group(1).lstrip("/")
    return tgt if tgt.startswith("xl/") else "xl/" + tgt.replace("../", "")


def _find_table_path(zf: zipfile.ZipFile, table: str) -> str | None:
    for n in zf.namelist():
        if n.startswith("xl/tables/") and n.endswith(".xml"):
            if f'name="{table}"' in zf.read(n).decode("utf-8"):
                return n
    return None


def _txt(ref: str, value: str) -> str:
    if value in (None, ""):
        return f'<c r="{ref}"/>'
    return (
        f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">'
        f"{escape(str(value))}</t></is></c>"
    )


def regenerar_p_aula_sa(source: Any, sa_titulos: list[str]) -> bytes:
    """Reconstruye Tabla9 con una columna por SA. Conserva el contenido de las
    columnas que ya existían en la misma posición; las nuevas van en blanco
    salvo la fila ``titulo``."""
    payload = _read_bytes(source)
    src = zipfile.ZipFile(BytesIO(payload))
    sp = _find_sheet_path(src, SA_SHEET)
    tp = _find_table_path(src, SA_TABLE)
    xml = src.read(sp).decode("utf-8")

    wb = load_workbook(BytesIO(payload), data_only=True)
    ws = wb[SA_SHEET]
    campos = [_s(r[0].value) for r in ws.iter_rows(min_row=2, max_col=1) if _s(r[0].value)]
    _fila = {c: i for i, c in enumerate(campos)}

    # contenido actual por columna, indexado por el título de esa columna
    old_by_titulo: dict[str, dict[str, str]] = {}
    ti = _fila.get("titulo")
    for ci in range(1, ws.max_column):
        vals = {}
        for i, campo in enumerate(campos):
            v = ws.cell(row=2 + i, column=1 + ci).value
            if v not in (None, ""):
                vals[campo] = _s(v)
        key = _norm(vals.get("titulo", "")) if ti is not None else ""
        if vals:
            old_by_titulo.setdefault(key, vals)

    n = len(sa_titulos)
    last_col = _col_letter(1 + n)
    header = "".join(
        [_txt("A1", "Campo")]
        + [_txt(f"{_col_letter(2 + j)}1", f"Situación {j + 1}") for j in range(n)]
    )
    rows_xml = [f'<row r="1" spans="1:{1 + n}">{header}</row>']
    for ri, campo in enumerate(campos):
        r = 2 + ri
        cells = [_txt(f"A{r}", campo)]
        for j in range(n):
            col = _col_letter(2 + j)
            prev = old_by_titulo.get(_norm(sa_titulos[j]), {})
            val = prev.get(campo, "")
            if campo == "titulo":
                val = sa_titulos[j] or val
            cells.append(_txt(f"{col}{r}", val))
        rows_xml.append(f'<row r="{r}" spans="1:{1 + n}">{"".join(cells)}</row>')

    sd = re.search(r"<sheetData>.*?</sheetData>", xml, re.S)
    xml = xml[: sd.start()] + "<sheetData>" + "".join(rows_xml) + "</sheetData>" + xml[sd.end():]
    xml = re.sub(r'<dimension ref="[^"]*"/>', f'<dimension ref="A1:{last_col}{1 + len(campos)}"/>', xml)

    replacements = {sp: xml.encode("utf-8")}
    if tp:
        t = src.read(tp).decode("utf-8")
        ref = f"A1:{last_col}{1 + len(campos)}"
        t = re.sub(r'(<table[^>]*\sref=")[^"]*(")', rf"\g<1>{ref}\g<2>", t)
        t = re.sub(r'(<autoFilter\s+ref=")[^"]*(")', rf"\g<1>{ref}\g<2>", t)
        # columnas de la tabla
        cols = "".join(
            f'<tableColumn id="{i + 1}" name="{escape("Campo" if i == 0 else f"Situación {i}")}"/>'
            for i in range(n + 1)
        )
        t = re.sub(
            r"<tableColumns count=\"\d+\">.*?</tableColumns>",
            f'<tableColumns count="{n + 1}">{cols}</tableColumns>',
            t,
            flags=re.S,
        )
        replacements[tp] = t.encode("utf-8")

    wbx = src.read("xl/workbook.xml").decode("utf-8")
    if "fullCalcOnLoad" not in wbx:
        wbx = re.sub(r"<calcPr\s+", '<calcPr fullCalcOnLoad="1" ', wbx, count=1)
    replacements["xl/workbook.xml"] = wbx.encode("utf-8")

    out = BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            dst.writestr(item, replacements.get(item.filename, src.read(item.filename)))
    return out.getvalue()
