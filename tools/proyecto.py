"""Proyecto del docente: un archivo SQLite con lo que es suyo (no el currículo).

La materia elegida (``meta.materia_id``) apunta a ``curriculo.db``; aquí solo
van las situaciones de aprendizaje, los pesos P de los criterios, los
indicadores de logro, las actividades, los datos de la programación de aula y
los textos de información a familias. Todos los códigos (CE, contenidos,
transversales, descriptores) deben existir en el currículo de esa materia: lo
comprueba ``consistencia.revisar``.

El proyecto se sube al empezar y se descarga al guardar: ``leer_proyecto``
convierte los bytes en el «estado» que usa la app y ``guardar_proyecto`` hace
lo contrario (escribe una base nueva en memoria y la serializa).

Estado (dict)::

    materia_id, sello
    situaciones          [{"SA", "EV", "DSA", "HSA"}]
    horas_previstas      {1: h, 2: h, 3: h}
    fechas_trimestre     {1: (date|None, date|None), ...}
    horas_dia            [L, M, X, J, V]
    festivo_local        date | None
    ce_p                 {CE: P}
    il_rows              [{"CE", "PIL", "DIL", "DO", "CON", "CT", "IE", "CC", "AE", "SA"}]
    pa_datos             {campo: valor}         (orden: DATOS_CAMPOS)
    pa_sa_cols           [{"nombre", "valores": {campo: valor}}]  una por SA
    pa_acts              [{"id", "SA", "IE", "titulo", "ils": [{"IL", "PA"}]}]
                         (ver tools.programacion_aula_editor)
    pa_acts_antiguas     [{"IL", "DA", "PA"}]  solo al leer un proyecto con
                         actividades de un único IL (schema 1); la app las
                         convierte con ``desde_formato_antiguo``
    fam_campos           {clave: texto}
"""

from __future__ import annotations

import re
import sqlite3
from datetime import date, datetime

SCHEMA_VERSION = "2"

# Campos de «Datos generales» y de cada SA en la programación de aula (los
# que usa la plantilla Word; mismo orden que tenían las hojas del Excel).
DATOS_CAMPOS = [
    "materia", "curso", "grupo", "docente", "numero_alumnos",
    "alumnos_atencion_individualizada", "caracteristicas_fisicas_cognitivas_afectivas",
    "nivel_competencia_curricular", "otras_caracteristicas_grupo",
    "resultados_evaluacion_inicial", "conclusiones_evaluacion_inicial",
    "resultados_evaluacion_aprendizajes", "revision_programacion",
]
SA_CAMPOS = [
    "titulo", "trimestre", "contextualizacion", "contenidos_materia",
    "contenidos_transversales", "aprendizaje_interdisciplinar", "metodos",
    "organizacion_alumnado", "cronograma", "organizacion_espacio",
    "materiales_recursos", "atencion_diferencias", "medidas_especificas",
    "proceso_evaluacion", "puesta_en_practica", "valoracion",
]
IL_CAMPOS = ["CE", "PIL", "DIL", "DO", "CON", "CT", "IE", "CC", "AE", "SA"]

_SCHEMA = """
CREATE TABLE meta (clave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE config (clave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE situaciones (
  numero INTEGER PRIMARY KEY, ev INTEGER, titulo TEXT NOT NULL DEFAULT '',
  horas REAL, orden INTEGER NOT NULL
);
CREATE TABLE situacion_campos (
  numero INTEGER NOT NULL REFERENCES situaciones(numero) ON DELETE CASCADE,
  campo TEXT NOT NULL, valor TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (numero, campo)
);
CREATE TABLE criterios_peso (ce TEXT PRIMARY KEY, peso REAL NOT NULL DEFAULT 0);
CREATE TABLE indicadores (
  orden INTEGER PRIMARY KEY, ce TEXT NOT NULL, pil REAL,
  descripcion TEXT NOT NULL DEFAULT '', descriptores TEXT NOT NULL DEFAULT '',
  contenidos TEXT NOT NULL DEFAULT '', transversales TEXT NOT NULL DEFAULT '',
  ie TEXT NOT NULL DEFAULT '', cc TEXT NOT NULL DEFAULT '', ae TEXT NOT NULL DEFAULT '',
  sa INTEGER
);
CREATE TABLE actividades (
  id INTEGER PRIMARY KEY, orden INTEGER NOT NULL, sa INTEGER,
  ie TEXT NOT NULL DEFAULT '', titulo TEXT NOT NULL DEFAULT ''
);
CREATE TABLE actividad_indicadores (
  actividad INTEGER NOT NULL REFERENCES actividades(id) ON DELETE CASCADE,
  il TEXT NOT NULL, peso REAL, orden INTEGER NOT NULL,
  PRIMARY KEY (actividad, il)
);
CREATE TABLE datos_generales (campo TEXT PRIMARY KEY, valor TEXT NOT NULL DEFAULT '');
CREATE TABLE familias (campo TEXT PRIMARY KEY, valor TEXT NOT NULL DEFAULT '');
"""


def _s(v) -> str:
    return "" if v is None else str(v).strip()


def _num(v):
    if v in (None, ""):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return int(f) if f.is_integer() else f


def _fecha(v) -> date | None:
    if not v:
        return None
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v))
    except ValueError:
        return None


def norm_titulo(v) -> str:
    return re.sub(r"\s+", " ", _s(v)).lower()


def trimestre_txt(ev) -> str:
    try:
        n = int(ev)
    except (TypeError, ValueError):
        return ""
    return f"{n}º trimestre" if n in (1, 2, 3) else ""


# ---------------------------------------------------------------------------
# Nuevo
# ---------------------------------------------------------------------------
def estado_vacio(curriculo: dict) -> dict:
    """Proyecto nuevo para una materia (``curriculo`` = ``cargar_materia``):
    sin situaciones ni indicadores y con peso P = 1 en todos los criterios."""
    m = curriculo["materia"]
    from tools.curriculo import ETAPA_NOMBRE

    datos = {k: "" for k in DATOS_CAMPOS}
    datos["materia"] = m["nombre"]
    datos["curso"] = f"{m['curso']}º {ETAPA_NOMBRE.get(m['etapa_app'], m['etapa'])}"
    return {
        "materia_id": m["id"],
        "sello": "",
        "situaciones": [],
        "horas_previstas": {1: 0.0, 2: 0.0, 3: 0.0},
        "fechas_trimestre": {1: (None, None), 2: (None, None), 3: (None, None)},
        "horas_dia": [None] * 5,
        "festivo_local": None,
        "ce_p": {ce: 1 for ce in curriculo["ce_list"]},
        "il_rows": [],
        "pa_datos": datos,
        "pa_sa_cols": [],
        "pa_acts": [],
        "fam_campos": {},
    }


# ---------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------
def _abrir(payload: bytes) -> sqlite3.Connection:
    if not payload.startswith(b"SQLite format 3\x00"):
        raise ValueError("El archivo no es un proyecto de IES Diseño (no es una base SQLite).")
    con = sqlite3.connect(":memory:")
    con.deserialize(payload)
    return con


def leer_meta(payload: bytes) -> dict:
    con = _abrir(payload)
    try:
        return dict(con.execute("SELECT clave, valor FROM meta"))
    except sqlite3.DatabaseError as exc:
        raise ValueError("El archivo no es un proyecto de IES Diseño.") from exc
    finally:
        con.close()


def leer_proyecto(payload: bytes) -> dict:
    con = _abrir(payload)
    try:
        meta = dict(con.execute("SELECT clave, valor FROM meta"))
        if not meta.get("materia_id"):
            raise ValueError("El proyecto no indica su materia.")
        cfg = dict(con.execute("SELECT clave, valor FROM config"))

        sits = [
            {"SA": n, "EV": ev, "DSA": t or "", "HSA": _num(h)}
            for n, ev, t, h in con.execute(
                "SELECT numero, ev, titulo, horas FROM situaciones ORDER BY orden"
            )
        ]
        campos_sa: dict[int, dict[str, str]] = {}
        for n, campo, valor in con.execute("SELECT numero, campo, valor FROM situacion_campos"):
            campos_sa.setdefault(n, {})[campo] = valor
        pa_sa_cols = []
        for s in sits:
            vals = dict(campos_sa.get(s["SA"], {}))
            vals["titulo"] = s["DSA"]
            vals["trimestre"] = trimestre_txt(s["EV"])
            pa_sa_cols.append({"nombre": f"Situación {s['SA']}", "valores": vals})

        il_rows = [
            dict(zip(IL_CAMPOS, (ce, _num(pil), d, do, con_, ct, ie, cc, ae, sa)))
            for ce, pil, d, do, con_, ct, ie, cc, ae, sa in con.execute(
                "SELECT ce, pil, descripcion, descriptores, contenidos, transversales, "
                "ie, cc, ae, sa FROM indicadores ORDER BY orden"
            )
        ]
        acts, antiguas = [], []
        cols_act = {c[1] for c in con.execute("PRAGMA table_info(actividades)")}
        if "il" in cols_act:  # schema 1: una actividad = un IL
            antiguas = [
                {"IL": il, "DA": d, "PA": _num(p)}
                for il, d, p in con.execute(
                    "SELECT il, descripcion, peso FROM actividades ORDER BY orden"
                )
            ]
        else:
            por_id = {}
            for i, sa, ie, t in con.execute(
                "SELECT id, sa, ie, titulo FROM actividades ORDER BY orden"
            ):
                por_id[i] = {"id": i, "SA": sa, "IE": ie or "", "titulo": t or "", "ils": []}
                acts.append(por_id[i])
            for a, il, p in con.execute(
                "SELECT actividad, il, peso FROM actividad_indicadores ORDER BY actividad, orden"
            ):
                if a in por_id:
                    por_id[a]["ils"].append({"IL": il, "PA": _num(p)})
        datos = {k: "" for k in DATOS_CAMPOS}
        datos.update(dict(con.execute("SELECT campo, valor FROM datos_generales")))

        return {
            "materia_id": meta["materia_id"],
            "sello": meta.get("actualizado", ""),
            "situaciones": sits,
            "horas_previstas": {t: float(_num(cfg.get(f"horas_previstas_{t}")) or 0) for t in (1, 2, 3)},
            "fechas_trimestre": {
                t: (_fecha(cfg.get(f"fecha_ini_{t}")), _fecha(cfg.get(f"fecha_fin_{t}")))
                for t in (1, 2, 3)
            },
            "horas_dia": [_num(cfg.get(f"horas_dia_{i}")) for i in range(5)],
            "festivo_local": _fecha(cfg.get("festivo_local")),
            "ce_p": {ce: _num(p) or 0 for ce, p in con.execute("SELECT ce, peso FROM criterios_peso")},
            "il_rows": il_rows,
            "pa_datos": datos,
            "pa_sa_cols": pa_sa_cols,
            "pa_acts": acts,
            "pa_acts_antiguas": antiguas,
            "fam_campos": dict(con.execute("SELECT campo, valor FROM familias")),
        }
    except sqlite3.DatabaseError as exc:
        raise ValueError(f"El archivo no es un proyecto de IES Diseño válido: {exc}") from exc
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Escritura
# ---------------------------------------------------------------------------
def guardar_proyecto(
    estado: dict,
    materia: dict,
    *,
    pa_sa_edits: dict[str, dict[str, str]] | None = None,
) -> tuple[bytes, str]:
    """Bytes del proyecto (base SQLite nueva) y el sello de fecha-hora.

    Los campos de aula de cada SA se toman por título (``pa_sa_edits`` de la
    sesión o, si no, ``estado["pa_sa_cols"]``); título y trimestre siempre de
    la tabla de situaciones, que es la que manda."""
    sello = datetime.now().strftime("%d/%m/%Y %H:%M")
    edits = {norm_titulo(k): v for k, v in (pa_sa_edits or {}).items()}
    previos = {
        norm_titulo(c.get("valores", {}).get("titulo")): c.get("valores", {})
        for c in estado.get("pa_sa_cols", [])
    }

    con = sqlite3.connect(":memory:")
    try:
        with con:
            con.executescript(_SCHEMA)
            meta = {
                "schema_version": SCHEMA_VERSION,
                "materia_id": materia["id"],
                "materia_nombre": materia["nombre"],
                "etapa": materia.get("etapa_app", materia["etapa"]),
                "curso": str(materia["curso"]),
                "normativa": materia.get("normativa") or "",
                "actualizado": sello,
            }
            con.executemany("INSERT INTO meta VALUES (?, ?)", meta.items())

            cfg: dict[str, str] = {}
            for t in (1, 2, 3):
                cfg[f"horas_previstas_{t}"] = str(estado.get("horas_previstas", {}).get(t, 0) or 0)
                ini, fin = estado.get("fechas_trimestre", {}).get(t, (None, None))
                cfg[f"fecha_ini_{t}"] = ini.isoformat() if ini else ""
                cfg[f"fecha_fin_{t}"] = fin.isoformat() if fin else ""
            for i, h in enumerate((estado.get("horas_dia") or [None] * 5)[:5]):
                cfg[f"horas_dia_{i}"] = "" if h in (None, "") else str(h)
            fl = estado.get("festivo_local")
            cfg["festivo_local"] = fl.isoformat() if fl else ""
            con.executemany("INSERT INTO config VALUES (?, ?)", cfg.items())

            vistos: set[int] = set()
            for orden, s in enumerate(estado.get("situaciones", [])):
                n = s.get("SA")
                if n in (None, "") or int(n) in vistos:
                    continue  # sin nº o repetida: la validación de la app ya avisa
                n = int(n)
                vistos.add(n)
                titulo = _s(s.get("DSA"))
                con.execute(
                    "INSERT INTO situaciones VALUES (?, ?, ?, ?, ?)",
                    (n, _num(s.get("EV")), titulo, _num(s.get("HSA")), orden),
                )
                vals = edits.get(norm_titulo(titulo)) or previos.get(norm_titulo(titulo)) or {}
                con.executemany(
                    "INSERT INTO situacion_campos VALUES (?, ?, ?)",
                    [
                        (n, campo, _s(v))
                        for campo, v in vals.items()
                        if campo not in ("titulo", "trimestre") and _s(v)
                    ],
                )

            con.executemany(
                "INSERT INTO criterios_peso VALUES (?, ?)",
                [(ce, float(p or 0)) for ce, p in estado.get("ce_p", {}).items()],
            )
            con.executemany(
                "INSERT INTO indicadores VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        i, _s(r.get("CE")), _num(r.get("PIL")), _s(r.get("DIL")),
                        _s(r.get("DO")), _s(r.get("CON")), _s(r.get("CT")),
                        _s(r.get("IE")), _s(r.get("CC")), _s(r.get("AE")),
                        None if r.get("SA") in (None, "") else int(r["SA"]),
                    )
                    for i, r in enumerate(estado.get("il_rows", []))
                ],
            )
            for orden, a in enumerate(estado.get("pa_acts", [])):
                con.execute(
                    "INSERT INTO actividades VALUES (?, ?, ?, ?, ?)",
                    (int(a["id"]), orden, _num(a.get("SA")), _s(a.get("IE")), _s(a.get("titulo"))),
                )
                vistos_il: set[str] = set()
                for j, e in enumerate(a.get("ils", [])):
                    il = _s(e.get("IL"))
                    if il and il not in vistos_il:
                        vistos_il.add(il)
                        con.execute(
                            "INSERT INTO actividad_indicadores VALUES (?, ?, ?, ?)",
                            (int(a["id"]), il, _num(e.get("PA")), j),
                        )
            con.executemany(
                "INSERT INTO datos_generales VALUES (?, ?)",
                [(k, _s(v)) for k, v in estado.get("pa_datos", {}).items()],
            )
            con.executemany(
                "INSERT INTO familias VALUES (?, ?)",
                [(k, _s(v)) for k, v in estado.get("fam_campos", {}).items()],
            )
        return con.serialize(), sello
    finally:
        con.close()
