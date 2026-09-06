"""Sello de fecha/hora en el Excel al guardar.

Se guarda como un *nombre definido* oculto en ``xl/workbook.xml``
(``IES_DISENO_ACTUALIZADO``), con la fecha-hora al minuto. Si el Excel cargado ya
lo trae, se borra y se pone el nuevo. El nombre de descarga lleva delante
``AAAAMMDD_HHMM_``.
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


def etiqueta_archivo(sello: str) -> str:
    """'2026-09-06 19:20' -> '20260906_1920' (prefijo del nombre de fichero)."""
    d = re.sub(r"\D", "", sello)
    if len(d) >= 12:
        return f"{d[:8]}_{d[8:12]}"
    return re.sub(r"[^0-9A-Za-z]+", "_", sello).strip("_")


def sellar(xlsx_bytes: bytes, *, ahora: datetime | None = None) -> tuple[bytes, str]:
    """Devuelve (bytes con el sello nuevo, texto del sello 'AAAA-MM-DD HH:MM')."""
    z = zipfile.ZipFile(BytesIO(xlsx_bytes))
    wb = z.read("xl/workbook.xml").decode("utf-8")

    sello = (ahora or datetime.now()).strftime("%Y-%m-%d %H:%M")

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
