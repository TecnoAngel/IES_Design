# IES Diseño

Aplicación Streamlit para diseñar y revisar la programación didáctica (LOMLOE) y
la programación de aula a partir del **Excel de programación** del departamento,
sin romper su modelo de Power Pivot ni sus tablas dinámicas.

## Requisitos

- Python 3.10+
- Windows (probado ahí; el Excel se abre después con Microsoft Excel)
- Chrome o Edge recomendados (permiten elegir dónde guardar el Excel, incluso
  sobrescribiendo el original; en Firefox/Safari se descarga sin más)

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

o `run_app.bat` (usa el python del `.venv` y el puerto 8502).

## Uso

1. Sube el Excel de programación (`.xlsx`) en la barra de arriba.
2. Edita en las páginas de la barra lateral.
3. Pulsa **Guardar Excel**: se genera el mismo libro con tus cambios y un
   prefijo `AAAAMMDD_HHMM_` en el nombre. Dentro del archivo queda también un
   sello oculto con la fecha y la hora del guardado.

Antes de guardar o generar el Word se revisa la coherencia entre tablas (la
tabla de situaciones de aprendizaje manda). Si algo no cuadra, puedes parar y
arreglarlo en Excel o regenerar automáticamente lo que falte.

## Funcionalidades

### Diseño de la programación

- **Situaciones de aprendizaje**: tabla SA / evaluación / descripción / horas,
  horas previstas vs. planificadas por trimestre y % de horas con gráfico de
  sectores (copiables a Word).
- **Sesiones por evaluación**: descarga el calendario escolar oficial de
  Castilla y León y cuenta, día a día, los días lectivos y las sesiones de cada
  evaluación. Las fechas, las sesiones por día y el festivo local se guardan en
  el Excel. El resultado se puede volcar a las horas previstas.
- **Criterios de evaluación**: edición del peso P de cada criterio (%CE automático).
- **Indicadores de logro**: alta y baja por criterio, numeración automática, PIL%,
  contenidos y transversales marcados con ticks, instrumento, calificación,
  agente y SA en desplegables. Resumen por criterio copiable a Word.
- **Ajuste de pesos**: fijas el % objetivo de cada instrumento de evaluación y,
  con el reparto horario, se sugieren P y PIL (ajuste IPF). Tú decides si los cargas.
- **Distribución CE × SA**: matriz de pesos por criterio y situación,
  comparada con el reparto de horas.
- **Peso final por instrumento**: tabla y gráfico del peso acumulado de cada
  instrumento de evaluación.

### Contenidos

Contenidos de la materia y transversales de la hoja `LOMLOE`, marcados en verde
si ya están asignados a algún indicador y en rojo si no.

### Programación de aula

- **Datos generales** del grupo.
- **Actividades por situación de aprendizaje**: actividades de cada indicador con
  peso, PA% y factor; resumen de su valor sobre la programación y sobre la SA;
  y los campos de la programación de aula de esa SA.
- **Generar programación de aula (Word)** con la plantilla por defecto
  (`templates/programacion_aula_template.docx`) o con una propia.

### Información a familias

Genera un Word para informar al alumnado y a las familias sobre la evaluación
(ORDEN EDU/424/2024, art. 12 · ORDEN EDU/425/2024, art. 10):

- competencias específicas, criterios de evaluación con su peso, resumen por
  criterio, contenidos y su temporalización;
- instrumentos de evaluación (tabla y gráfico);
- criterios de calificación (redondeo, competencias clave), promoción y
  titulación, y medidas de atención individualizada;
- una página por situación de aprendizaje: criterios e indicadores de logro que
  se trabajan (sin el texto del indicador) con sus pesos, instrumento,
  calificación, agente, contenidos y transversales, y la tarta de instrumentos de
  esa SA.

Los textos que no están en el resto del Excel (competencias específicas,
redondeo, promoción, medidas…) se rellenan en la app y se guardan en la hoja
`Info_Familias`. Esa hoja se crea sola al guardar, solo si has escrito algo.
Plantilla por defecto: `templates/informacion_familias_template.docx`; para
regenerarla, ejecuta `python -m tools.plantilla_familias`.

## Nota técnica

`openpyxl` / `pandas` **no** sirven para *escribir* estos libros: al guardar
eliminan el modelo de datos, las dinámicas y las segmentaciones (el archivo pasa
de ~690 KB a ~60 KB). Para leer sí se usan sin problema. La escritura se hace en
los módulos de `tools/` modificando directamente el XML de las partes afectadas
dentro del ZIP. El resto del archivo se copia tal cual y se fuerza el recálculo al
abrirlo en Excel.

Más detalle interno (estructura del Excel, decisiones, trampas conocidas,
bitácora): ver [MEMORIA.md](MEMORIA.md).
