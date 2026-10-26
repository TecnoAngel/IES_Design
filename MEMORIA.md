# Memoria del proyecto — IES Diseño

Documento vivo para no depender del historial de chats. Recoge **qué es** la app,
**cómo está montada**, las **decisiones** tomadas y sus porqués, las **trampas**
conocidas y una **bitácora** de cambios. Actualizar al final de cada sesión de
trabajo relevante (sección «Bitácora» y, si cambia algo estructural, la sección
correspondiente).

---

## 1. Qué es

Aplicación **Streamlit** (Python, Windows) para que el profesorado de un IES de
Castilla y León diseñe y revise su **programación didáctica (LOMLOE)** y su
**programación de aula**.

- **Currículo común** (`curriculo.db`, SQLite, en el repo de GitHub): materias de
  ESO, Diversificación y Bachillerato con criterios de evaluación, competencias
  específicas, contenidos, transversales, descriptores operativos y catálogos
  IE/CC/AE. La app lo **descarga sola** en cada sesión.
- **Proyecto del docente** (`.sqlite`): lo que es suyo (SA, pesos, indicadores,
  actividades, datos de aula, textos de familias). Se **sube** al empezar (o se
  crea eligiendo **etapa → curso → materia**) y se **descarga** con «Guardar
  proyecto».
- Genera dos **Word** con plantilla: programación de aula e información a familias.
- Hasta octubre de 2026 la app trabajaba sobre un **Excel de programación** con
  Power Pivot (escritura quirúrgica del ZIP). Se abandonó (ver §8); las ~6
  programaciones antiguas se migran fuera de la app, con Claude.ai.
- Nombre anterior: «IES Manager». Proyecto hermano/origen: **IES_Creator**
  (de ahí viene el parser del calendario JCyL).
- Idioma de código, UI, comentarios y commits: **español**.

## 2. Arranque

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
run_app.bat            # = .venv\Scripts\python.exe -m streamlit run app.py --server.port 8502
```

- `app.py` detecta si faltan dependencias (venv equivocado) y muestra cómo lanzarlo.
- Tema fijo claro rojo carmín `#A6182E` + oro `#E0A21C` (`.streamlit/config.toml`
  y CSS en `app.py`). Sin escudos ni logos institucionales (se quitaron a propósito).
- `curriculo.db` se descarga de
  `https://raw.githubusercontent.com/TecnoAngel/IES_Design/master/curriculo.db`
  (repo **público**) a `%LOCALAPPDATA%\IES_Diseno\`. Sin red usa la copia en caché
  y, si no hay, la del propio repo. La barra lateral dice de dónde salió.
  **Hay que hacer push de `curriculo.db`** para que la descarga funcione.
- `ejemplos/` (Excel antiguo de prueba), `salida/`, `*.xlsx` y `*.sqlite` de la
  raíz están ignorados por git (datos reales).

## 3. Estructura de archivos

| Archivo | Papel |
|---|---|
| `app.py` (~2700 líneas) | Toda la UI: CSS, barra lateral, barra global abrir/crear/guardar, las 4 páginas y sus pestañas, diálogos. |
| `curriculo.db` | Currículo común (ver §4). Versionado en git; se actualiza fuera de la app. |
| `tools/curriculo.py` | Solo lectura de `curriculo.db`: `obtener_curriculo` (descarga + caché), `cursos`, `materias`, `materia`, `cargar_materia`. Etapas `ESO`/`DIVER`/`BACH`. |
| `tools/proyecto.py` | Proyecto `.sqlite`: esquema, `estado_vacio`, `leer_proyecto`, `leer_meta`, `guardar_proyecto`. Listas fijas `DATOS_CAMPOS`, `SA_CAMPOS`. |
| `tools/consistencia.py` | `revisar()` coherencia (currículo + SA) y autoarreglos (`add_il_para_ce`, `quitar_il_de_ce`, `limpiar_codigos`, `quitar_actividades_huerfanas`). |
| `tools/indicadores_logro.py` | Cálculos de IL: `recompute` (agrupa por CE, numera IL, PIL%), `matriz_sa_ce`, `peso_por_ie`, `resumen_por_ce`, `usados_en_il`. |
| `tools/programacion_aula_editor.py` | `recompute_actividades`, `valores_actividades`. |
| `tools/situaciones_aprendizaje.py` | `Situacion`, `TRIMESTRES`, `acumulado_por_trimestre`. |
| `tools/programacion_aula.py` | Word de programación de aula con **docxtpl** (`run_programacion_aula(datos_generales, situaciones, plantilla, resumen_por_sa=…)`). |
| `tools/info_familias.py` | Información a familias: `CAMPOS`, cálculos (`datos_familias`) y Word (`generar_docx`). |
| `tools/plantilla_familias.py` | Construye la plantilla Word por defecto de familias (`python -m tools.plantilla_familias`). |
| `tools/ajuste_pesos.py` | IPF (Sinkhorn/RAS) para sugerir P y PIL a partir de % objetivo por instrumento + reparto horario. |
| `tools/sesiones_calendario.py` | Descarga/parsea el calendario escolar JCyL y cuenta días lectivos/sesiones por evaluación. |
| `tools/situaciones_informe.py` | Gráficos matplotlib, tablas HTML «estilo Word», botones JS de copiar, CSS de AgGrid. |
| `templates/programacion_aula_template.docx` / `templates/informacion_familias_template.docx` | Plantillas Word por defecto (las únicas versionadas). |

## 4. Modelo de datos

### `curriculo.db` (común, solo lectura en la app)
`materias(id, nombre, etapa ESO|BACH, curso, comunidad, normativa)`,
`criterios(materia_id, codigo '1.1', ce_numero, descripcion, orden)`,
`competencias_especificas(materia_id, numero, descripcion, descriptores)`,
`criterio_descriptores(materia_id, criterio, descriptor, orden)`,
`contenidos(materia_id, codigo 'A.3.1', bloque, descripcion, orden)`,
`transversales(etapa, comunidad, numero, descripcion)`,
`descriptores(codigo, etapa, competencia, descripcion)`,
`catalogos(tipo IE|CC|AE, valor, orden)`.

- **DIVER** = materias con `normativa = 'Orden EDU/1332/2023'` (ámbitos de 3º y
  4º). En la base figuran como `etapa='ESO'`: usan transversales y descriptores
  de ESO. **ESO** en la app = ESO sin esas materias.
- `cargar_materia` devuelve lo que la sesión usaba antes del Excel (`ce_list`,
  `ce_ced`, `elementos{contenidos, transversales, descriptores}`, `aux{IE,CC,AE}`)
  más `ce_do` (descriptores de cada CE), `competencias` y `comp_descriptores`.

### Proyecto `.sqlite` (del docente)
`meta(clave, valor)` (schema_version, materia_id, materia_nombre, etapa, curso,
normativa, actualizado = sello), `config(clave, valor)` (horas previstas,
fechas de cada evaluación en ISO, horas por día, festivo local),
`situaciones(numero, ev, titulo, horas, orden)`,
`situacion_campos(numero, campo, valor)` (campos de aula de cada SA, antes la
hoja transpuesta P_Aula_SA), `criterios_peso(ce, peso)`,
`indicadores(orden, ce, pil, descripcion, descriptores, contenidos,
transversales, ie, cc, ae, sa)` (CON/CT/DO como texto `"A.1.1, A.1.2"`; el IL se
recalcula con `recompute`), `actividades(orden, il, descripcion, peso)`,
`datos_generales(campo, valor)`, `familias(campo, valor)`.

- Se escribe entero cada vez (`guardar_proyecto`: base nueva en memoria +
  `serialize()`), no se actualiza en sitio.
- **Todos los códigos deben existir en el currículo de la materia** (CE,
  CON, CT, DO). Lo comprueba `consistencia.revisar`; los pesos de CE que ya no
  existen se descartan al cargar y un CE nuevo empieza con P = 0.

### Abreviaturas
- **SA** situación de aprendizaje (nº) · **EV** evaluación/trimestre (1-3) · **DSA** descripción/título · **HSA** horas.
- **CE** criterio de evaluación (p. ej. `4.2`) · **CED** su descripción · **P** peso del CE · **%CE** = P/ΣP.
- **IL** indicador de logro (`4.2.1`, automático y correlativo dentro del CE) · **PIL** peso · **PIL%** = PIL/ΣPIL del CE · **DIL** descripción · **DO** descriptores operativos.
- **CON** contenidos de la materia · **CT** contenidos transversales.
- **IE** instrumento de evaluación · **CC** criterio de calificación · **AE** agente evaluador.
- **A** código de actividad (`<IL>.n`) · **DA** descripción · **PA** peso · **PA%** = PA/ΣPA del IL · **FACTOR** = PIL·PA%.
- Competencia específica de un CE = su primer número (`2.4` → 2); su peso = Σ %CE de sus criterios.

### Fórmulas de peso (réplicas de las dinámicas/DAX del antiguo Excel)
- Peso de un IL sobre la programación = `(PIL/ΣPIL del CE) · (P/ΣP)`.
- Valor de una actividad sobre la programación = `PA% · (PIL/ΣPIL del CE) · (P/ΣP)`; sobre la SA = ese valor / Σ de la SA.

## 5. Guardado

- `_guardar_todo()` (`app.py`) = `_estado_actual()` (todo lo que hay en sesión) →
  `proyecto.guardar_proyecto(...)`. Devuelve los bytes del `.sqlite` y el sello.
- Los campos de aula de cada SA se emparejan **por título** (`pa_sa_edits` en
  sesión o `pa_sa_cols` cargados); título y trimestre salen siempre de la tabla
  de SA.

## 6. Arquitectura de la UI (`app.py`)

- **Barra lateral** (`st.radio` key `active_page`): 4 páginas, más el origen del currículo.
  - **Diseño de la programación** — pestañas: Situaciones de aprendizaje · Sesiones por evaluación · Criterios de evaluación · Indicadores de logro · Ajuste de pesos · Distribución CE × SA · Peso final por instrumento.
  - **Contenidos** — Contenidos de la materia (con su bloque) · Contenidos transversales (🟢 asignado a algún IL / 🔴 no).
  - **Programación de aula** — botón Generar Word (+ plantilla opcional) · pestañas Datos generales · Actividades por SA (incluye campos de aula de la SA y resumen de actividades).
  - **Información a familias** — botón Generar/Descargar Word (+ plantilla opcional) · aviso de campos vacíos · pestañas Competencias específicas (solo lectura, del currículo) · Calificación y promoción · Atención individualizada · Vista previa por SA.
- **Barra global** arriba: `segmented_control` (`proy_modo`) **Abrir proyecto** (uploader `.sqlite`) / **Nuevo proyecto** (Etapa → Curso → Materia + Crear), y el botón **«Guardar proyecto»** (HTML/JS propio, `_guardar_archivo_html`): `showSaveFilePicker` en Chrome/Edge, descarga normal en Firefox/Safari. Prefijo `AAAAMMDD_HHMM_` calculado **en JS al hacer clic**; `_nombre_sin_sello` evita acumular prefijos. Nombre base: el del archivo abierto o el id de la materia.
- El proyecto de salida (`prog_out`) se **recalcula solo** cuando falta; **cualquier edición hace `pop("prog_out")`**. Si hay incoherencias, se muestra `_dlg_coherencia` una vez por proyecto cargado (`consist_seen`, se marca al abrir el diálogo).

### Patrones de estado (session_state)
- `_cargar_estado(estado, nombre)` rellena la sesión desde un proyecto (o uno nuevo, `estado_vacio`) + el currículo de su materia: `cur` (lo de `cargar_materia`), `proy_materia`, `proy_nombre`, `sa_df`, `sa_previstas`, `sa_fechas_trimestre`, `sa_horas_dia`, `sa_festivo_local`, `il_rows`, `il_ce_list`, `il_ce_ced`, `il_ce_p`, `il_aux`, `elementos`, `pa_*`, `fam_campos`; y borra derivados y widgets (`prog_out`, `sa_grid_rows`, `ce_rows`, `il_pending`, `consist_seen`, `fam_w_*`, `pad_*`, `pasa_*`, `ses_*`…).
- Un archivo subido solo se carga si es **nuevo** (`proy_file_seen` = nombre + md5): así «Crear» no queda pisado por el archivo que siga en el uploader.
- **Canónico vs. pendiente**: `sa_grid_rows`/`ce_rows`/`il_rows`/`pa_acts` son lo canónico; lo que hay en la rejilla AgGrid se lee cada rerun (`il_pending`, `ce_pending`…). El botón **Actualizar** consolida y remonta la rejilla subiendo un **nonce** en la `key` (`sa_nonce`, `ce_nonce`, `il_nonce`, `pa_nonce`).
- Pestañas persistentes con `_pestanas(key, títulos)`.
- En **Diseño** el cuerpo de **todas** las pestañas se ejecuta siempre (unas usan variables de otras: `sits`, `ce_p`, `pending`). En las otras páginas sí se mira `.open`.
- La tabla de **situaciones de aprendizaje manda** dentro del proyecto; el **currículo manda** sobre los códigos.

### Trucos/trampas conocidas
- **AgGrid en iframe** dentro de pestaña oculta/expander se monta con ancho 0 → parche JS al principio de `app.py`.
- **Clic en celda → diálogo**: `onCellClicked` escribe en una columna oculta `_pick` (`campo|fila|timestamp`); Python lo detecta comparando con `il_pick_seen` / `pa_pick_seen`. En Indicadores sirve para **DO, CON y CT** (ticks); en DO solo se ofrecen los descriptores que el currículo vincula a ese CE (+ los ya marcados). Al añadir un IL, DO trae los descriptores del CE.
- **`st.dialog`**: un `on_click` dentro del diálogo solo relanza el diálogo (es un fragment) → botón imperativo + `st.rerun(scope="app")`. **Dos `st.dialog` en la misma ejecución revientan** (`StreamlitDuplicateElementId`): `_dlg_coherencia` es un envoltorio que lo abre como mucho una vez por ejecución.
- **Campos de texto sin botón Actualizar** (calculadora de sesiones, Datos generales, campos de aula de la SA, familias) llevan `on_change` que copia el valor al estado e invalida `prog_out` **antes** del rerun (`_invalidar_prog_out`, `_pad_sync`, `_pasa_sync`, `_fam_sync`): la barra de arriba calcula el proyecto antes de que la página vuelva a pintar los campos.
- EV en la rejilla de SA va como **texto** (con desplegable numérico daba «invalid number»).
- Selectores con valores fuera de lista: `_with_existing()` añade los valores presentes.
- **Maquetación del Word de familias** (`_fila` en `tools/info_familias.py`): filas que no se parten, cabecera repetida y «conservar con el siguiente». **Ojo:** `cell.text = …` borra el formato del párrafo → aplicar `_fila` después. Para revisar páginas: Word por COM → PDF y PyMuPDF.
- docxtpl usa `jinja2.ChainableUndefined` (un TOC cacheado en la plantilla puede dejar `{{ situacion.titulo }}` fuera del bucle).
- **AppTest** no simula bien los botones dentro de un `st.dialog` (relanza la app entera, no el fragment): los autoarreglos se prueban llamando a `tools.consistencia` directamente.

## 7. Plantilla Word

Variables: datos generales (`materia`, `curso`, `grupo`, `docente`, `numero_alumnos`, `alumnos_atencion_individualizada`, `caracteristicas_fisicas_cognitivas_afectivas`, `nivel_competencia_curricular`, `otras_caracteristicas_grupo`, `resultados_evaluacion_inicial`, `conclusiones_evaluacion_inicial`, `resultados_evaluacion_aprendizajes`, `revision_programacion`) y un bucle `{% for situacion in situaciones %}` con `situacion.numero/titulo/trimestre/contextualizacion/…` (`SA_CAMPOS`) y las subtablas `{{p situacion.tabla_indicadores}}` (CE, IL, CT, IE, CC, AE) y `{{p situacion.tabla_actividades}}`.

## 8. Decisiones tomadas (y por qué)

- **2026-10-26: del Excel a currículo + proyecto SQLite.** El Excel obligaba a escritura quirúrgica del ZIP con regex (~1000 líneas frágiles, para no romper Power Pivot) y cada Excel llevaba su copia del currículo. Ahora: currículo único en `curriculo.db` (GitHub, descarga automática), proyecto propio `.sqlite` que se sube/descarga, selección etapa → curso → materia. Decisiones del usuario: ante códigos que no casan, **avisar y ofrecer arreglo** (no bloquear ni limpiar solo); **catálogos IE/CC/AE comunes** en `curriculo.db`; flujo **subir/descargar**; **sin importador** de Excel en la app (son unas 6 programaciones: se convierten con Claude.ai).
- Coste asumido: el proyecto ya no se abre en Excel (sin dinámicas ni segmentaciones; la app replica los cálculos).
- Un único botón «Guardar proyecto», sin paso previo; no recuerda el archivo entre guardados (un intento anterior se quedaba colgado).
- Fechas/horas por día/festivo local se guardan en el proyecto → no repensarlas cada curso.
- Sin logotipos institucionales (b64569e).
- Contenidos, transversales y DO se marcan con ticks en un diálogo, no a mano.
- **Información a familias** (2026-10-15), a partir del PowerPoint de inspección (Orden EDU/424/2024 art. 12 y 425/2024 art. 10): Word con plantilla; contenido = resumen por criterio + **una página por SA** con CE → sus IL (**sin el texto del IL**) + **tarta de instrumentos de cada SA**; **no** calcular el peso de las competencias clave a partir de DO (por ahora). Desde 2026-10-26 el texto de las competencias específicas sale del currículo.
- Las medidas de atención para familias son texto **general**: nunca se usa `alumnos_atencion_individualizada` (datos de alumnos concretos).

## 9. Observaciones / posibles problemas detectados (sin verificar)

- `DEFAULT_CALENDAR_URL` apunta al curso **2026-2027**: actualizar cada curso.
- No hay tests automatizados. Para probar la UI sin navegador sirve `streamlit.testing.v1.AppTest` sustituyendo `st.file_uploader` por uno falso que devuelva un `.sqlite` de prueba.
- Si se cambian códigos en `curriculo.db`, los proyectos antiguos darán avisos de coherencia (es lo esperado).
- En el Excel de ejemplo, algunos IL tenían **frases en la columna DO** en vez de códigos: al migrar, la coherencia lo marca y el arreglo las quita.
- Streamlit avisa de que `use_container_width` y `st.components.v1.html` están obsoletos (fechas de retirada ya pasadas): habrá que migrar a `width=` y `st.iframe`.

## 10. Pendientes / ideas

- Hacer push de `curriculo.db` a GitHub (si no, la app usa la copia local).
- Migrar las programaciones Excel antiguas con Claude.ai (prompt preparado en la sesión del 2026-10-26).
- Familias: peso de las competencias clave a partir de los DO — aplazado por decisión del usuario (ahora es viable con `criterio_descriptores`).
- Familias: quizá textos por defecto del centro para redondeo/promoción.

---

## Bitácora

Formato: `AAAA-MM-DD — qué se hizo (commit si aplica)`.

- 2026-09-05 — Esqueleto «IES Manager»; editor de Situaciones con escritura quirúrgica; % de horas y tarta copiable a Word.
- 2026-09-06 — Día grande (33 commits): Indicadores de logro, Criterios, matriz CE×SA, resumen por CE para Word, pestaña Elementos curriculares/Contenidos, programación de aula completa, coherencia al guardar/generar, renombrado a «IES Diseño», sello de fecha/hora.
- 2026-09-07 — Peso por instrumento de evaluación; sello sin versión; limpieza de plantillas.
- 2026-09-16 — Secciones colapsables, calculadora de sesiones, ajuste de pesos IPF (9156056); README breve.
- 2026-09-25 — Quitar logotipos institucionales (b64569e); contenidos en campo aparte; desplegables CON/CT en todas las programaciones.
- 2026-09-26 — Guardado corregido y persistencia de horas/fechas (b44b368); nuevo diseño con barra lateral (948cae8).
- 2026-10-15 — Estudio completo del código y creación de este `MEMORIA.md` (+ `CLAUDE.md` que lo importa). README reescrito.
- 2026-10-15 — Nueva página **Información a familias**. Probado con AppTest y abriendo el Excel resultante en Excel.
- 2026-10-20 — Word de familias: maquetación sin cortes bruscos. Plantilla regenerada.
- 2026-10-20 — Recarga del Excel por contenido (nombre + hash), no solo por nombre.
- 2026-10-26 — **Cambio de modelo: fuera el Excel.** `curriculo.db` (catálogos IE/CC/AE rellenados) + `tools/curriculo.py` (descarga de GitHub con caché) + proyecto `.sqlite` (`tools/proyecto.py`). Barra Abrir/Nuevo proyecto (etapa → curso → materia), «Guardar proyecto». Coherencia contra el currículo (CE, CON, CT, DO) con arreglos. DO con ticks. Competencias específicas del currículo en familias. Word de aula generado desde la sesión. Borradas todas las escrituras del ZIP del xlsx, `tools/sellado.py` y `openpyxl`. Arreglados: doble `st.dialog` al cerrar el aviso con la X, y Datos generales / campos de aula que podían no llegar al archivo guardado. Probado con AppTest: proyecto nuevo (Biología 1º ESO) y el Excel de ejemplo convertido (Ámbito Científico-Tecnológico 4º, 100 % de coincidencia de códigos): 4 páginas sin errores, los dos Word, ida y vuelta idéntica.
