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
**programación de aula** sobre un **Excel de programación** que ya existe y que
tiene Power Pivot, tablas dinámicas, segmentaciones y formato condicional.

- La app **lee** el Excel, permite editar sus tablas con rejillas tipo hoja de
  cálculo, muestra cálculos/informes equivalentes a las hojas INFORMES/RESUMEN,
  y **devuelve el mismo Excel** modificado (sin romperlo) + un **Word** de la
  programación de aula generado con plantilla.
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
- Excel de ejemplo para probar: `ejemplos/20260925_1948_3ESO_DIVER_ACT.xlsx`
  (carpeta ignorada por git, igual que `salida/` y los `*.xlsx` de la raíz).

## 3. Estructura de archivos

| Archivo | Papel |
|---|---|
| `app.py` (~2500 líneas) | Toda la UI: CSS, barra lateral, barra global de carga/guardado, las 3 páginas y sus pestañas, diálogos. |
| `tools/situaciones_aprendizaje.py` | Leer/escribir `tablaSAprendizaje` + bloque G1:J4 (horas previstas) + L2:W2 (fechas de evaluación, horas por día, festivo local). Define `Situacion`, `TRIMESTRES`. |
| `tools/indicadores_logro.py` | Leer/escribir `TablaIndicadoresLogro`; leer criterios (`TablaCriteriosEvaluacion`), listas auxiliares y hoja `LOMLOE`; `recompute` (agrupa por CE, numera IL, PIL%); `save_criterios` (solo columna P); cálculos `matriz_sa_ce`, `peso_por_ie`, `resumen_por_ce`, `usados_en_il`. |
| `tools/programacion_aula_editor.py` | Leer/escribir `Tabla8` (datos generales), `Tabla9` (P_Aula_SA) y `TablaActividades`; `recompute_actividades`, `valores_actividades`. |
| `tools/consistencia.py` | `revisar()` coherencia entre tablas; autoarreglos (`add_il_para_ce`, `quitar_actividades_huerfanas`, `regenerar_p_aula_sa`). |
| `tools/programacion_aula.py` | Genera el `.docx` con **docxtpl** (`run_programacion_aula`). |
| `tools/ajuste_pesos.py` | IPF (Sinkhorn/RAS) para sugerir P y PIL a partir de % objetivo por instrumento + reparto horario. Réplica de la hoja `Ajuste_Pesos_IPF`. |
| `tools/sesiones_calendario.py` | Descarga/parsea el calendario escolar JCyL y cuenta días lectivos/sesiones por evaluación. |
| `tools/situaciones_informe.py` | Gráficos matplotlib (tartas, comparativa SA), tablas HTML «estilo Word», botones JS de copiar al portapapeles, CSS de AgGrid. |
| `tools/sellado.py` | Sello de fecha/hora como *defined name* oculto `IES_DISENO_ACTUALIZADO` en `xl/workbook.xml`. |
| `tools/info_familias.py` | Información a familias: leer/escribir la hoja propia `Info_Familias` (la **añade** al libro si falta), cálculos (`datos_familias`: criterios, competencias, contenidos, temporalización, instrumentos, una entrada por SA) y Word (`generar_docx`). |
| `tools/plantilla_familias.py` | Construye la plantilla Word por defecto de familias (`python -m tools.plantilla_familias`). |
| `templates/programacion_aula_template.docx` / `templates/informacion_familias_template.docx` | Plantillas Word por defecto (las únicas versionadas; el resto de `templates/` se ignora). |

## 4. El Excel de programación (modelo de datos)

Hojas: `Ajuste_Pesos_IPF`, `INFORMES`, `RESUMEN`, `SituacionesAprendizaje`,
`CriteriosEvaluación` (con tilde → se busca por prefijo `CriteriosEvaluaci`),
`IndicadoresLogro`, `Actividades`, `LOMLOE`, `TablasAuxiliares`,
`P_Aula_Datos_Generales`, `P_Aula_SA` y, si se usa la página de familias,
`Info_Familias` (creada por la app).

Tablas (ListObjects): `tablaSAprendizaje`, `TablaCriteriosEvaluacion`,
`TablaIndicadoresLogro`, `TablaActividades`, `Tabla8`, `Tabla9`, `CC`, `IE`, `AE`.

### Abreviaturas
- **SA** situación de aprendizaje (nº) · **EV** evaluación/trimestre (1-3) · **DSA** descripción/título · **HSA** horas.
- **CE** criterio de evaluación (p. ej. `4.2`) · **CED** su descripción · **P** peso del CE · **%CE** = P/ΣP.
- **IL** indicador de logro (`4.2.1`, automático y correlativo dentro del CE) · **PIL** peso · **PIL%** = PIL/ΣPIL del CE · **DIL** descripción · **DO** descriptores operativos.
- **CON** contenidos de la materia · **CT** contenidos transversales (códigos separados por comas, de la hoja `LOMLOE`).
- **IE** instrumento de evaluación · **CC** criterio de calificación · **AE** agente evaluador (listas en `TablasAuxiliares` B2:B11, F2:F5, D2:D4).
- **A** código de actividad (`<IL>.n`) · **DA** descripción · **PA** peso · **PA%** = PA/ΣPA del IL · **FACTOR** = PIL·PA%.

### Ubicaciones clave
- `SituacionesAprendizaje`: tabla `A1:D{n}`; resumen suelto `G1:J4` (H = horas previstas a mano, I = SUMIF, J = desviación); fila 2: `L2:Q2` fechas inicio/fin de cada evaluación (texto `DD/MM/AAAA`), `R2:V2` sesiones L-V, `W2` festivo local.
- `IndicadoresLogro`: cabecera en **fila 4**, datos desde la 5, columnas A..M. PIL% se escribe como **fórmula** estructurada.
- `Actividades`: A = IL, B..J = `VLOOKUP` sobre `TablaIndicadoresLogro`, K = A, L = DA, M = PA, N = PA% (fórmula), O = FACTOR (fórmula).
- `P_Aula_SA` (`Tabla9`) está **transpuesta**: col A = campo, cada columna = una SA. Se empareja con las SA **por título** (normalizado), no por número.
- `Info_Familias` (sin ListObject, la reescribe entera la app): `A:B` campo/valor (`CAMPOS` en `tools/info_familias.py`: redondeos, competencias clave, promoción/titulación, 4 medidas de atención), `D:E` nº de competencia específica / texto. Si falta, `save_info_familias` la da de alta tocando `workbook.xml`, `workbook.xml.rels`, `[Content_Types].xml` y `docProps/app.xml`. Solo se escribe si ya existía o hay algún texto (no se añaden hojas vacías). Verificado abriéndolo en Excel: Power Pivot y dinámicas intactos.
- Competencia específica de un CE = su primer número (`2.4` → 2); su peso = Σ %CE de sus criterios.

### Fórmulas de peso (réplicas de las dinámicas/DAX de INFORMES)
- Peso de un IL sobre la programación = `(PIL/ΣPIL del CE) · (P/ΣP)`.
- Valor de una actividad sobre la programación = `PA% · (PIL/ΣPIL del CE) · (P/ΣP)`; sobre la SA = ese valor / Σ de la SA.

## 5. Regla de oro: escritura quirúrgica del .xlsx

**Nunca guardar con openpyxl/pandas**: eliminan Power Pivot, dinámicas y
segmentaciones (el archivo pasa de ~690 KB a ~60 KB). openpyxl **solo para leer**
(`data_only=True`).

Para escribir: abrir el `.xlsx` como ZIP, reescribir con regex solo el XML de la
hoja afectada (+ definición de la tabla para ajustar `ref`/`autoFilter`) y
`xl/workbook.xml` (se fuerza `fullCalcOnLoad="1"` y se quitan valores en caché
de fórmulas para que Excel recalcule), y copiar **byte a byte** el resto.
Celdas de texto como `inlineStr`. Cada módulo repite sus helpers
(`_find_sheet_path`, `_find_table_path`, `_force_full_recalc`…): duplicación
conocida, no unificada.

Orden de escritura en `_guardar_todo()` (`app.py`): situaciones → indicadores →
criterios (P) → datos generales → P_Aula_SA (siempre regenerada desde la lista de
SA) → actividades → sello.

## 6. Arquitectura de la UI (`app.py`)

- **Barra lateral** (`st.radio` key `active_page`): 3 páginas
  - **Diseño de la programación** — pestañas: Situaciones de aprendizaje · Sesiones por evaluación · Criterios de evaluación · Indicadores de logro · Ajuste de pesos · Distribución CE × SA · Peso final por instrumento.
  - **Contenidos** — Contenidos de la materia · Contenidos transversales (🟢 asignado a algún IL / 🔴 no).
  - **Programación de aula** — botón Generar Word (+ plantilla opcional) · pestañas Datos generales · Actividades por SA (incluye campos de P_Aula_SA y resumen de actividades).
  - **Información a familias** — botón Generar/Descargar Word (+ plantilla opcional) · aviso de campos vacíos · pestañas Competencias específicas · Calificación y promoción · Atención individualizada · Vista previa por SA. Los widgets (`fam_w_*`) usan `on_change=_fam_sync`, que copia a `fam_campos`/`fam_comp` e invalida `prog_out` **antes** del rerun (así la barra de arriba guarda el texto nuevo).
- **Barra global** arriba: `file_uploader` del Excel + botón **«Guardar Excel»** (HTML/JS propio, `_guardar_excel_html`): usa `showSaveFilePicker` (Chrome/Edge, permite sobrescribir el original) o descarga normal (Firefox/Safari). El nombre lleva prefijo `AAAAMMDD_HHMM_` calculado **en JS al hacer clic**; `_nombre_sin_sello` evita acumular prefijos.
- El Excel de salida (`prog_out`) se **recalcula solo** cuando falta; **cualquier edición hace `pop("prog_out")`** para invalidarlo. Si hay incoherencias, se muestra `_dlg_coherencia` una vez por Excel cargado (`consist_seen`).

### Patrones de estado (session_state)
- Carga del Excel: al cambiar `prog_loaded_id` (nombre + md5 del contenido, `_huella_excel`; antes solo el nombre y no se recargaba un Excel retocado en Excel y resubido con el mismo nombre) se rellenan `sa_df`, `sa_previstas`, `sa_fechas_trimestre`, `sa_horas_dia`, `sa_festivo_local`, `il_rows`, `il_ce_list`, `il_ce_ced`, `il_ce_p`, `il_aux`, `elementos`, `pa_*`, y se borran derivados (`prog_out`, `prog_base`, `sa_grid_rows`, `ce_rows`, `il_pending`, `pa_docx`, `consist_seen`, `ses_*`).
- **Canónico vs. pendiente**: `sa_grid_rows`/`ce_rows`/`il_rows`/`pa_acts` son lo canónico; lo que hay en la rejilla AgGrid se lee cada rerun (`il_pending`, `ce_pending`…). El botón **Actualizar** consolida (reagrupa, renumera, recalcula %) y remonta la rejilla subiendo un **nonce** en la `key` (`sa_nonce`, `ce_nonce`, `il_nonce`, `pa_nonce`).
- `prog_base`: Excel base ya regenerado (tras autoarreglos) sobre el que se aplican los cambios.
- Pestañas persistentes con `_pestanas(key, títulos)` (`st.tabs(..., key, default, on_change)` + copia en `_last_<key>`).
- En **Diseño** el cuerpo de **todas** las pestañas se ejecuta siempre (unas usan variables de otras: `sits`, `ce_p`, `pending`). En las otras páginas sí se mira `.open`.
- La tabla de **situaciones de aprendizaje manda**: P_Aula_SA, títulos y trimestres derivan de ella.

### Trucos/trampas conocidas
- **AgGrid en iframe** dentro de pestaña oculta/expander se monta con ancho 0 → parche JS al principio de `app.py` que fuerza `width:100%` y lanza `resize`.
- **Clic en celda → diálogo**: `onCellClicked` escribe en una columna oculta `_pick` (`campo|fila|timestamp`); Python detecta el cambio comparando con `il_pick_seen` / `pa_pick_seen`. En Actividades, un temporizador de 280 ms distingue clic (resumen) de doble clic (editar IL).
- **`st.dialog`**: un `on_click` dentro del diálogo solo relanza el diálogo (es un fragment) → usar botón imperativo + `st.rerun(scope="app")` para cerrarlo.
- EV en la rejilla de SA va como **texto** (con desplegable numérico daba «invalid number» y bloqueaba editar DSA).
- Selectores con valores fuera de lista: `_with_existing()` añade los valores presentes para que no reviente.
- Campos de la calculadora de sesiones llevan `on_change=_invalidar_prog_out` (no tienen botón Actualizar propio).
- **Maquetación del Word de familias** (`_fila` en `tools/info_familias.py`): filas que no se parten (`cantSplit`), cabecera repetida (`tblHeader`) y «conservar con el siguiente» para atar filas: tablas cortas enteras (`max_juntas`), las largas sin filas sueltas al principio/final; en cada SA, criterio + sus IL juntos y el último criterio va con la línea de agentes y la tarta. **Ojo:** `cell.text = …` borra el formato del párrafo → aplicar `_fila` después de escribir. En la plantilla, los títulos y las introducciones van pegados a su tabla, y cada SA empieza en página nueva con `page_break_before` en su título (sin párrafo vacío). Para revisar páginas: Word por COM → PDF (`SaveAs` formato 17) y renderizar con PyMuPDF.
- docxtpl usa `jinja2.ChainableUndefined` porque un TOC cacheado en la plantilla puede dejar `{{ situacion.titulo }}` fuera del bucle.
- `programacion_aula.py` recibe `resumen_por_sa` ya calculado por la app (las fórmulas del Excel recién guardado no tienen caché); si no, replica las medidas DAX desde el Excel.

## 7. Plantilla Word

Variables: datos generales (`curso`, `grupo`, `materia`, `docente`, `numero_alumnos`, `años`, `alumnos_atencion_individualizada`, `caracteristicas_fisicas_cognitivas_afectivas`, `nivel_competencia_curricular`, `otras_caracteristicas_grupo`, `resultados_evaluacion_inicial`, `conclusiones_evaluacion_inicial`, `resultados_evaluacion_aprendizajes`, `revision_programacion`) y un bucle `{% for situacion in situaciones %}` con `situacion.numero/titulo/trimestre/contextualizacion/…` y las subtablas `{{p situacion.tabla_indicadores}}` (CE, IL, CT, IE, CC, AE) y `{{p situacion.tabla_actividades}}`.

## 8. Decisiones tomadas (y por qué)

- Escritura quirúrgica del ZIP en vez de openpyxl → preservar Power Pivot (ver §5).
- Un único botón «Guardar Excel», sin paso previo de «generar» → menos fricción; no recuerda el archivo entre guardados (un intento anterior se quedaba colgado).
- Sello dentro del Excel sin número de versión, solo fecha-hora (commit 55501c1).
- Fechas/horas por día/festivo local se guardan en el propio Excel (L2:W2) → no repensarlas cada curso.
- Sin logotipos institucionales (b64569e).
- Contenidos (CON/CT) se marcan con ticks en un diálogo, no a mano.
- Se eliminó la pestaña «Actividades» suelta: todo va dentro de Programación de aula por SA.
- **Información a familias** (2026-10-15), a partir del PowerPoint de inspección «ACTUACIÓN Evaluación_POWER P_CH (2).ppt» (supervisión de la información al alumnado y las familias; ESO/Bach: Orden EDU/424/2024 art. 12 y 425/2024 art. 10; la parte de FP no aplica a este Excel). Decisiones del usuario: Word con plantilla; datos nuevos guardados **en el Excel**; contenido = resumen por criterio de la programación + **una página por SA** con CE → sus IL (**sin el texto del IL**) y todos los valores + **tarta de instrumentos parcial de cada SA**; **no** calcular el peso de las competencias clave a partir de DO (por ahora).
- Las medidas de atención para familias son texto **general**: nunca se usa `alumnos_atencion_individualizada` (datos de alumnos concretos) porque el documento va a todas las familias.

## 9. Observaciones / posibles problemas detectados (sin verificar)

- `save_criterios` sustituye `<c r="C{fila}" …>…</c>` con regex que **no casa con celdas autocerradas** (`<c r="C5" s="3"/>`): si un P estaba vacío en el Excel original, el nuevo valor podría no escribirse.
- `regenerar_p_aula_sa` no añade `fullCalcOnLoad` si el workbook no tiene `<calcPr` (los otros módulos sí lo añaden).
- `DEFAULT_CALENDAR_URL` apunta al curso **2026-2027**: actualizar cada curso.
- No hay tests automatizados. Para probar la UI sin navegador sirve `streamlit.testing.v1.AppTest` sustituyendo `st.file_uploader` por uno falso que devuelva el Excel de ejemplo (así se probó la página de familias).
- **Probable fallo (sin confirmar):** en Programación de aula, los campos de «Datos generales» y de P_Aula_SA no llevan `on_change` que invalide `prog_out`; como la barra de arriba calcula el Excel antes de que la página actualice `pa_datos`, un texto tecleado ahí podría no llegar al Excel guardado hasta la siguiente edición en otro sitio. Solución: el mismo patrón que `_fam_sync`.
- Streamlit avisa de que `use_container_width` y `st.components.v1.html` están obsoletos (fechas de retirada ya pasadas): habrá que migrar a `width=` y `st.iframe`.

## 10. Pendientes / ideas

- Familias: peso de las competencias clave a partir de los descriptores operativos (DO) — aplazado por decisión del usuario.
- Familias: quizá textos por defecto del centro para redondeo/promoción (ahora se teclean por Excel).

---

## Bitácora

Formato: `AAAA-MM-DD — qué se hizo (commit si aplica)`.

- 2026-09-05 — Esqueleto «IES Manager»; editor de Situaciones con escritura quirúrgica; % de horas y tarta copiable a Word.
- 2026-09-06 — Día grande (33 commits): Indicadores de logro, Criterios, matriz CE×SA, resumen por CE para Word, pestaña Elementos curriculares/Contenidos, programación de aula completa, coherencia al guardar/generar, renombrado a «IES Diseño», sello de fecha/hora.
- 2026-09-07 — Peso por instrumento de evaluación; sello sin versión; limpieza de plantillas.
- 2026-09-16 — Secciones colapsables, calculadora de sesiones, ajuste de pesos IPF (9156056); README breve.
- 2026-09-25 — Quitar logotipos institucionales (b64569e); contenidos en campo aparte; desplegables CON/CT en todas las programaciones.
- 2026-09-26 — Guardado corregido y persistencia de horas/fechas (b44b368); nuevo diseño con barra lateral (948cae8).
- 2026-10-15 — Estudio completo del código y creación de este `MEMORIA.md` (+ `CLAUDE.md` que lo importa). README reescrito con las 3 páginas y todas las pestañas actuales.
- 2026-10-15 — Nueva página **Información a familias** (`tools/info_familias.py`, `tools/plantilla_familias.py`, plantilla Word nueva, hoja `Info_Familias`). Probado con AppTest (4 páginas sin errores, guardado y Word) y abriendo el Excel resultante en Excel.
- 2026-10-20 — Word de familias: maquetación sin cortes bruscos (cabeceras repetidas, filas enteras, criterios con sus IL, tarta junto a su tabla, SA en página nueva sin párrafo vacío). Plantilla regenerada. Comprobado en Word con el Excel de ejemplo y con una SA artificialmente larga.
- 2026-10-20 — Recarga del Excel por contenido (nombre + hash), no solo por nombre: un Excel retocado fuera de la app con el mismo nombre no rellenaba los campos de familias.
