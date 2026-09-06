"""Sello de fecha/hora y versión en el Excel al guardar.

Se guarda como un *nombre definido* oculto en ``xl/workbook.xml``
(``IES_DISENO_ACTUALIZADO``). Al volver a guardar:

* si la fecha-hora (al minuto) coincide con la del sello anterior → sube la
  versión (V1 → V2 → …);
* si no coincide → vuelve a empezar en V1 con la nueva fecha-hora.

Si el Excel cargado ya trae el sello, se borra y se pone el nuevo.
"""

from __future__ import annotations

import re
import zipfile
from datetime import datetime
from io import BytesIO

MARCA = "IES_DISENO_ACTUALIZADO"
_RE_DN = re.compile(rf'<definedName name="{MARCA}"[^>]*>.*?</definedName>', re.S)


def leer_sello(xlsx_bytes: bytes) -> str | None:
    try:
        wb = zipfile.ZipFile(BytesIO(xlsx_bytes)).read("xl/workbook.xml").decode("utf-8")
    except Exception:
        return None
    m = _RE_DN.search(wb)
    if not m:
        return None
    inner = re.sub(r"</?definedName[^>]*>", "", m.group(0)).strip().strip('"')
    return inner or None


def _parse(sello: str | None):
    if not sello:
        return None, 0
    md = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", sello)
    mv = re.search(r"[Vv](\d+)", sello)
    return (md.group(0) if md else None), (int(mv.group(1)) if mv else 0)


def etiqueta_archivo(sello: str) -> str:
    """'2026-09-06 18:45 · V1' -> '2026-09-06_18-45_V1' (para el nombre de fichero)."""
    s = sello.replace(":", "-")
    return re.sub(r"[^0-9A-Za-z-]+", "_", s).strip("_")


def sellar(xlsx_bytes: bytes, *, ahora: datetime | None = None) -> tuple[bytes, str]:
    """Devuelve (bytes con el sello nuevo, texto del sello)."""
    z = zipfile.ZipFile(BytesIO(xlsx_bytes))
    wb = z.read("xl/workbook.xml").decode("utf-8")

    prev_dt, prev_v = _parse(leer_sello(xlsx_bytes))
    momento = (ahora or datetime.now()).strftime("%Y-%m-%d %H:%M")
    version = prev_v + 1 if prev_dt == momento else 1
    sello = f"{momento} · V{version}"

    dn = f'<definedName name="{MARCA}" hidden="1">"{sello}"</definedName>'
    wb = _RE_DN.sub("", wb)
    if "<definedNames>" in wb:
        wb = wb.replace("<definedNames>", "<definedNames>" + dn, 1)
    elif "</sheets>" in wb:
        wb = wb.replace("</sheets>", "</sheets><definedNames>" + dn + "</definedNames>", 1)
    else:  # muy raro
        wb = wb.replace("</workbook>", "<definedNames>" + dn + "</definedNames></workbook>")

    out = BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for it in z.infolist():
            dst.writestr(
                it,
                wb.encode("utf-8") if it.filename == "xl/workbook.xml" else z.read(it.filename),
            )
    return out.getvalue(), sello
