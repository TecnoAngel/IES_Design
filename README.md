# IES Manager

Aplicación Streamlit para la gestión del día a día del departamento, con la misma
estructura que IES Creator.

## Requisitos

- Python 3.10+
- Windows para la parte de Word/Excel

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

```bash
streamlit run app.py
```

o `run_app.bat` (usa el puerto 8502 para no chocar con IES Creator).

## Funcionalidades

- **Situaciones de aprendizaje**: editor tipo hoja de cálculo (añadir / quitar /
  modificar filas) de la tabla `tablaSAprendizaje` de la hoja
  `SituacionesAprendizaje`, con panel de horas previstas vs. acumuladas por
  trimestre y aviso si te pasas. Al guardar se reescriben **solo** las partes
  mínimas del `.xlsx` (edición quirúrgica sobre el ZIP), conservando intactos el
  modelo de Power Pivot, las tablas dinámicas y el formato condicional.
- **Programación de aula**: genera el documento Word de la programación de aula a
  partir de un Excel con los datos del grupo y las situaciones de aprendizaje.

Las pestañas se irán reorganizando y ampliando.

## Nota técnica

`openpyxl` / `pandas` **no** sirven para *escribir* estos libros: al guardar
eliminan el modelo de datos, las dinámicas y las segmentaciones (el archivo pasa
de ~690 KB a ~60 KB). Para leer sí se usan sin problema. La escritura se hace en
`tools/situaciones_aprendizaje.py` manipulando el XML del ZIP directamente.
