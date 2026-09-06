"""Lectura y escritura de las tablas de la programación de aula:

* ``Tabla8``  (hoja P_Aula_Datos_Generales) — pares campo / valor.
* ``Tabla9``  (hoja P_Aula_SA) — transpuesta: columna A = campo, cada columna
  siguiente = una situación de aprendizaje.
* ``TablaActividades`` (hoja Actividades) — actividades por indicador de logro.
  Editables: IL (a qué indicador pertenece), A (código, automático), DA
  (descripción), PA (peso). El resto de columnas son VLOOKUP sobre
  ``TablaIndicadoresLogro`` y se recalculan al abrir el Excel.

Todo se escribe de forma quirúrgica sobre el ZIP (ver `indicadores_logro`).
"""

from __future__ import annotations

import re
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from openpyxl import load_workbook

DATOS_SHEET = "P_Aula_Datos_Generales"
SA_SHEET = "P_Aula_SA"
ACT_SHEET = "Actividades"
ACT_TABLE = "TablaActividades"

# VLOOKUP de las columnas B..J de TablaActividades sobre TablaIndicadoresLogro[[IL]:[SA]]
_VLOOKUP_COLS = {  # letra de columna -> índice en el VLOOKUP
    "B": 2, "C": 4, "D": 5, "E": 6, "F": 7, "G": 8, "H": 9, "I": 10, "J": 11,
}
_VLOOKUP = (
    "VLOOKUP(TablaActividades[[#This Row],[IL]],"
    "TablaIndicadoresLogro[[#Data],[IL]:[SA]],{idx},1)"
)
_PA_PCT = (
    "TablaActividades[[#This Row],[PA]]/SUMIF(TablaActividades[IL], "
    "TablaActividades[[#This Row],[IL]], TablaActividades[PA])"
)
_FACTOR = "TablaActividades[[#This Row],[PIL]]*TablaActividades[[#This Row],[PA%]]"


def _read_bytes(source: Any) -> bytes:
    if isinstance(source, (str, Path)):
        return Path(source).expanduser().resolve().read_bytes()
    if hasattr(source, "getvalue"):
        return source.getvalue()
    if hasattr(source, "read"):
        return source.read()
    raise TypeError("El origen debe ser una ruta o un archivo subido")


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


def _find_sheet(wb, name: str):
    for n in wb.sheetnames:
        if n == name:
            return wb[n]
    return None


# ---------------------------------------------------------------------------
# LECTURA
# ---------------------------------------------------------------------------
def read_prog_aula(source: Any) -> dict:
    payload = _read_bytes(source)
    wb = load_workbook(BytesIO(payload), data_only=True)

    # Datos generales: campo -> valor (filas 2..)
    datos: list[tuple[str, str]] = []
    ws = _find_sheet(wb, DATOS_SHEET)
    if ws is not None:
        for row in ws.iter_rows(min_row=2, max_col=2, values_only=True):
            if row and _s(row[0]):
                datos.append((_s(row[0]), _s(row[1] if len(row) > 1 else "")))

    # P_Aula_SA transpuesta: campos (col A, filas 2..) + columnas de situación
    sa_campos: list[str] = []
    sa_cols: list[dict] = []
    ws = _find_sheet(wb, SA_SHEET)
    if ws is not None:
        rows = list(ws.iter_rows(values_only=True))
        if rows:
            header = rows[0]
            for r in rows[1:]:
                if r and _s(r[0]):
                    sa_campos.append(_s(r[0]))
            for ci in range(1, len(header)):
                if header[ci] in (None, ""):
                    continue
                col_letter = _col_letter(ci + 1)
                valores = {}
                for ri, r in enumerate(rows[1:]):
                    if r and _s(r[0]) and ci < len(r):
                        valores[_s(r[0])] = _s(r[ci])
                sa_cols.append(
                    {"col": col_letter, "nombre": _s(header[ci]), "valores": valores}
                )

    # Actividades: IL, A, DA, PA
    actividades: list[dict] = []
    ws = _find_sheet(wb, ACT_SHEET)
    if ws is not None:
        headers = [(_s(c.value)) for c in ws[1]]
        idx = {h: i for i, h in enumerate(headers)}
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row is None or all(c in (None, "") for c in row):
                continue
            il = _s(row[idx.get("IL", 0)]) if "IL" in idx else _s(row[0])
            a = _s(row[idx["A"]]) if "A" in idx and idx["A"] < len(row) else ""
            da = _s(row[idx["DA"]]) if "DA" in idx and idx["DA"] < len(row) else ""
            pa = _num(row[idx["PA"]]) if "PA" in idx and idx["PA"] < len(row) else None
            sa = _num(row[idx["SA"]]) if "SA" in idx and idx["SA"] < len(row) else None
            if not (il or a or da):
                continue
            actividades.append({"IL": il, "A": a, "DA": da, "PA": pa, "SA": sa})

    return {
        "datos": datos,
        "sa_campos": sa_campos,
        "sa_cols": sa_cols,
        "actividades": actividades,
    }


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


# ---------------------------------------------------------------------------
# ESCRITURA QUIRÚRGICA
# ---------------------------------------------------------------------------
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


def _num_xml(v) -> str:
    f = float(v)
    return str(int(f)) if f.is_integer() else repr(f)


def _txt_cell(ref: str, value: str, style: str = "") -> str:
    st = f' s="{style}"' if style else ""
    if value in (None, ""):
        return f'<c r="{ref}"{st}/>' if st else ""
    return (
        f'<c r="{ref}"{st} t="inlineStr"><is><t xml:space="preserve">'
        f"{escape(str(value))}</t></is></c>"
    )


def _force_full_recalc(xml: str) -> str:
    if "fullCalcOnLoad" in xml:
        return xml
    if "<calcPr" in xml:
        return re.sub(r"<calcPr\s+", '<calcPr fullCalcOnLoad="1" ', xml, count=1)
    return xml.replace("</workbook>", '<calcPr fullCalcOnLoad="1"/></workbook>')


def _rewrite_col_b(sheet_xml: str, campo_valor: dict[str, str], campos_orden: list[str], first_row: int) -> str:
    """Reescribe la columna B (valor) de una tabla campo/valor vertical."""
    for i, campo in enumerate(campos_orden):
        if campo not in campo_valor:
            continue
        row = first_row + i
        cell = _txt_cell(f"B{row}", campo_valor[campo], style="1")
        sheet_xml = re.sub(
            rf'<c r="B{row}"[^>]*?(?:/>|>.*?</c>)',
            cell or f'<c r="B{row}" s="1"/>',
            sheet_xml,
            count=1,
            flags=re.S,
        )
    return sheet_xml


def _apply(src: zipfile.ZipFile, replacements: dict) -> bytes:
    out = BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            dst.writestr(item, replacements.get(item.filename, src.read(item.filename)))
    return out.getvalue()


def save_datos_generales(source: Any, datos: dict[str, str]) -> bytes:
    payload = _read_bytes(source)
    src = zipfile.ZipFile(BytesIO(payload))
    sp = _find_sheet_path(src, DATOS_SHEET)
    xml = src.read(sp).decode("utf-8")

    # orden de campos = filas 2.. (col A). Los sacamos del propio xml vía openpyxl.
    wb = load_workbook(BytesIO(payload), data_only=True)
    ws = wb[DATOS_SHEET]
    campos = [_s(r[0].value) for r in ws.iter_rows(min_row=2, max_col=1) if _s(r[0].value)]

    xml = _rewrite_col_b(xml, datos, campos, first_row=2)
    return _apply(
        src,
        {
            sp: xml.encode("utf-8"),
            "xl/workbook.xml": _force_full_recalc(
                src.read("xl/workbook.xml").decode("utf-8")
            ).encode("utf-8"),
        },
    )


def save_p_aula_sa(source: Any, col_letter: str, valores: dict[str, str]) -> bytes:
    payload = _read_bytes(source)
    src = zipfile.ZipFile(BytesIO(payload))
    sp = _find_sheet_path(src, SA_SHEET)
    xml = src.read(sp).decode("utf-8")

    wb = load_workbook(BytesIO(payload), data_only=True)
    ws = wb[SA_SHEET]
    campos = [_s(r[0].value) for r in ws.iter_rows(min_row=2, max_col=1) if _s(r[0].value)]

    for i, campo in enumerate(campos):
        if campo not in valores:
            continue
        row = 2 + i
        ref = f"{col_letter}{row}"
        cell = _txt_cell(ref, valores[campo])
        xml = re.sub(
            rf'<c r="{ref}"[^>]*?(?:/>|>.*?</c>)',
            cell or f'<c r="{ref}"/>',
            xml,
            count=1,
            flags=re.S,
        )
    return _apply(
        src,
        {
            sp: xml.encode("utf-8"),
            "xl/workbook.xml": _force_full_recalc(
                src.read("xl/workbook.xml").decode("utf-8")
            ).encode("utf-8"),
        },
    )


def _act_row_xml(r: int, act: dict) -> str:
    cells = [_txt_cell(f"A{r}", act.get("IL", ""), style="7")]
    for col, idx in _VLOOKUP_COLS.items():
        cells.append(
            f'<c r="{col}{r}"><f>{escape(_VLOOKUP.format(idx=idx))}</f></c>'
        )
    cells.append(_txt_cell(f"K{r}", act.get("A", ""), style="7"))
    cells.append(_txt_cell(f"L{r}", act.get("DA", ""), style="7"))
    pa = act.get("PA")
    cells.append(
        f'<c r="M{r}" s="7"><v>{_num_xml(pa)}</v></c>' if pa not in (None, "") else f'<c r="M{r}" s="7"/>'
    )
    cells.append(f'<c r="N{r}" s="18"><f>{escape(_PA_PCT)}</f></c>')
    cells.append(f'<c r="O{r}"><f>{escape(_FACTOR)}</f></c>')
    return f'<row r="{r}" spans="1:15" x14ac:dyDescent="0.25">{"".join(cells)}</row>'


def save_actividades(source: Any, actividades: list[dict], pil_por_il: dict[str, float]) -> bytes:
    payload = _read_bytes(source)
    acts = recompute_actividades(actividades, pil_por_il)

    src = zipfile.ZipFile(BytesIO(payload))
    sp = _find_sheet_path(src, ACT_SHEET)
    tp = _find_table_path(src, ACT_TABLE)
    xml = src.read(sp).decode("utf-8")

    sd = re.search(r"<sheetData>(.*)</sheetData>", xml, re.S)
    rows_xml = re.findall(r"<row [^>]*>.*?</row>|<row [^>]*/>", sd.group(1), re.S)
    header = next(rx for rx in rows_xml if re.search(r'r="1"', rx))

    n = len(acts)
    new_rows = [header] + [_act_row_xml(2 + i, a) for i, a in enumerate(acts)]
    last = max(n + 1, 2)

    xml = xml[: sd.start()] + "<sheetData>" + "".join(new_rows) + "</sheetData>" + xml[sd.end():]
    xml = re.sub(r'<dimension ref="[^"]*"/>', f'<dimension ref="A1:O{last}"/>', xml)
    xml = re.sub(r"<xm:sqref>[^<]*</xm:sqref>", "", xml)  # (por si acaso)
    xml = re.sub(r'sqref="C2:J\d+"', f'sqref="C2:J{last}"', xml)
    xml = re.sub(r'sqref="A2:A\d+"', f'sqref="A2:A{last}"', xml)

    replacements = {
        sp: xml.encode("utf-8"),
        "xl/workbook.xml": _force_full_recalc(
            src.read("xl/workbook.xml").decode("utf-8")
        ).encode("utf-8"),
    }
    if tp:
        t = src.read(tp).decode("utf-8")
        t = re.sub(r'(<table[^>]*\sref=")[^"]*(")', rf"\g<1>A1:O{last}\g<2>", t)
        t = re.sub(r'(<autoFilter\s+ref=")[^"]*(")', rf"\g<1>A1:O{last}\g<2>", t)
        replacements[tp] = t.encode("utf-8")
    return _apply(src, replacements)
