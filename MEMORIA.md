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
- Tema fijo claro **azul `#0F5CA8` + plata `#F3F6FA` / `#D6DEE8` + blanco**, al estilo de la web de
  educacyl (`.streamlit/config.toml` y variables `--c-azul`, `--c-azul-2`, `--c-acento`, `--c-tinta`,
  `--c-plata`, `--c-linea` del CSS de `app.py`; hasta 2026-11-14 era rojo carmín + oro). Sin escudos ni logos institucionales (se quitaron a propósito).
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
| `app.py` (~2500 líneas) | La UI: CSS, barra lateral, barra global abrir/crear/guardar, el menú (`NAV`), las páginas y sus pestañas, diálogos. |
| `ui/actividades.py` | Pestaña «Actividades por situación de aprendizaje» entera (los tres cuadros), solo con widgets de Streamlit. `app.py` pone el selector de SA y llama a `pintar(sa, il_rows, ce_p)`. |
| `ui/redaccion.py` | Página «Redacción» entera (una pestaña por capítulo), solo con widgets de Streamlit. Pinta lo que define `tools/redaccion.py`; `app.py` crea las pestañas y llama a `pintar(pestañas, _datos_redaccion)`. |
| `ui/ajuste_categoria.py` | Modo «Ajustar por categoría» de Ajuste de pesos (objetivo % por opción, sugerencia de P/PIL, «Cargar»). Lógica: `ajuste_pesos.sugerir_por_categoria`. |
| `ui/categorias.py` | Desplegable «Categorías de los indicadores (opcional)» de la pestaña Indicadores de logro (define categorías y sus opciones). `app.py` lo llama con `pintar(recalcular)`. |
| `tools/categorias.py` | Lógica de las categorías de IL (sin pantalla): `normalizar`, `añadir_categoria`, `añadir_opcion`, `quitar_categoria`, `quitar_opcion`, `limpiar_filas`, `columna`, `id_de_opcion`, `nombre_de_opcion`. |
| `ui/` | Carpeta de las pantallas sacadas de `app.py` (usan Streamlit; la lógica sin pantalla va en `tools/`). Se importan como `from ui import actividades as ui_actividades`. |
| `curriculo.db` | Currículo común (ver §4). Versionado en git; se actualiza fuera de la app. |
| `tools/curriculo.py` | Solo lectura de `curriculo.db`: `obtener_curriculo` (descarga + caché), `cursos`, `materias`, `materia`, `cargar_materia`. Etapas `ESO`/`DIVER`/`BACH`. |
| `tools/proyecto.py` | Proyecto `.sqlite`: esquema, `estado_vacio`, `leer_proyecto`, `leer_meta`, `guardar_proyecto`. Listas fijas `DATOS_CAMPOS`, `SA_CAMPOS`. |
| `tools/consistencia.py` | `revisar()` coherencia (currículo + SA + actividades) y autoarreglos (`add_il_para_ce`, `quitar_il_de_ce`, `limpiar_codigos`, `quitar_actividades_huerfanas`, `repartir_pendientes`). |
| `tools/indicadores_logro.py` | Cálculos de IL: `recompute` (agrupa por CE, numera IL, PIL%), `matriz_sa_ce`, `peso_por_ie`, `resumen_por_ce`, `usados_en_il`. |
| `tools/programacion_aula_editor.py` | Actividades (SA + IE + título + varios IL): `fraccion_por_enlace`, `valores_enlaces`, `reparto_pendiente`, `repartir_iguales`, `enlaces_invalidos`, `codigos` (A1, A2… por SA), `valores_actividades`, `desde_formato_antiguo`. |
| `tools/situaciones_aprendizaje.py` | `Situacion`, `TRIMESTRES`, `acumulado_por_trimestre`. |
| `tools/programacion_aula.py` | Word de programación de aula con **docxtpl** (`run_programacion_aula(datos_generales, situaciones, plantilla, resumen_por_sa=…)`). |
| `tools/info_familias.py` | Información a familias: `CAMPOS`, cálculos (`datos_familias`) y Word (`generar_docx`). |
| `tools/plantilla_familias.py` | Construye la plantilla Word por defecto de familias (`python -m tools.plantilla_familias`). |
| `tools/redaccion.py` | **Definición** de la programación didáctica: `CAPITULOS` (portada, a–ñ y anexos) con sus elementos `texto` / `tabla` / `auto` / `grafica`, textos y filas propuestos (`valores_iniciales`, `completar`), marcas `{la_materia}`, `{norma}`… por etapa (`marcas`), y los cálculos de lo automático (`preparar`, `tabla_auto`, `grafica_png`). Sin Streamlit ni Word. |
| `tools/programacion_didactica.py` | Word de la programación didáctica (`generar_docx(materia, redaccion, datos, template_source)`): construye el cuerpo de cada capítulo como subdocumento de docxtpl. |
| `tools/plantilla_didactica.py` | Construye la plantilla Word por defecto de la programación didáctica (`python -m tools.plantilla_didactica`). |
| `tools/ajuste_pesos.py` | IPF (Sinkhorn/RAS) para sugerir P y PIL a partir de % objetivo por instrumento + reparto horario. |
| `tools/sesiones_calendario.py` | Descarga/parsea el calendario escolar JCyL y cuenta días lectivos/sesiones por evaluación. |
| `tools/situaciones_informe.py` | Gráficos matplotlib, tablas HTML «estilo Word», botones JS de copiar, CSS de AgGrid. |
| `templates/programacion_aula_template.docx` / `templates/informacion_familias_template.docx` / `templates/programacion_didactica_template.docx` | Plantillas Word por defecto (las únicas versionadas). |

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

- **Contenidos de Tecnología e Ingeniería I y II, Digitalización 4º, TIC II y Ámbito Práctico 4º**: la lista viene de las programaciones Excel del centro y sustituye a la del decreto (códigos `A.1.1`; en Tecnología e Ingeniería cambian también el número y los textos: I 21→14, II 18→61). Las demás materias siguen con su codificación.  
- **Transversales**: mandan los enunciados y la numeración de `curriculo.db`, también frente a los Excel. En Bachillerato los Excel numeraban distinto (su CT 2 era oratoria, el 3 de la base): al migrar se convirtió 2 → 3.
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
recalcula con `recompute`), `actividades(id, orden, sa, ie, titulo)` +
`actividad_indicadores(actividad, il, peso, orden)` (schema 2; en el schema 1
`actividades(orden, il, descripcion, peso)`, una actividad por IL: al abrir se
convierte con `desde_formato_antiguo`, PA pasa a % del IL),
`datos_generales(campo, valor)`, `familias(campo, valor)`, `redaccion(clave, tipo, valor)` (redacción de la programación didáctica: `tipo` = `texto` (valor = el texto), `opcion` (`1`/`0`: si aparece una tabla o gráfica automática) o `tabla` (valor = JSON con la lista de filas `{columna: texto}`); los proyectos anteriores no tienen la tabla y se abren con lo propuesto).

- **Categorías de IL (schema 3, opcionales, 2026-11-20)**: `categorias(id, nombre, orden)`, `categoria_opciones(id, categoria, nombre, orden)` e `indicador_categoria(indicador, categoria, opcion)` (`indicador` = `indicadores.orden`). Se guardan **ids**, no nombres: renombrar no toca las asignaciones y borrar una opción/categoría las quita de los IL. Los ids son únicos en todo el proyecto (categorías y opciones comparten contador). En sesión: `il_categorias` (`[{"id","nombre","opciones":[{"id","nombre"}]}]`) y `fila["CAT"] = {id_categoria: id_opcion}` en cada fila de `il_rows` (`recompute` conserva claves extra). Sin categorías no se escribe ninguna fila ni aparece nada en pantalla.
- Se escribe entero cada vez (`guardar_proyecto`: base nueva en memoria +
  `serialize()`), no se actualiza en sitio.

#### Compatibilidad del proyecto (reglas para ampliar el modelo)
El archivo se **reescribe entero** con el esquema actual, así que un proyecto antiguo se «actualiza» solo al descargarlo. Para que no haya conflictos:
1. **Solo se añade**: tablas nuevas (o columnas con `DEFAULT`); nunca se cambia el significado de las que existen. Quitar una función = dejar de escribir su tabla (los archivos viejos que la tengan se limpian al guardar).
2. **Leer con tolerancia**: cada bloque nuevo comprueba que su tabla exista (`_tabla_existe`) y, si no, devuelve lo vacío/propuesto; las consultas nombran sus columnas (no `SELECT *`), así que se ignoran las tablas y columnas que esta versión no conoce.
3. **Datos huérfanos fuera al leer y al escribir** (`limpiar_filas`, `normalizar`): una asignación a algo que ya no existe se descarta, no rompe.
4. **`schema_version` es informativo** (hoy `"3"`): `leer_proyecto` no rechaza por versión. Una app antigua abre un archivo nuevo (ignora lo que no conoce y al guardar pierde esos datos). Excepción histórica: el schema 2 de actividades no se abre en versiones anteriores.
5. En la **sesión** (`_cargar_estado`) toda clave nueva se inicializa con `estado.get(...)` y se limpia en las listas de claves que se borran al cambiar de proyecto (`ilcat_` para los widgets de categorías).
- **Todos los códigos deben existir en el currículo de la materia** (CE,
  CON, CT, DO). Lo comprueba `consistencia.revisar`; los pesos de CE que ya no
  existen se descartan al cargar y un CE nuevo empieza con P = 0.

### Abreviaturas
- **SA** situación de aprendizaje (nº) · **EV** evaluación/trimestre (1-3) · **DSA** descripción/título · **HSA** horas.
- **CE** criterio de evaluación (p. ej. `4.2`) · **CED** su descripción · **P** peso del CE · **%CE** = P/ΣP.
- **IL** indicador de logro (`4.2.1`, automático y correlativo dentro del CE) · **PIL** peso · **PIL%** = PIL/ΣPIL del CE · **DIL** descripción · **DO** descriptores operativos.
- **CON** contenidos de la materia · **CT** contenidos transversales.
- **IE** instrumento de evaluación · **CC** criterio de calificación · **AE** agente evaluador.
- **A** código de actividad (`A1`, `A2`… dentro de su SA) · **PA** peso de una actividad dentro de un IL: la parte del IL que se evalúa en ella es PA/ΣPA de ese IL (quien trabaje en % pone pesos que sumen 100). Si el IL está en una sola actividad cuenta 100 %; PA vacío en un IL compartido = pendiente (mientras tanto cuenta como la media de los demás).
- Competencia específica de un CE = su primer número (`2.4` → 2); su peso = Σ %CE de sus criterios.

### Fórmulas de peso (réplicas de las dinámicas/DAX del antiguo Excel)
- Peso de un IL sobre la programación = `(PIL/ΣPIL del CE) · (P/ΣP)`.
- **Factor iDoceo/Additio** de un IL en una actividad = `PIL · PA/ΣPA` (fracción del IL en esa actividad). Solo en pantalla (cuadros 2 y 3 de Actividades); no va al Word.
- Valor de una actividad sobre la programación = Σ de sus IL de `(PA/ΣPA) · (PIL/ΣPIL del CE) · (P/ΣP)`; sobre la SA = ese valor / Σ de la SA.

## 5. Guardado

- `_guardar_todo()` (`app.py`) = `_estado_actual()` (todo lo que hay en sesión) →
  `proyecto.guardar_proyecto(...)`. Devuelve los bytes del `.sqlite` y el sello.
- Los campos de aula de cada SA se emparejan **por título** (`pa_sa_edits` en
  sesión o `pa_sa_cols` cargados); título y trimestre salen siempre de la tabla
  de SA.

## 6. Arquitectura de la UI (`app.py`)

- **Barra lateral**: menú de **3 grupos numerados** con sus páginas, definido en la lista `NAV` de `app.py` (grupo → `(id, etiqueta)`). Cada entrada es un `st.button` dentro del contenedor `menu` (la activa es la primaria; CSS `.st-key-menu`, `.nav-grupo`); el id va en `active_page` y es lo que miran los `if page == …`. Debajo, el origen del currículo. Añadir una página = una línea en `NAV` + su bloque `elif`.
  - **1 · Programación didáctica**
    - **Diseño de la programación** (en Indicadores de logro hay un desplegable cerrado «Categorías de los indicadores (opcional)»: cada categoría definida —p. ej. «Destrezas»— añade una columna con desplegable a la rejilla; al cambiarlas se consolida lo tecleado y se remonta la rejilla con `il_nonce`; aún no salen en los Word) — pestañas: Situaciones de aprendizaje · Sesiones por evaluación · Criterios de evaluación · Indicadores de logro · Ajuste de pesos · Distribución CE × SA · Peso final por instrumento.
    - **Contenidos** — Contenidos de la materia (con su bloque) · Contenidos transversales (🟢 asignado a algún IL / 🔴 no).
    - **Redacción** (`ui/redaccion.py`) — una pestaña por capítulo de la programación didáctica (`tabs_redaccion`): Portada · a Introducción · b Evaluación inicial · c Competencias específicas · d Criterios y contenidos · e Transversales · f Metodología · g Proyectos significativos · h Materiales y recursos · i Planes del centro · j Complementarias y extraescolares · k Evaluación del alumnado · l Diferencias individuales · m Secuencia · n Práctica docente · ñ Evaluación de la programación · Anexos. En cada una: título con etiqueta de textos sin rellenar, desplegable «Qué pide la guía de la Junta» y sus elementos: **textos** (con propuesta y ayuda en el propio campo), **tablas** de añadir/quitar filas (cuadro con franja azul), **tablas automáticas** (cuadro plata: casilla «Aparece en el documento» y vista previa) y **gráficas** (cuadro discontinuo: casilla «Aparece esta gráfica» y «Ver la gráfica»).
  - **2 · Programación de aula** (un solo bloque `elif page in ("aula_datos", "aula_sa", "doc_aula")` con la preparación común; `_Zona` hace de pestaña para lo que ya no va en pestañas)
    - **Datos generales** (`aula_datos`).
    - **Situaciones de aprendizaje** (`aula_sa`) — pestañas Descripción SA (selector de SA + campos de texto de `SA_CAMPOS`) · Actividades por SA (`ui/actividades.py`): selector de SA en una **banda azul destacada** (es la selección principal; también en Descripción SA) y tres cuadros numerados con franja azul. **1 · Actividades**: una fila por actividad con el fondo de su color (código A, nombre editable, papelera, IL en un `multiselect` con una etiqueta por línea «código · texto», instrumento = el de sus IL, % prog., % SA, total y «Añadir actividad»). **2 · Peso de cada actividad en su indicador**: un bloque por IL de la SA (código, texto completo e instrumento arriba) y dentro una fila por actividad (**Peso** editable, % automático, % prog., % SA, factor iDoceo/Additio; «Sin actividad» / «Faltan pesos» como etiquetas). **3 · Vista en el cuaderno**: columnas pastel por actividad con «CE 1.1 × factor» (factor sumado por CE; «× ?» si faltan pesos; solo pantalla). Una SA sin actividades se abre **vacía** (2026-11-22; antes creaba una por IL) con un aviso de cuántos IL no están en ninguna actividad, y los cuadros 2 y 3 solo salen si hay alguna. Las dos pestañas comparten la SA elegida (`pa_sa_actual`; cada una tiene su selector, `pa_sa_sel_campos` / `pa_sa_sel`, que se inicializa con ella).
  - **3 · Generación de documentos**
    - **Programación didáctica** (`doc_didactica`) — plantilla opcional + Generar/Descargar Word, «Descargar la plantilla por defecto» y aviso de los textos de Redacción sin rellenar.
    - **Programación de aula** (`doc_aula`) — plantilla opcional + Generar/Descargar Word.
    - **Otros informes** (`doc_otros`) — por ahora solo **Información a familias**, entera: Generar/Descargar Word (+ plantilla opcional) · aviso de campos vacíos · pestañas Competencias específicas (solo lectura, del currículo) · Calificación y promoción · Atención individualizada · Vista previa por SA. Cuando haya más informes, selector de informe arriba.
- **Barra global** arriba (`_abrir_o_crear`). **Sin proyecto**: tarjeta con el `segmented_control` (`proy_modo`) **Abrir proyecto** (uploader `.sqlite`) / **Nuevo proyecto** (Etapa → Curso → Materia + Crear). **Con proyecto**: una sola línea de 45 px (`st-key-proybar`) con materia · curso · guardado (la normativa, al pasar el ratón), el desplegable **«Cambiar de proyecto»** (`st.popover` con lo mismo, apilado) y el botón **«Guardar proyecto»** con su mensaje a la derecha (HTML/JS propio, `_guardar_archivo_html`): `showSaveFilePicker` en Chrome/Edge, descarga normal en Firefox/Safari. Prefijo `AAAAMMDD_HHMM_` calculado **en JS al hacer clic**; `_nombre_sin_sello` evita acumular prefijos. Nombre base: el del archivo abierto o el id de la materia.
- El proyecto de salida (`prog_out`) se **recalcula solo** cuando falta; **cualquier edición hace `pop("prog_out")`**. Si hay incoherencias, se muestra `_dlg_coherencia` una vez por proyecto cargado (`consist_seen`, se marca al abrir el diálogo).

### Patrones de estado (session_state)
- `_cargar_estado(estado, nombre)` rellena la sesión desde un proyecto (o uno nuevo, `estado_vacio`) + el currículo de su materia: `cur` (lo de `cargar_materia`), `proy_materia`, `proy_nombre`, `sa_df`, `sa_previstas`, `sa_fechas_trimestre`, `sa_horas_dia`, `sa_festivo_local`, `il_rows`, `il_ce_list`, `il_ce_ced`, `il_ce_p`, `il_aux`, `elementos`, `pa_*`, `fam_campos`; y borra derivados y widgets (`prog_out`, `sa_grid_rows`, `ce_rows`, `il_pending`, `consist_seen`, `fam_w_*`, `pad_*`, `pasa_*`, `ses_*`…).
- Un archivo subido solo se carga si es **nuevo** (`proy_file_seen` = nombre + md5): así «Crear» no queda pisado por el archivo que siga en el uploader.
- **Canónico vs. pendiente**: `sa_grid_rows`/`ce_rows`/`il_rows` son lo canónico; lo que hay en la rejilla AgGrid se lee cada rerun (`il_pending`, `ce_pending`…). El botón **Actualizar** consolida y remonta la rejilla subiendo un **nonce** en la `key` (`sa_nonce`, `ce_nonce`, `il_nonce`).
- `red` (redacción) = `{"textos", "tablas", "opciones"}`, siempre completo (`redaccion.completar`: lo guardado manda, aunque esté vacío; lo demás, lo propuesto). Sus widgets son `redw_…` y siguen el patrón de Actividades (se rellenan desde `red` antes de pintarlos y su `on_change` escribe en `red`). El Word generado es `pd_docx`.
- `pa_acts` (actividades) no va en rejilla: widgets de Streamlit cuyo `on_change` escribe en `pa_acts` (ver «Actividades» en las trampas).
- Pestañas persistentes con `_pestanas(key, títulos)`.
- En **Diseño** el cuerpo de **todas** las pestañas se ejecuta siempre (unas usan variables de otras: `sits`, `ce_p`, `pending`). En las otras páginas sí se mira `.open`.
- La tabla de **situaciones de aprendizaje manda** dentro del proyecto; el **currículo manda** sobre los códigos.

### Trucos/trampas conocidas
- **AgGrid en iframe** dentro de pestaña oculta/expander se monta con ancho 0 → parche JS al principio de `app.py`.
- **Tablas nativas de Streamlit (`st.dataframe`/`st.data_editor`, dibujadas en `<canvas>`) salían en negro** en el navegador del usuario en Ajuste de pesos, Peso final por instrumento, Competencias específicas y Vista previa por SA de familias (otras sí se veían; en Chrome headless todas bien). Se cambiaron a tabla HTML (`_tabla_html`) o AgGrid. Si vuelve a pasar en otra tabla, mismo remedio.
- En Distribución CE × SA, `ColumnsAutoSizeMode.FIT_CONTENTS` se calculaba con la pestaña oculta y recortaba los valores → anchos fijos.
- Para ver la app de verdad sin navegador visible: script de captura por CDP (Chrome headless + `websockets`, esperar ~30 s) sobre un «harness» que sustituye `st.file_uploader` por un `.sqlite` de prueba y fija `active_page` / `_last_tabs_diseno` / `_last_tabs_aula`.
- **Clic en celda → diálogo**: `onCellClicked` escribe en una columna oculta `_pick` (`campo|fila|timestamp`); Python lo detecta comparando con `il_pick_seen`. En Indicadores sirve para **DO, CON y CT** (ticks); en DO solo se ofrecen los descriptores que el currículo vincula a ese CE (+ los ya marcados). Al añadir un IL, DO trae los descriptores del CE.
- **`st.dialog`**: un `on_click` dentro del diálogo solo relanza el diálogo (es un fragment) → botón imperativo + `st.rerun(scope="app")`. **Dos `st.dialog` en la misma ejecución revientan** (`StreamlitDuplicateElementId`): `_dlg_coherencia` es un envoltorio que lo abre como mucho una vez por ejecución.
- **Campos de texto sin botón Actualizar** (calculadora de sesiones, Datos generales, campos de aula de la SA, familias) llevan `on_change` que copia el valor al estado e invalida `prog_out` **antes** del rerun (`_invalidar_prog_out`, `_pad_sync`, `_pasa_sync`, `_fam_sync`): la barra de arriba calcula el proyecto antes de que la página vuelva a pintar los campos.
- **Filtro por SA en Indicadores de logro** (`il_filtro_sa`): filtro externo de AgGrid (`doesExternalFilterPass`), no se recorta el DataFrame. La rejilla va con `data_return_mode="AS_INPUT"` (por defecto st_aggrid devuelve **solo las filas filtradas** y se perderían al Actualizar/Borrar). Cambiar el filtro remonta la rejilla (va en la `key`), así que antes consolida lo pendiente en `il_rows`. Con filtro, «Añadir» crea los IL en esa SA.
- **Actividades** (`ui/actividades.py`): los widgets de cada fila (`paact_tit_<id>`, `paact_ils_<id>`, `paact_pa_<id>_<IL>`) se **rellenan desde `pa_acts` en cada ejecución**, justo antes de pintarlos, y su `on_change` (`_al_cambiar_actividad`, `_al_cambiar_peso`) escribe en `pa_acts`; así no hay que borrar claves cuando algo cambia desde fuera. Borrar y añadir van con `on_click`. Al elegir IL, el instrumento de la actividad pasa a ser el del primer IL y solo se ofrecen los IL de la SA con ese instrumento (todos si aún no hay ninguno). El `multiselect` enseña «código · texto» del IL, una etiqueta por línea cortada con «…» (el texto entero sale al pasar el ratón: Streamlit pone `title` en la etiqueta); para eso el CSS de `ui/actividades.py` quita la altura fija de la casilla (`[role="group"]` con `max-height: 40px`) y apila las etiquetas. Si se cambia `ui/actividades.py` con la app abierta, reiniciarla (el módulo importado no siempre se recarga). Las actividades apuntan al IL **por su código**: se diseñan con las programaciones ya entregadas (IL bloqueados todo el curso), así que no se reenlazan al renumerar; si algo cambia, la coherencia avisa (IL inexistente, de otra SA o de otro instrumento) y el arreglo los quita.
- **Sesiones que sobreviven a un despliegue** (Streamlit Cloud recarga el código sin perder `session_state`, y el mismo archivo no se vuelve a leer por `proy_file_seen`): el estado puede venir con el formato de la versión anterior. Por eso, justo tras la barra de abrir proyecto, las actividades sin `id` se convierten con `desde_formato_antiguo`. Si se vuelve a cambiar un formato de sesión, hacer lo mismo.
- **`ImportError` en Streamlit Cloud tras un push** que añade funciones a un módulo de `tools/` (2026-11-13, `valores_enlaces`): el servidor recoge el código nuevo pero conserva en memoria el módulo antiguo. Se arregla con «Manage app» › **Reboot app**; el código está bien.
- **Celdas HTML descuadradas**: Streamlit pone `margin-bottom: -1rem` al contenedor de cada `st.markdown` (espera un `<p>`); con un `<div>` propio la celda mide 16 px menos y las filas de `st.columns` bailan o se recortan. En Actividades se anula dentro de los cuadros (`[class*="st-key-actbox_"] [data-testid="stMarkdownContainer"] { margin-bottom: 0 }`). Para medir de verdad: `getBoundingClientRect` por CDP, no a ojo.
- **AppTest y `format_func`**: debe devolver lo mismo si recibe una etiqueta ya formateada (si no, `select_index` falla con «is not in list»); por eso el «SA n: título» del selector está en el diccionario `_lbl` y no en la función.
- EV en la rejilla de SA va como **texto** (con desplegable numérico daba «invalid number»).
- Selectores con valores fuera de lista: `_with_existing()` añade los valores presentes.
- **Maquetación del Word de familias** (`_fila` en `tools/info_familias.py`): filas que no se parten, cabecera repetida y «conservar con el siguiente». **Ojo:** `cell.text = …` borra el formato del párrafo → aplicar `_fila` después. Para revisar páginas: Word por COM → PDF y PyMuPDF.
- **Estilo de Programación de aula**: títulos de sección con `_seccion(título, n, sub)` (clase `.pa-sec`), etiquetas de estado `.pa-tag ok|warn|info` (siempre con texto, no solo color; grises ≥ 4,5:1). **Un tono pastel por actividad** (`TONOS` en `ui/actividades.py`, por posición en la SA): el mismo en su código A de los cuadros 1 y 2 y en su columna de la Vista en el cuaderno. El CSS propio de la pestaña (`.act-*`) está en `ui/actividades.py`; el de `.pa-tag`, `.pa-sec`, la tabla `.cuad` y la banda del selector de SA (`st-key-pasel_…`), en `app.py`. Para retocar un widget concreto: Streamlit pone la clase `st-key-<key>` en su contenedor; las etiquetas de `st.multiselect` son `[data-tag]` (no `[data-baseweb="tag"]`, que ya no existe en 1.63). Para capturas, lanzar Streamlit **desde la carpeta del proyecto** (si no, no lee `.streamlit/config.toml` y sale en tema oscuro).
- **«Guardar proyecto» y el último campo tecleado**: Streamlit no recibe el texto de un campo hasta que se sale de él. Si se pulsaba Guardar con el cursor dentro, el clic lo sacaba del campo, la app se recalculaba y cambiaba el iframe del botón a mitad del clic: se guardaba el proyecto de antes. Ahora el guardado lo hace una función que el iframe deja en la página (`window.parent.__iesGuardar`, creada con `new parent.Function` para que sobreviva al iframe; ver `_JS_GUARDAR`): espera a que Streamlit termine (`data-test-script-state` de `stApp`) y guarda lo que publique el iframe más reciente en `__iesDatos`. Probado con clic real por CDP (el botón tiene que estar a la vista: el scroll es de `stMain`, no de la ventana).
- **Pestañas** (`st.tabs`, CSS general de `app.py`): selector segmentado — carril gris suave `#EDF1F6` y la activa como ficha blanca con texto azul; si no caben, saltan de línea dentro del carril. En Streamlit 1.63 las pestañas son de react-aria: la raya del seleccionado es `.react-aria-SelectionIndicator` (hijo de la pestaña) y la línea del carril el `::after` del `tablist`; los `[data-baseweb="tab-highlight"]` de antes ya no existen. Si tras actualizar Streamlit vuelve a salir una raya, inspeccionar el DOM por CDP.
- **Columna «::auto_unique_id::» en una rejilla**: st_aggrid (1.2.x) añade esa columna interna **al propio DataFrame que se le pasa**. Si ese DataFrame vive en la sesión (pasaba con `ipf_obj_df`, Ajuste de pesos), a la siguiente ejecución `GridOptionsBuilder.from_dataframe` la toma como una columna más y se ve (0, 1, 2…). Remedio: dar a AgGrid una copia.
- **Botones** (CSS general de `app.py`): todos los `st.button` primarios/secundarios y `st.download_button` van **al ancho de su texto**, 36 px de alto y texto 0,92 rem seminegrita, aunque lleven `use_container_width` (el CSS pone `width: auto`). Por eso las filas de botones usan columnas estrechas + una columna vacía al final. «Guardar proyecto» (HTML propio, iframe de 38 px) sigue el mismo tamaño. Una **franja de color sobre una esquina redondeada** se pinta con `box-shadow: inset` (un `border-top` grueso se afila en las esquinas).
- **Etiquetas del selector de IL** (Actividades): Streamlit les pone `margin-bottom: 5px` con mucha especificidad; para anularlo hace falta el selector largo (`… [data-testid="stMultiSelect"] [role="group"] span[data-tag]`).
- docxtpl usa `jinja2.ChainableUndefined` (un TOC cacheado en la plantilla puede dejar `{{ situacion.titulo }}` fuera del bucle).
- **AppTest** no simula bien los botones dentro de un `st.dialog` (relanza la app entera, no el fragment): los autoarreglos se prueban llamando a `tools.consistencia` directamente.

## 7. Plantilla Word

Variables: datos generales (`materia`, `curso`, `grupo`, `docente`, `numero_alumnos`, `alumnos_atencion_individualizada`, `caracteristicas_fisicas_cognitivas_afectivas`, `nivel_competencia_curricular`, `otras_caracteristicas_grupo`, `resultados_evaluacion_inicial`, `conclusiones_evaluacion_inicial`, `resultados_evaluacion_aprendizajes`, `revision_programacion`) y un bucle `{% for situacion in situaciones %}` con `situacion.numero/titulo/trimestre/contextualizacion/…` (`SA_CAMPOS`) y las subtablas `{{p situacion.tabla_indicadores}}` (CE, IL, CT, IE, CC, AE) y `{{p situacion.tabla_actividades}}` (A, Actividad, Instrumento, IL, Valor s/ programación, Valor s/ SA).

### Programación didáctica (`templates/programacion_didactica_template.docx`)

Todo en **blanco y negro** (petición del usuario): títulos en negro, cabeceras de tabla en gris `D9D9D9` con letra negra, bandas `F2F2F2` y gráficas en grises con tramas (`build_pie_png_simple(..., grises=True)`). Tras la portada lleva un **índice** (campo TOC de Word con los títulos de nivel 1, marcado como pendiente: Word pregunta al abrir si actualiza los campos, o clic derecho › Actualizar campo). Portada: `{{ materia }}`, `{{ curso }}`, `{{ curso_academico }}`, `{{ centro }}`, `{{ departamento }}`, `{{ profesorado }}` (cada dato dentro de un `{%p if … %}`). Cuerpo de cada capítulo: `{{p cap_a }}` … `{{p cap_m }}`, `{{p cap_n }}`, `{{p cap_nn }}` (ñ) y anexos generados `{{p cap_anexo_1 }}` (contenidos), `{{p cap_anexo_2 }}` (transversales), `{{p cap_anexo_3 }}` (competencias y criterios), con `hay_anexo_1…3` para quitar su título. La plantilla por defecto pone a–m en el cuerpo y n) y ñ) como anexos IV y V, como la programación entregada; para cambiar el orden basta mover las etiquetas en Word.

## 8. Decisiones tomadas (y por qué)

- **2026-10-26: del Excel a currículo + proyecto SQLite.** El Excel obligaba a escritura quirúrgica del ZIP con regex (~1000 líneas frágiles, para no romper Power Pivot) y cada Excel llevaba su copia del currículo. Ahora: currículo único en `curriculo.db` (GitHub, descarga automática), proyecto propio `.sqlite` que se sube/descarga, selección etapa → curso → materia. Decisiones del usuario: ante códigos que no casan, **avisar y ofrecer arreglo** (no bloquear ni limpiar solo); **catálogos IE/CC/AE comunes** en `curriculo.db`; flujo **subir/descargar**; **sin importador** de Excel en la app (son unas 6 programaciones: se convierten con Claude.ai).
- Coste asumido: el proyecto ya no se abre en Excel (sin dinámicas ni segmentaciones; la app replica los cálculos).
- Un único botón «Guardar proyecto», sin paso previo; no recuerda el archivo entre guardados (un intento anterior se quedaba colgado).
- Fechas/horas por día/festivo local se guardan en el proyecto → no repensarlas cada curso.
- Sin logotipos institucionales (b64569e).
- Contenidos, transversales y DO se marcan con ticks en un diálogo, no a mano.
- **Información a familias** (2026-10-15), a partir del PowerPoint de inspección (Orden EDU/424/2024 art. 12 y 425/2024 art. 10): Word con plantilla; contenido = resumen por criterio + **una página por SA** con CE → sus IL (**sin el texto del IL**) + **tarta de instrumentos de cada SA**; **no** calcular el peso de las competencias clave a partir de DO (por ahora). Desde 2026-10-26 el texto de las competencias específicas sale del currículo.
- **Actividades (2026-10-26)**: una actividad es de una SA y un instrumento, tiene título y evalúa varios IL de esa SA con ese instrumento. Si un IL está en varias actividades se **insta a repartir** su peso (aviso en la pestaña + aviso de coherencia con arreglo «a partes iguales»). Se diseñan después de entregar la programación: los IL ya no cambian.
- **Actividades, rediseño (2026-11-13)**: las tarjetas no eran usables → tres cuadros en tabla (ver §6). El reparto de un IL compartido pasa de «% que debe sumar 100» a **pesos relativos** (el % se calcula solo); los proyectos anteriores valen igual (sus % son pesos). El arreglo «a partes iguales» pone peso 1 a cada actividad. Requisito del usuario: poder modificarlo **sin IA y solo con Python** → pestaña en archivo propio, widgets nativos (no AgGrid/JS) y comentarios de guía. Se quitaron las cifras-resumen de la SA, el diálogo «Ver resumen» de un IL y el botón «Copiar tabla (Word)» de actividades (la tabla va en el Word).
- **Redacción de la programación didáctica (2026-11-13)**: referencias = guía de la Junta (apartados a–ñ) y la programación de 3º Diversificación entregada en 2026-27 (más resumida), ambas en `ejemplos/Ejemplos_redaccion` (fuera de git). Se sigue la forma de la entregada sin dejar fuera nada de la guía: lo que la guía pide y la entregada no lleva (indicadores de logro desglosados, instrumento/agente/SA por indicador, peso por SA) está como tabla automática **desactivada**. Peticiones del usuario: un capítulo por pestaña; campos también para lo que hay que inferir (pendientes, copia, ausencias, absentismo…); donde va una gráfica, solo una casilla «aparece»; contenidos siempre de la base de datos; tablas de libros, recursos, planes, extraescolares… con añadir/quitar filas. Reglas del Word: un texto vacío no sale (ni su rótulo); de una tabla del docente salen las filas con algo escrito (si tiene columnas de texto largo, las que lo tengan relleno) y se quitan las columnas vacías; las líneas que empiezan por «- » salen como lista. Los textos propuestos no citan artículos concretos salvo en lo seguro (cambian entre ESO y Bachillerato).
- Las medidas de atención para familias son texto **general**: nunca se usa `alumnos_atencion_individualizada` (datos de alumnos concretos).

## 9. Observaciones / posibles problemas detectados (sin verificar)

- `DEFAULT_CALENDAR_URL` apunta al curso **2026-2027**: actualizar cada curso.
- No hay tests automatizados. Para probar la UI sin navegador sirve `streamlit.testing.v1.AppTest` sustituyendo `st.file_uploader` por uno falso que devuelva un `.sqlite` de prueba.
- Si se cambian códigos en `curriculo.db`, los proyectos antiguos darán avisos de coherencia (es lo esperado).
- En el Excel de ejemplo, algunos IL tenían **frases en la columna DO** en vez de códigos: al migrar, la coherencia lo marca y el arreglo las quita.
- Un proyecto guardado con el schema 2 (actividades con varios IL, 2026-10-26) **no se abre** con una versión anterior de la app.
- Streamlit avisa de que `use_container_width` y `st.components.v1.html` están obsoletos (fechas de retirada ya pasadas): habrá que migrar a `width=` y `st.iframe`.

## 10. Pendientes / ideas

- Hacer push de `curriculo.db` a GitHub (si no, la app usa la copia local).
- Migrar las programaciones Excel antiguas que queden (las 5 de `ejemplos/Ejemplos programaciones` ya están en `.sqlite`, 2026-11-05).
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
- 2026-10-26 — Tablas que salían en negro (Ajuste de pesos, Peso final por instrumento, Competencias específicas, Vista previa por SA) pasadas a HTML/AgGrid; anchos fijos en Distribución CE × SA. Comprobado con capturas de Chrome headless.
- 2026-10-26 — Indicadores de logro: filtro por SA (Todas / SA n / Sin SA) (95811ff). Probado con AppTest (sin pérdida de filas) y captura en Chrome headless.
- 2026-10-26 — **Cambio de modelo en actividades**: actividad = SA + instrumento + título + varios IL, con reparto de peso (%) de los IL compartidos. Schema 2 del proyecto (`actividad_indicadores`), conversión automática de los proyectos antiguos (mismos valores salvo actividades antiguas con peso vacío, que ahora cuentan el 100 % de su IL). Word: tabla de actividades con instrumento e IL. Coherencia: IL que no corresponden y repartos pendientes. Probado con AppTest (crear, repartir 70/30, editar título, guardar y releer, Word) y captura en Chrome (14cf5f6).
- 2026-10-26 — Arreglo: `KeyError: 'id'` en Actividades en Streamlit Cloud con una sesión abierta antes del despliegue (actividades con el formato viejo); se convierten tras la barra de abrir proyecto (10ff5c6).
- 2026-10-27 — Repaso de `MEMORIA.md` y `README.md` tras los cambios de actividades (quitadas referencias a la antigua rejilla de actividades, `pa_nonce`, `pa_pick_seen`).
- 2026-10-27 — Programación de aula: los campos de texto de cada SA pasan a su propia pestaña «Descripción SA» (entre Datos generales y Actividades) para descargar la de actividades. Probado con AppTest.
- 2026-10-27 — Actividades: vuelve el **factor iDoceo** (`PIL · PA%`) en la línea de cada IL de la tarjeta (solo pantalla, no va al Word). Probado con AppTest.
- 2026-10-27 — **Rediseño visual de Programación de aula** (jerarquía y accesibilidad). Actividades: cifras de la SA (actividades, IL, IL sin actividad, repartos pendientes) en lugar del aviso amarillo; secciones con título y contador (Actividades · Reparto de pesos · Indicadores de esta SA · Resumen de actividades); tarjeta con código A en insignia, instrumento en etiqueta, «Borrar» discreto con icono y tabla de IL (compartido con…, parte del IL, factor iDoceo) en vez de la línea gris; etiquetas de IL en tono suave; estados con texto. Datos generales en dos secciones; Descripción SA con la SA como título (fuera los campos deshabilitados, poco contraste); etiquetas de campos con tildes (`_ETIQ`). Barra del Word alineada. Probado con AppTest (crear, repartir 70/30, título, partes iguales, borrar, guardar) y capturas en Chrome headless.
- 2026-10-27 — Actividades: etiquetas de IL del selector en neutro (el rojo sobre rosa parecía un error) y nueva sección **Vista en el cuaderno** (iDoceo/Additio) al final de la pestaña. Probado con AppTest y captura.
- 2026-10-27 — Actividades: cada tarjeta, sus etiquetas «También en…» y sus casillas de reparto llevan el color de su columna del cuaderno. Probado con AppTest y captura.
- 2026-11-05 — Migradas a `.sqlite` las 5 programaciones de `ejemplos/Ejemplos programaciones` (TIN I y II, Digitalización, Ámbito Práctico 4º, TIC II), junto a sus Excel. `curriculo.db`: contenidos de esas 5 materias sustituidos por los del Excel y corregido el CE 2.2 de Ámbito Práctico («posible»); transversales intactos. Actividades con el mismo título, SA e instrumento agrupadas en una con varios IL. Corregido `A.2.1` → `A.1.2` en el IL 1.2.1 de TIN I (no existía). Probado: fila a fila y pesos contra el Excel, coherencia sin avisos, ida y vuelta idéntica, AppTest en todas las páginas y SA, los dos Word y capturas en Chrome headless. Con el `curriculo.db` anterior dan avisos de contenidos: hace falta el push.
- 2026-11-13 — **Rediseño de Actividades** en tres cuadros (actividades · peso de cada actividad en su indicador · vista en el cuaderno), en `ui/actividades.py`; pesos relativos con % automático (`fraccion_por_enlace`, `valores_enlaces`); SA vacía → una actividad por IL. Probado con AppTest (nombre, añadir, elegir IL, pesos 2 y 1 → 66,67/33,33 %, borrar, cambiar de SA, Word), los 5 proyectos de ejemplo sin repartos pendientes y capturas en Chrome headless.
- 2026-11-13 — Actividades, segunda vuelta (más jerarquía y alineación): selector de SA en banda carmín, cuadros numerados, banda oscura de títulos de columna, filas con el color de su actividad, bloques por IL con su texto completo, selector de IL con «código · texto» por línea, celdas cuadradas (margen de `st.markdown`). Barra de proyecto alineada por abajo y botones «Generar…» a la altura de su cargador. Probado con AppTest y capturas/medidas en Chrome headless.
- 2026-11-13 — Retoque de estilo a petición del usuario (más compacto, menos «gigante»): botones de toda la app al ancho de su texto y 36 px; selector de IL con etiqueta crema sin borde, centrada con la «x» y la flecha; Vista en el cuaderno con columna «Alumnado» estrecha, tabla al ancho de sus columnas y esquinas de 8 px; cuadros de Actividades con menos aire y franja recta; banda del selector de SA más baja. Comprobado con capturas y medidas en Chrome headless (Actividades, Diseño, Familias).
- 2026-11-13 — Barra del proyecto compacta: con un proyecto abierto pasa de tarjeta (~190 px) a una línea de 45 px (materia · curso · guardado, desplegable «Cambiar de proyecto» y «Guardar proyecto» con el mensaje a su derecha); sin proyecto sigue la tarjeta de abrir/crear. Tras abrir un archivo se hace `st.rerun()` para pasar a la línea. Quitado el rótulo «Guardado: …» bajo el botón. Probado con AppTest (4 páginas) y capturas/medidas en Chrome headless; el cargador real dentro del desplegable no se ha visto en captura (el harness lo sustituye).
- 2026-11-13 — **Menú lateral con grupos**: 1 · Programación didáctica (Diseño, Contenidos, Redacción —por hacer—), 2 · Programación de aula (Datos generales, Situaciones de aprendizaje con las pestañas Descripción SA y Actividades), 3 · Generación de documentos (Programación didáctica —por hacer—, Programación de aula, Otros informes = familias). Lista `NAV` + botones en vez del `st.radio`; el botón de generar el Word de aula sale de las páginas de edición. Una sesión con la página antigua se reconduce (`_PAG_ANTES`). Probado con AppTest (las 8 entradas, Word de aula, edición de un dato general) y capturas en Chrome headless.
- 2026-11-13 — **Redacción de la programación didáctica y su Word.** `tools/redaccion.py` (17 capítulos: portada, a–ñ y anexos; textos propuestos, tablas del docente, tablas y gráficas automáticas), `ui/redaccion.py` (una pestaña por capítulo), tabla `redaccion` en el proyecto, `tools/programacion_didactica.py` + plantilla por defecto (`tools/plantilla_didactica.py`) y página «Generación de documentos › Programación didáctica». Probado con AppTest (los 17 capítulos, editar texto, añadir/quitar filas, casillas, guardado e ida y vuelta, generar Word), con el proyecto real de 3º Diversificación (mismas cifras que la programación entregada; Word → PDF con Word y revisión de las 22 páginas), con uno de Bachillerato y capturas en Chrome headless.
- 2026-11-13 — Volcada a un proyecto la programación didáctica entregada de 3º Diversificación (Ámbito Científico-Tecnológico): copia nueva de `20261029_1615_3ESO_DIVER_ACT.sqlite` en `ejemplos/Ejemplos_redaccion` con la redacción rellena (textos y tablas del Word entregado; el resto del proyecto, idéntico) y su Word generado. Añadido el texto «Qué se evalúa» al capítulo n). El volcado se hizo con un script suelto, fuera de la app.
- 2026-11-14 — Arreglo: lo tecleado en un campo (Redacción y cualquier otro) no llegaba al archivo si se pulsaba «Guardar proyecto» sin salir antes del campo; el guardado pasa a una función de la página que espera al recálculo. Reproducido y comprobado en Chrome por CDP con clic real.
- 2026-11-14 — Word de la programación didáctica: índice automático tras la portada y todo en blanco y negro (plantilla, tablas y gráficas en grises con tramas). Plantilla regenerada; revisado en PDF con el índice actualizado.
- 2026-11-14 — Pestañas de todas las páginas rediseñadas (selector segmentado, sin la raya que cruzaba la seleccionada). Comprobado con capturas en Chrome headless (Diseño y Redacción).
- 2026-11-14 — Arreglo: columna «::auto_unique_id::» visible en la rejilla de objetivos de Ajuste de pesos (se pasa una copia del DataFrame). Borrada la carpeta `.devcontainer` (plantilla de Codespaces que no se usa).
- 2026-11-14 — `ui_actividades.py` y `ui_redaccion.py` pasan a la carpeta `ui/` (`ui/actividades.py`, `ui/redaccion.py`). Probado con AppTest.
- 2026-11-14 — **Cambio de tema: azul, plata y blanco** (estilo educacyl) en lugar de carmín, oro y crema: `config.toml`, CSS de `app.py`, `ui/actividades.py`, `ui/redaccion.py`, icono de pestaña, botón «Guardar proyecto» y gráficas/tablas de `tools/situaciones_informe.py` (`COLOR_AZUL`, `COLOR_PLATA`). El primer tono de actividad pasa a ser el azul. No se han tocado los Word (el de familias sigue con cabeceras carmín: `HEADER_FILL` en `tools/info_familias.py` y `ROJO` en `tools/plantilla_familias.py`). Comprobado con AppTest y capturas en Chrome headless (inicio, Diseño, Descripción SA, Actividades).
- 2026-11-20 — **Categorías opcionales de los indicadores de logro** (p. ej. «Destrezas»): desplegable cerrado en Indicadores de logro para definir categorías y sus opciones; cada una es una columna con desplegable en la rejilla. Schema 3 del proyecto (3 tablas nuevas, ids estables) y reglas de compatibilidad con proyectos antiguos (§6, «Compatibilidad del proyecto»). Probado con un proyecto real antiguo (se abre sin categorías), ida y vuelta con categorías, datos huérfanos descartados, y AppTest (crear categoría y opciones, renombrar, borrar opción limpia los IL). Sin probar aún en navegador la columna de la rejilla ni el guardado con asignaciones hechas desde AgGrid.
- 2026-11-20 — Indicadores de logro: selector «Ocultar columnas» (CED, DIL, DO, CON, CT, IE, CC, AE, SA y las categorías) junto al filtro por SA. Se guardan las ocultas (`il_ocultas`, solo sesión, no va al proyecto) y cambiarlas consolida lo tecleado y remonta la rejilla (van en su `key`). Probado con AppTest; la rejilla real, sin ver en navegador.

- 2026-11-20 — **Ajuste de pesos por categoría**: si hay categorías de IL, un selector «Ajustar por» (Instrumento y horas · Por «Destrezas»…). En el modo por categoría se fija el % objetivo de cada opción y se propone P por criterio (suma 100) y PIL solo en criterios con indicadores de varias opciones; los IL sin opción conservan su peso; no usa el reparto horario. `tools/ajuste_pesos.py` (`pesos_globales`, `sugerir_por_categoria`) y `ui/ajuste_categoria.py`. Probado con el proyecto de inglés (reproduce la tabla de destrezas; con otros objetivos suma 100 y los porcentajes salen exactos) y AppTest (cargar P). La rejilla de objetivos, sin ver en navegador.
- 2026-11-22 — **Ajuste de pesos como tabla dinámica**: el selector «Ajustar por» (siempre visible) ofrece «Instrumento y horas» (el IPF de siempre) y **cualquier columna de los indicadores** (instrumento, criterio de calificación, agente, SA) **o categoría definida por el docente**, sin nada fijo para «Destrezas». `ui/ajuste_categoria.agrupaciones` convierte las columnas en pseudo-categorías (ids `"col:IE"`…) y `sugerir_por_categoria` las trata igual. Comprobado con datos de prueba; la pantalla, sin ver en navegador.
- 2026-11-22 — **Resumen por categorías (niveles)** en Ajuste de pesos (desplegable): el orden de las categorías es la jerarquía (cada una a la derecha subdivide la anterior; sin opción = se queda en la anterior; sin ninguna = «Sin categoría»). Las opciones siguen siendo listas definidas a mano, sin depender del padre (decisión del usuario: cada departamento lo cuida). `tools/categorias.tabla_por_niveles`. Probado con datos de prueba; pantalla sin ver en navegador. Pendiente: ajuste por hojas (combinaciones) y tabla en el Word.
- 2026-11-22 — Proyecto `20261122_1545_6Bach_ING.sqlite` reorganizado a mano (SQL directo) en dos niveles según la tabla de destrezas del departamento: «Destrezas» (Listening, Reading, Speaking, Writing, Mediation, Voc & Gram, Daily work, Interest & Participation) y «Subdestrezas» (Readers, Individual, Role-play, Writing in class). El resumen por niveles reproduce la tabla (10/15/10/20/7/35/2/1 %). Copia previa en el scratchpad de la sesión.
- 2026-11-22 — Resumen por categorías: la cabecera de las subcategorías usa el nombre de la(s) categoría(s) de la derecha (no «Subcategoría»), y la tabla agrupa con celdas combinadas, tono alterno por categoría principal y trazo azul grueso al empezar cada una.
- 2026-11-22 — Ajuste de pesos por una categoría de nivel inferior (p. ej. Skills): un indicador sin opción en ella cuenta con la de la categoría anterior (la primera que tenga), así aparecen Listening, Reading, Interest & Participation… junto a Readers, Individual… y todo se puede ajustar. `ui/ajuste_categoria.agrupaciones`. Probado con el proyecto de 6º Bach Inglés (suman 100 %, sin indicadores sin opción).
- 2026-11-22 — Actividades: una SA sin actividades ya no crea una actividad vacía por indicador (salían muchísimas que luego se agrupaban); queda vacía y avisa de los IL que no están en ninguna actividad. Los cuadros 2 y 3 solo aparecen cuando hay actividades. Comprobada la sintaxis; pantalla sin ver en navegador.
