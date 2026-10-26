"""Currículo común (``curriculo.db``): materias de ESO, Diversificación y
Bachillerato de Castilla y León con sus criterios de evaluación, competencias
específicas, contenidos, transversales, descriptores operativos y los
catálogos de instrumentos (IE), criterios de calificación (CC) y agentes (AE).

La base vive en GitHub y la app la descarga sola (``obtener_curriculo``); aquí
solo se LEE. Lo que es de cada docente va en su proyecto (ver ``proyecto``).

Etapas de la app:

* ``ESO``   materias con ``etapa='ESO'`` salvo los ámbitos de Diversificación;
* ``DIVER`` los ámbitos (``normativa = 'Orden EDU/1332/2023'``, 3º y 4º), que
  en la base figuran como ESO y usan sus transversales y descriptores;
* ``BACH``  Bachillerato.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path

CURRICULO_URL = "https://raw.githubusercontent.com/TecnoAngel/IES_Design/master/curriculo.db"
LOCAL_DB = Path(__file__).resolve().parent.parent / "curriculo.db"
CACHE_DIR = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".cache") / "IES_Diseno"

ETAPAS = ["ESO", "DIVER", "BACH"]
ETAPA_NOMBRE = {"ESO": "ESO", "DIVER": "Diversificación (ESO)", "BACH": "Bachillerato"}
NORMATIVA_DIVER = "Orden EDU/1332/2023"


# ---------------------------------------------------------------------------
# Descarga
# ---------------------------------------------------------------------------
def _es_sqlite(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(16) == b"SQLite format 3\x00"
    except OSError:
        return False


def obtener_curriculo(url: str = CURRICULO_URL, timeout: float = 20) -> tuple[Path, str]:
    """Descarga ``curriculo.db`` de GitHub a la caché local y devuelve
    ``(ruta, origen)``. Sin red (o si lo descargado no es una base SQLite) usa
    la última copia en caché y, si no hay, la del propio repositorio."""
    destino = CACHE_DIR / "curriculo.db"
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            datos = resp.read()
        fd, tmp = tempfile.mkstemp(dir=CACHE_DIR, suffix=".db")
        with os.fdopen(fd, "wb") as f:
            f.write(datos)
        if not _es_sqlite(Path(tmp)):
            os.remove(tmp)
            raise ValueError("lo descargado no es una base SQLite")
        os.replace(tmp, destino)
        return destino, f"GitHub · descargado {datetime.now():%d/%m/%Y %H:%M}"
    except Exception as exc:
        if _es_sqlite(destino):
            fecha = datetime.fromtimestamp(destino.stat().st_mtime)
            return destino, f"copia en caché del {fecha:%d/%m/%Y %H:%M} (no se pudo descargar: {exc})"
        if _es_sqlite(LOCAL_DB):
            return LOCAL_DB, f"copia local del repositorio (no se pudo descargar: {exc})"
        raise RuntimeError(f"No se puede obtener curriculo.db: {exc}") from exc


def _con(db: Path | str) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True)


# ---------------------------------------------------------------------------
# Selección etapa → curso → materia
# ---------------------------------------------------------------------------
def _filtro_etapa(etapa: str) -> tuple[str, tuple]:
    if etapa == "DIVER":
        return "etapa = 'ESO' AND normativa = ?", (NORMATIVA_DIVER,)
    if etapa == "ESO":
        return "etapa = 'ESO' AND COALESCE(normativa, '') <> ?", (NORMATIVA_DIVER,)
    return "etapa = ?", (etapa,)


def etapa_de(materia: dict) -> str:
    return "DIVER" if materia.get("normativa") == NORMATIVA_DIVER else materia["etapa"]


def cursos(db, etapa: str) -> list[int]:
    w, p = _filtro_etapa(etapa)
    with _con(db) as c:
        return [r[0] for r in c.execute(f"SELECT DISTINCT curso FROM materias WHERE {w} ORDER BY curso", p)]


def materias(db, etapa: str, curso: int) -> list[dict]:
    w, p = _filtro_etapa(etapa)
    with _con(db) as c:
        rows = c.execute(
            f"SELECT id, nombre, etapa, curso, normativa FROM materias WHERE {w} AND curso = ? "
            "ORDER BY nombre", p + (int(curso),),
        ).fetchall()
    return [dict(zip(("id", "nombre", "etapa", "curso", "normativa"), r)) for r in rows]


def materia(db, materia_id: str) -> dict | None:
    with _con(db) as c:
        r = c.execute(
            "SELECT id, nombre, etapa, curso, normativa FROM materias WHERE id = ?", (materia_id,)
        ).fetchone()
    if not r:
        return None
    m = dict(zip(("id", "nombre", "etapa", "curso", "normativa"), r))
    m["etapa_app"] = etapa_de(m)
    return m


# ---------------------------------------------------------------------------
# Currículo de una materia
# ---------------------------------------------------------------------------
def cargar_materia(db, materia_id: str) -> dict:
    """Todo el currículo de una materia, con las mismas estructuras que antes
    se leían del Excel (``ce_list``, ``ce_ced``, ``elementos``, ``aux``) más lo
    nuevo (competencias específicas, descriptores por criterio)."""
    m = materia(db, materia_id)
    if m is None:
        raise ValueError(f"La materia '{materia_id}' no está en curriculo.db.")
    with _con(db) as c:
        crit = c.execute(
            "SELECT codigo, ce_numero, descripcion FROM criterios WHERE materia_id = ? ORDER BY orden",
            (materia_id,),
        ).fetchall()
        comp = c.execute(
            "SELECT numero, descripcion, descriptores FROM competencias_especificas "
            "WHERE materia_id = ? ORDER BY numero", (materia_id,),
        ).fetchall()
        ce_do: dict[str, list[str]] = {}
        for ce, d in c.execute(
            "SELECT criterio, descriptor FROM criterio_descriptores WHERE materia_id = ? "
            "ORDER BY criterio, orden", (materia_id,),
        ):
            ce_do.setdefault(ce, []).append(d)
        cont = c.execute(
            "SELECT codigo, descripcion, bloque FROM contenidos WHERE materia_id = ? ORDER BY orden",
            (materia_id,),
        ).fetchall()
        # Transversales y descriptores: de la etapa real de la base (DIVER = ESO).
        trans = c.execute(
            "SELECT numero, descripcion FROM transversales WHERE etapa = ? ORDER BY numero",
            (m["etapa"],),
        ).fetchall()
        desc = c.execute(
            "SELECT codigo, competencia, COALESCE(descripcion, '') FROM descriptores WHERE etapa = ?",
            (m["etapa"],),
        ).fetchall()
        aux: dict[str, list[str]] = {"IE": [], "CC": [], "AE": []}
        for tipo, valor in c.execute("SELECT tipo, valor FROM catalogos ORDER BY tipo, orden"):
            aux.setdefault(tipo, []).append(valor)

    return {
        "materia": m,
        "ce_list": [r[0] for r in crit],
        "ce_ced": {r[0]: r[2] for r in crit},
        "ce_comp": {r[0]: r[1] for r in crit},
        "ce_do": ce_do,
        "competencias": {str(r[0]): r[1] for r in comp},
        "comp_descriptores": {str(r[0]): r[2] or "" for r in comp},
        "elementos": {
            "contenidos": [{"cod": r[0], "desc": r[1], "bloque": r[2] or ""} for r in cont],
            "transversales": [{"num": str(r[0]), "desc": r[1]} for r in trans],
            "descriptores": [
                {"cod": r[0], "desc": r[2], "competencia": r[1]} for r in _orden_descriptores(desc)
            ],
        },
        "aux": aux,
    }


_ORDEN_COMPETENCIAS = ["CCL", "CP", "STEM", "CD", "CPSAA", "CC", "CE", "CCEC"]


def _orden_descriptores(rows):
    def key(r):
        cod, comp = r[0], r[1]
        num = "".join(ch for ch in cod if ch.isdigit())
        rank = _ORDEN_COMPETENCIAS.index(comp) if comp in _ORDEN_COMPETENCIAS else 99
        return (rank, int(num) if num else 0, cod)

    return sorted(rows, key=key)
