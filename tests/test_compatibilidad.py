"""Pruebas de compatibilidad del archivo de proyecto (.sqlite).

Se ejecutan con::

    .venv\\Scripts\\python.exe -m unittest discover -s tests -v

Protegen la regla de oro del proyecto: **lo que un docente ya ha guardado no se
pierde ni deja de abrirse porque la app cambie**. Para ello:

* ``tests/esquemas/schema_N.sql`` son los esquemas **congelados** de cada versión
  que ha existido. No se editan nunca: si el esquema cambia, se añade
  ``schema_<N+1>.sql`` y se lista abajo en ``ESQUEMAS``.
* Cada esquema antiguo se rellena con datos de prueba, se abre con la app actual,
  se guarda y se vuelve a abrir: los datos tienen que seguir ahí.
* El esquema actual (``tools.proyecto._SCHEMA``) tiene que contener todas las
  tablas y columnas del último esquema congelado (**solo se añade**).
* Un archivo con tablas, columnas y tipos de redacción que esta versión no conoce
  tiene que abrirse igualmente.
"""

from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

from tools import proyecto

ESQUEMAS = {1: "schema_1.sql", 2: "schema_2.sql", 3: "schema_3.sql"}
CARPETA = Path(__file__).parent / "esquemas"
MATERIA = {"id": "TEST-1BACH", "nombre": "Materia de prueba", "etapa": "BACH", "curso": 1,
           "normativa": "Decreto de prueba", "etapa_app": "BACH"}


def _columnas(con: sqlite3.Connection) -> dict[str, set[str]]:
    tablas = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
    return {t: {c[1] for c in con.execute(f"PRAGMA table_info({t})")} for t in tablas}


def _archivo(version: int, extra: str = "") -> bytes:
    """Proyecto de prueba con el esquema congelado de la versión ``version``."""
    con = sqlite3.connect(":memory:")
    con.executescript((CARPETA / ESQUEMAS[version]).read_text(encoding="utf8"))
    con.executemany("INSERT INTO meta VALUES (?, ?)", [
        ("schema_version", str(version)), ("materia_id", MATERIA["id"]),
        ("materia_nombre", MATERIA["nombre"]), ("etapa", "BACH"), ("curso", "1"),
        ("normativa", ""), ("actualizado", "01/01/2026 10:00"),
    ])
    con.execute("INSERT INTO config VALUES ('horas_previstas_1', '30')")
    con.execute("INSERT INTO situaciones VALUES (1, 1, 'Primera SA', 12, 0)")
    con.execute("INSERT INTO situacion_campos VALUES (1, 'metodos', 'Aprendizaje cooperativo')")
    con.execute("INSERT INTO criterios_peso VALUES ('1.1', 10)")
    con.execute("INSERT INTO indicadores VALUES (0, '1.1', 2, 'Indicador uno', 'CCL1', 'A.1.1', '1', 'Examen', 'Nota', 'Profesor', 1)")
    if version == 1:
        con.execute("INSERT INTO actividades VALUES (0, '1.1.1', 'Actividad antigua', 100)")
    else:
        con.execute("INSERT INTO actividades VALUES (1, 0, 1, 'Examen', 'Prueba escrita')")
        con.execute("INSERT INTO actividad_indicadores VALUES (1, '1.1.1', 60, 0)")
    con.execute("INSERT INTO datos_generales VALUES ('grupo', '1ºA')")
    con.execute("INSERT INTO familias VALUES ('apoyos', 'Apoyo en el aula')")
    if version >= 3:
        con.execute("INSERT INTO redaccion VALUES ('a_marco', 'texto', 'Marco legal propio')")
        con.execute("INSERT INTO redaccion VALUES ('k_instrumentos', 'opcion', '1')")
        con.execute("INSERT INTO redaccion VALUES ('k', 'extra', ?)",
                    ('[{"id": 1, "nivel": 1, "encabezado": "Mi apartado", "texto": "Mi texto"}]',))
        con.execute("INSERT INTO categorias VALUES (1, 'Destrezas', 0)")
        con.execute("INSERT INTO categoria_opciones VALUES (2, 1, 'Reading', 0)")
        con.execute("INSERT INTO indicador_categoria VALUES (0, 1, 2)")
    if extra:
        con.executescript(extra)
    con.commit()
    return con.serialize()


def _comprueba_datos(test: unittest.TestCase, est: dict, version: int) -> None:
    test.assertEqual(est["materia_id"], MATERIA["id"])
    test.assertEqual(est["situaciones"][0]["DSA"], "Primera SA")
    test.assertEqual(est["pa_sa_cols"][0]["valores"]["metodos"], "Aprendizaje cooperativo")
    test.assertEqual(est["ce_p"], {"1.1": 10})
    test.assertEqual(est["il_rows"][0]["DIL"], "Indicador uno")
    test.assertEqual(est["il_rows"][0]["IE"], "Examen")
    test.assertEqual(est["pa_datos"]["grupo"], "1ºA")
    test.assertEqual(est["fam_campos"]["apoyos"], "Apoyo en el aula")
    if version == 1:
        test.assertEqual(est["pa_acts_antiguas"][0]["DA"], "Actividad antigua")
    else:
        test.assertEqual(est["pa_acts"][0]["titulo"], "Prueba escrita")
        test.assertEqual(est["pa_acts"][0]["ils"][0], {"IL": "1.1.1", "PA": 60})
    if version >= 3:
        test.assertEqual(est["redaccion"]["textos"]["a_marco"], "Marco legal propio")
        test.assertTrue(est["redaccion"]["opciones"]["k_instrumentos"])
        test.assertEqual(est["redaccion"]["extras"]["k"][0]["encabezado"], "Mi apartado")
        test.assertEqual(est["categorias"][0]["nombre"], "Destrezas")
        test.assertEqual(est["il_rows"][0]["CAT"], {1: 2})


class CompatibilidadProyecto(unittest.TestCase):
    def test_cada_esquema_antiguo_se_abre_y_se_guarda_sin_perder_datos(self):
        for version in ESQUEMAS:
            with self.subTest(schema=version):
                est = proyecto.leer_proyecto(_archivo(version))
                _comprueba_datos(self, est, version)
                if version == 1:  # la app convierte las actividades antiguas al abrir
                    est["pa_acts"] = []
                guardado, _sello = proyecto.guardar_proyecto(est, MATERIA)
                est2 = proyecto.leer_proyecto(guardado)
                for clave in est:
                    if clave in ("sello", "pa_acts_antiguas"):
                        continue
                    self.assertEqual(est[clave], est2[clave], f"cambia «{clave}» al guardar")

    def test_el_esquema_actual_solo_anade_al_ultimo_congelado(self):
        """Regla «solo se añade»: no desaparece ni se renombra ninguna tabla o columna."""
        actual = sqlite3.connect(":memory:")
        actual.executescript(proyecto._SCHEMA)
        ultimo = sqlite3.connect(":memory:")
        ultimo.executescript((CARPETA / ESQUEMAS[max(ESQUEMAS)]).read_text(encoding="utf8"))
        cols_actual, cols_ultimo = _columnas(actual), _columnas(ultimo)
        for tabla, cols in cols_ultimo.items():
            self.assertIn(tabla, cols_actual, f"falta la tabla «{tabla}»")
            self.assertLessEqual(cols, cols_actual[tabla], f"faltan columnas en «{tabla}»")

    def test_la_version_actual_tiene_su_esquema_congelado(self):
        self.assertIn(int(proyecto.SCHEMA_VERSION), ESQUEMAS,
                      "SCHEMA_VERSION no tiene su tests/esquemas/schema_N.sql")

    def test_un_archivo_de_una_version_futura_se_abre(self):
        """Tablas, columnas y tipos de redacción que esta versión no conoce se ignoran."""
        extra = """
            ALTER TABLE indicadores ADD COLUMN novedad TEXT DEFAULT '';
            CREATE TABLE tabla_futura (a TEXT, b TEXT);
            INSERT INTO tabla_futura VALUES ('x', 'y');
            INSERT INTO redaccion VALUES ('algo_nuevo', 'tipo_futuro', 'valor');
            INSERT INTO redaccion VALUES ('otra', 'extra', 'esto no es json');
        """
        est = proyecto.leer_proyecto(_archivo(3, extra))
        _comprueba_datos(self, est, 3)

    def test_datos_huerfanos_se_descartan_sin_error(self):
        extra = """
            INSERT INTO indicador_categoria VALUES (0, 5, 999);
            INSERT INTO indicador_categoria VALUES (77, 1, 2);
        """
        est = proyecto.leer_proyecto(_archivo(3, extra))
        self.assertEqual(est["il_rows"][0]["CAT"], {1: 2})

    def test_un_archivo_que_no_es_un_proyecto_da_un_error_claro(self):
        with self.assertRaises(ValueError):
            proyecto.leer_proyecto(b"esto no es sqlite")


if __name__ == "__main__":
    unittest.main()
