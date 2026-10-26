# IES Diseño

Aplicación Streamlit para diseñar y revisar la programación didáctica (LOMLOE) y
la programación de aula sobre el **currículo de Castilla y León** (ESO,
Diversificación y Bachillerato).

- El currículo (criterios, competencias específicas, contenidos, transversales,
  descriptores, instrumentos…) está en `curriculo.db`, en este repositorio, y la
  app lo descarga sola.
- Cada programación es un **proyecto** (`.sqlite`) que se abre y se guarda desde
  la app.

## Requisitos

- Python 3.10+
- Windows (probado ahí)
- Chrome o Edge recomendados (permiten elegir dónde guardar el proyecto, incluso
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

1. En la barra de arriba, **Abrir proyecto** (sube tu `.sqlite`) o **Nuevo
   proyecto** (elige etapa, curso y materia y pulsa *Crear*).
2. Edita en las páginas de la barra lateral.
3. Pulsa **Guardar proyecto**: se guarda con un prefijo `AAAAMMDD_HHMM_` en el
   nombre. Dentro del archivo queda también la fecha y la hora del guardado.

Los códigos de la programación (criterios, contenidos, transversales,
descriptores) tienen que existir en el currículo de la materia. Antes de guardar
o generar el Word se revisa la coherencia; si algo no cuadra, puedes revisarlo a
mano o aplicar los arreglos automáticos.

## Funcionalidades

### Diseño de la programación

- **Situaciones de aprendizaje**: tabla SA / evaluación / descripción / horas,
  horas previstas vs. planificadas por trimestre y % de horas con gráfico de
  sectores (copiables a Word).
- **Sesiones por evaluación**: descarga el calendario escolar oficial de
  Castilla y León y cuenta, día a día, los días lectivos y las sesiones de cada
  evaluación. Las fechas, las sesiones por día y el festivo local se guardan en
  el proyecto. El resultado se puede volcar a las horas previstas.
- **Criterios de evaluación**: los de la materia; edición del peso P de cada
  criterio (%CE automático).
- **Indicadores de logro**: alta y baja por criterio, numeración automática, PIL%,
  descriptores operativos, contenidos y transversales marcados con ticks,
  instrumento, calificación, agente y SA en desplegables. Resumen por criterio copiable a Word.
- **Ajuste de pesos**: fijas el % objetivo de cada instrumento de evaluación y,
  con el reparto horario, se sugieren P y PIL (ajuste IPF). Tú decides si los cargas.
- **Distribución CE × SA**: matriz de pesos por criterio y situación,
  comparada con el reparto de horas.
- **Peso final por instrumento**: tabla y gráfico del peso acumulado de cada
  instrumento de evaluación.

### Contenidos

Contenidos de la materia (con su bloque) y transversales de la etapa, marcados
en verde si ya están asignados a algún indicador y en rojo si no.

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

Las competencias específicas salen del currículo. Los textos que no están en la
programación (redondeo, promoción, medidas…) se rellenan en la app y se guardan
en el proyecto.
Plantilla por defecto: `templates/informacion_familias_template.docx`; para
regenerarla, ejecuta `python -m tools.plantilla_familias`.

## Nota técnica

- `curriculo.db` se descarga de este repositorio (rama `master`) y se guarda en
  `%LOCALAPPDATA%\IES_Diseno\`. Sin conexión se usa la última copia descargada o,
  si no hay, la del propio repositorio.
- El proyecto es una base SQLite con solo lo del docente; la materia apunta al
  currículo por su identificador.
- Hasta octubre de 2026 la app trabajaba sobre un Excel de programación con
  Power Pivot. Ya no se usa.

Más detalle interno (modelo de datos, decisiones, trampas conocidas,
bitácora): ver [MEMORIA.md](MEMORIA.md).
