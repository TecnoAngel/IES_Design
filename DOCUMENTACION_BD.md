# Documentación de las bases de datos — IES Diseño

Dos bases SQLite con papeles distintos. Este documento describe **qué guarda cada tabla,
cómo se relacionan y qué reglas hay que respetar para no romper la compatibilidad**.
Fuente de verdad del código: `tools/proyecto.py` (proyecto) y `tools/curriculo.py` (currículo).
Estado: estructura cerrada el 2026-11-22 (`schema_version` = `3`).

| Base | Quién la escribe | La app la… |
|---|---|---|
| `curriculo.db` | Se mantiene fuera de la app (repositorio de GitHub) | **solo lee** |
| Proyecto `.sqlite` | La app, cada vez que se pulsa «Guardar proyecto» | lee y reescribe **entera** |

---

## 1. `curriculo.db` — currículo común (solo lectura)

Descarga automática de GitHub con copia en `%LOCALAPPDATA%\IES_Diseno\`. Una fila de `materias`
por materia y curso; todo lo demás cuelga de `materias.id` (p. ej. `HES-2BACH`).

| Tabla | Clave | Contenido |
|---|---|---|
| `materias` | `id` | `nombre`, `etapa` (`ESO`/`BACH`), `curso`, `comunidad`, `normativa`. Las materias con `normativa = 'Orden EDU/1332/2023'` son los ámbitos de Diversificación (se tratan como etapa `DIVER` en la app). |
| `competencias_especificas` | `(materia_id, numero)` | Texto y `descriptores` del Perfil de salida vinculados (`'CCL1, STEM4'`). |
| `criterios` | `(materia_id, codigo)` | Criterios de evaluación (`'1.1'`), su `ce_numero` y `orden`. |
| `criterio_descriptores` | `(materia_id, criterio, descriptor)` | Descriptores operativos de cada criterio. |
| `contenidos` | `(materia_id, codigo)` | Contenidos de la materia (`'A.3.1'`) con su `bloque`. |
| `transversales` | `(etapa, comunidad, numero)` | Contenidos transversales de la etapa. |
| `descriptores` | `(codigo, etapa)` | Descriptores operativos del Perfil de salida (`CCL1`…). |
| `catalogos` | `(tipo, valor)` | Listas comunes: `IE` instrumentos, `CC` criterios de calificación, `AE` agentes evaluadores. |

Reglas: los códigos de un proyecto (CE, CON, CT, DO) **deben existir** aquí; si no, la comprobación
de coherencia avisa y ofrece arreglo (nunca bloquea). Los cambios en esta base **no** cambian el
esquema del proyecto: solo pueden provocar avisos de coherencia.

---

## 2. Proyecto del docente `.sqlite`

Un archivo por programación. Nombre: `AAAAMMDD_HHMM_<nombre>.sqlite` (el prefijo lo pone «Guardar proyecto»).
La materia se enlaza con el currículo por `meta.materia_id`.

### 2.1 Tablas

**`meta(clave, valor)`** — `schema_version`, `materia_id`, `materia_nombre`, `etapa`, `curso`, `normativa`, `actualizado` (sello `dd/mm/aaaa hh:mm`).

**`config(clave, valor)`** — `horas_previstas_1..3`, `fecha_ini_1..3` y `fecha_fin_1..3` (ISO, vacío si no hay),
`horas_dia_0..4` (lunes a viernes), `festivo_local` (ISO).

**`situaciones(numero PK, ev, titulo, horas, orden)`** — situaciones de aprendizaje (SA). `numero` es el nº de la SA.
La tabla de SA **manda** dentro del proyecto (título y trimestre de la programación de aula salen de aquí).

**`situacion_campos(numero, campo, valor)`** — campos de texto de aula de cada SA (titulo, trimestre, contextualizacion, contenidos_materia, contenidos_transversales, aprendizaje_interdisciplinar, metodos, organizacion_alumnado, cronograma, organizacion_espacio, materiales_recursos, atencion_diferencias, medidas_especificas, proceso_evaluacion, puesta_en_practica, valoracion;
`titulo` y `trimestre` no se guardan aquí). Solo se guardan los no vacíos.

**`criterios_peso(ce PK, peso)`** — peso P de cada criterio de evaluación. Un CE que ya no existe en el currículo se descarta al cargar.

**`indicadores(orden PK, ce, pil, descripcion, descriptores, contenidos, transversales, ie, cc, ae, sa)`** —
indicadores de logro (IL). `descriptores`, `contenidos` y `transversales` son texto `"A.1.1, A.1.2"`. `pil` es el peso;
`sa` el nº de la SA. **El código del IL (`4.2.1`) no se guarda**: se recalcula (correlativo dentro de su CE).
`orden` es la posición en la lista.

**`actividades(id PK, orden, sa, ie, titulo)`** y **`actividad_indicadores(actividad, il, peso, orden)`** — una actividad
es de una SA y un instrumento y evalúa varios IL; `il` es el **código** del IL (`'4.2.1'`), `peso` el peso relativo
de la actividad dentro de ese IL (vacío = pendiente). Si el IL está en una sola actividad cuenta 100 %.

**`datos_generales(campo, valor)`** — datos del grupo para la programación de aula (materia, curso, grupo, docente, numero_alumnos, alumnos_atencion_individualizada, caracteristicas_fisicas_cognitivas_afectivas, nivel_competencia_curricular, otras_caracteristicas_grupo, resultados_evaluacion_inicial, conclusiones_evaluacion_inicial, resultados_evaluacion_aprendizajes, revision_programacion).

**`familias(campo, valor)`** — textos de información a familias (`redondeo_criterios`, `redondeo_materia`, `competencias_clave`,
`promocion_titulacion`, `plan_recuperacion`, `plan_refuerzo`, `apoyos`, `adaptaciones`).

**`categorias(id PK, nombre, orden)`**, **`categoria_opciones(id PK, categoria → categorias.id, nombre, orden)`** y
**`indicador_categoria(indicador, categoria, opcion)`** — categorías opcionales de los indicadores definidas por cada
departamento (p. ej. «Destrezas», «Skills»). `indicador_categoria.indicador` = `indicadores.orden`. Se guardan **ids**,
no nombres. Los ids son únicos en todo el proyecto (categorías y opciones comparten contador). **El orden de las categorías
es la jerarquía**: cada una subdivide la anterior; sin opción en una categoría = se queda en la anterior.
Sin categorías no se escribe ninguna fila.

**`redaccion(clave PK, tipo, valor)`** — redacción de la programación didáctica. Es una tabla **abierta**: lo que se
añade no cambia el esquema. Tipos:

| `tipo` | `clave` | `valor` |
|---|---|---|
| `texto` | clave del elemento (tabla 2.3) | el texto. Incluye los ajustes `k_categorias_titulo` y `k_categorias_niveles` (nº de niveles; `0` = todos) |
| `opcion` | clave de una tabla/gráfica automática | `1` o `0`: si aparece en el Word |
| `tabla` | clave de una tabla del docente | JSON: lista de filas `{columna: texto}` |
| `extra` | id del capítulo (`a`…`nn`) o `anexo_1`…`anexo_3` | JSON: `[{"id", "nivel" 0/1/2, "encabezado", "texto"}]` — **párrafos que añade el docente** al final de su capítulo |

### 2.2 Relaciones y lo que no es una clave foránea

```
meta.materia_id ─────────────────► curriculo.db · materias.id
criterios_peso.ce, indicadores.ce ► criterios.codigo (de esa materia)
indicadores.contenidos / .transversales / .descriptores
                                  ► contenidos / transversales / criterio_descriptores
indicadores.sa, actividades.sa ───► situaciones.numero
actividad_indicadores.il ─────────► código de IL calculado (CE + correlativo)   ← por texto
indicador_categoria.indicador ────► indicadores.orden                           ← por posición
categoria_opciones.categoria ─────► categorias.id
```

Las uniones «por texto» y «por posición» no son claves foráneas de SQLite: las mantiene la app (ver 2.5).

### 2.3 Claves de `redaccion` (definidas en `tools/redaccion.py`, lista `CAPITULOS`)

Las claves **no se renombran ni se reutilizan**: son lo que liga el texto guardado con su sitio en el documento.

| Clave | Tipo | Capítulo | Etiqueta |
|---|---|---|---|
| `portada_curso_academico` | texto | portada | Curso académico |
| `portada_centro` | texto | portada | Centro |
| `portada_departamento` | texto | portada | Departamento |
| `portada_profesorado` | texto | portada | Profesorado que imparte la materia |
| `a_marco` | texto | a | Marco normativo |
| `a_conceptualizacion` | texto | a | Conceptualización y características de la materia |
| `a_objetivos` | texto | a | Contribución a los objetivos de etapa |
| `a_competencias` | texto | a | Contribución al desarrollo de las competencias clave |
| `b_planteamiento` | texto | b | Planteamiento |
| `b_instrumentos` | texto | b | Instrumentos |
| `b_tabla` | tabla | b | Tabla de la evaluación inicial |
| `b_uso` | texto | b | Uso de los resultados |
| `c_intro` | texto | c | Introducción |
| `c_competencias` | auto | c | Competencias específicas con sus descriptores operativos |
| `c_mapa` | auto | c | Mapa de relaciones competenciales |
| `d_intro` | texto | d | Introducción |
| `d_proceso` | texto | d | Cómo se han vinculado los elementos |
| `d_resumen` | auto | d | Tabla resumen por criterio de evaluación |
| `d_nota` | texto | d | Nota bajo la tabla |
| `d_indicadores` | auto | d | Criterios de evaluación desglosados en indicadores de logro |
| `e_intro` | texto | e | Introducción |
| `e_tabla` | auto | e | Contenidos transversales y situaciones de aprendizaje en que se trabajan |
| `e_convivencia` | texto | e | Bienestar emocional y convivencia escolar |
| `f_principios` | texto | f | Principios metodológicos |
| `f_metodos` | texto | f | Métodos pedagógicos |
| `f_aula` | texto | f | Metodologías de aula |
| `f_dua` | texto | f | Pautas DUA en el aula |
| `f_fases` | texto | f | Fases de la sesión |
| `f_agrupamientos` | tabla | f | Tipos de agrupamientos |
| `f_tiempos` | texto | f | Organización de tiempos y espacios |
| `f_actividades` | texto | f | Tipos de actividades |
| `g_intro` | texto | g | Planteamiento |
| `g_proyectos` | tabla | g | Proyectos |
| `h_libros` | tabla | h | Libros de texto |
| `h_intro` | texto | h | Materiales y recursos: definición |
| `h_materiales` | tabla | h | Materiales y recursos por tipo |
| `i_intro` | texto | i | Introducción |
| `i_planes` | tabla | i | Planes, programas y proyectos |
| `j_actividades` | tabla | j | Actividades |
| `j_nota` | texto | j | Nota |
| `k_intro` | texto | k | Planteamiento general |
| `k_tecnicas` | texto | k | Técnicas e instrumentos de evaluación |
| `k_instrumentos` | auto | k | Peso de cada instrumento de evaluación |
| `k_grafica_instrumentos` | grafica | k | Gráfica: peso por instrumento de evaluación |
| `k_nota_redondeo` | texto | k | Nota bajo la tabla |
| `k_categorias` | auto | k | Resumen por categorías de los indicadores (tabla dinámica) |
| `k_detalle` | auto | k | Instrumento, agente evaluador y situación de aprendizaje de cada indicador de logro |
| `k_momentos` | texto | k | Momentos de la evaluación |
| `k_agentes` | texto | k | Agentes evaluadores |
| `k_calificacion` | texto | k | Criterios de calificación |
| `k_pesos_sa` | auto | k | Peso de cada situación de aprendizaje en la calificación |
| `k_formativa` | texto | k | Evaluación formativa y oportunidades de mejora |
| `k_cualitativa` | tabla | k | Traducción entre calificación numérica y cualitativa |
| `k_redondeo` | texto | k | Redondeo |
| `k_copia` | texto | k | Copia o incumplimiento de las normas de una prueba |
| `k_ausencias` | texto | k | Ausencias justificadas |
| `k_absentismo` | texto | k | Faltas de asistencia reiteradas |
| `k_recuperacion` | texto | k | Recuperación de criterios no superados durante el curso |
| `k_pendientes` | texto | k | Alumnado con la materia pendiente de cursos anteriores |
| `k_extraordinaria` | texto | k | Evaluación extraordinaria |
| `k_neae` | texto | k | Adaptación de la evaluación para el alumnado con necesidad específica de apoyo educativo |
| `l_intro` | texto | l | Generalidades |
| `l_dua` | tabla | l | Medidas generales (DUA) |
| `l_perfiles` | tabla | l | Medidas específicas por perfil de alumnado |
| `l_refuerzo` | texto | l | Plan específico de refuerzo |
| `l_recuperacion` | texto | l | Plan específico de recuperación |
| `l_enriquecimiento` | texto | l | Plan de enriquecimiento curricular |
| `l_acceso` | texto | l | Adaptaciones curriculares de acceso |
| `l_no_significativas` | texto | l | Adaptaciones curriculares no significativas |
| `l_significativas` | texto | l | Adaptaciones curriculares significativas |
| `m_intro` | texto | m | Introducción |
| `m_secuencia` | auto | m | Tabla de situaciones de aprendizaje |
| `m_grafica_horas` | grafica | m | Gráfica: reparto de horas por situación de aprendizaje |
| `m_nota` | texto | m | Nota bajo la tabla |
| `n_intro` | texto | n | Introducción |
| `n_que` | texto | n | Qué se evalúa |
| `n_tecnicas` | texto | n | Técnicas e instrumentos |
| `n_momentos` | texto | n | Momentos |
| `n_agentes` | texto | n | Agentes evaluadores |
| `n_ind_aula` | tabla | n | Indicadores de logro: programación de aula |
| `n_ind_practica` | tabla | n | Indicadores: práctica docente |
| `nn_intro` | texto | nn | Introducción |
| `nn_que` | texto | nn | ¿Qué evaluar? Indicadores de logro |
| `nn_como` | texto | nn | ¿Cómo evaluar? Instrumentos |
| `nn_cuando` | texto | nn | ¿Cuándo evaluar? Momentos |
| `nn_quien` | texto | nn | ¿Quién evalúa? |
| `anexo1_intro` | texto | anexos | Anexo I · Introducción |
| `anexo_contenidos` | auto | anexos | Anexo I · Tabla de contenidos de la materia |
| `anexo2_intro` | texto | anexos | Anexo II · Introducción |
| `anexo_transversales` | auto | anexos | Anexo II · Tabla de contenidos transversales |
| `anexo_criterios` | auto | anexos | Anexo III · Competencias específicas y criterios de evaluación |
| `anexo_mapa_criterial` | auto | anexos | Anexo III · Mapa de relaciones criteriales |

### 2.4 Reglas de compatibilidad (las que permiten no volver a convertir las programaciones)

1. **Solo se añade.** Tablas nuevas o columnas con `DEFAULT`; nunca se cambia el significado de lo que existe.
   Quitar una función = dejar de escribir su tabla.
2. **Lectura tolerante.** Cada bloque comprueba que su tabla exista y, si no, usa lo vacío o lo propuesto. Las
   consultas nombran columnas (nada de `SELECT *`): se ignora lo que esta versión no conoce.
3. **Huérfanos fuera.** Una asignación a algo que ya no existe (opción de categoría borrada, CE que ya no está en el
   currículo, enlace a un IL inexistente) se descarta al leer y al escribir, sin error.
4. **`schema_version` es informativo.** La lectura no rechaza por versión. Una versión antigua abre un archivo nuevo, ignora
   lo que no conoce y lo pierde al guardar. Excepción histórica: el schema 2 de actividades (varios IL por actividad)
   no se abre con versiones anteriores.
5. **Se reescribe entero** con el esquema actual en cada guardado: un proyecto antiguo se actualiza solo al descargarlo.
   No hay migraciones que ejecutar.
6. **Contenido nuevo dentro de tablas abiertas** (`redaccion`: nuevos elementos y párrafos añadidos; `config`, `datos_generales`,
   `familias`, `situacion_campos`: nuevos campos) **no requiere cambio de esquema**.

#### Cómo se protege (pruebas automáticas)

`tests/test_compatibilidad.py` guarda los esquemas de cada versión (`tests/esquemas/schema_N.sql`, **nunca se editan**) y
comprueba que cada uno se abre con la app actual, se guarda y se vuelve a abrir sin perder nada; que el esquema actual solo
añade a lo congelado; y que un archivo con elementos desconocidos o datos huérfanos se abre sin error. Ejecutar:
`.venv\Scripts\python.exe -m unittest discover -s tests -t .`. Si algún día hay que cambiar el esquema: subir
`SCHEMA_VERSION`, añadir `schema_<N+1>.sql` y listarlo en `ESQUEMAS`. Si un proyecto lo guardó una versión más nueva
que la app, esta lo avisa al abrirlo.

### 2.5 Puntos delicados a tener presentes

- **El código de un IL no se guarda y las actividades lo usan** (`actividad_indicadores.il`). Si se cambian CE o el orden de
  los IL de un CE, los códigos se renumeran y las actividades pueden apuntar a otro IL o a ninguno. Por diseño las actividades
  se hacen **con la programación ya entregada** (IL bloqueados todo el curso); si algo cambia, la comprobación de coherencia
  lo avisa y el arreglo quita el enlace.
- **`indicador_categoria.indicador` es la posición** del IL. La app lo consolida al guardar (escribe las categorías con la
  posición actual), así que es seguro a través de la app. Modificar `indicadores` a mano con SQL sin repetir ese orden en
  `indicador_categoria` desalinea las categorías.
- **Los códigos de `contenidos` / `transversales` / `criterios` de `curriculo.db`** pueden cambiar (se han unificado
  contenidos de varias materias desde los Excel del centro): los proyectos no se rompen, pero la coherencia avisa y propone
  quitar los códigos que ya no existen.
- **Las claves de `redaccion` no se cambian** (2.3). Para dejar de usar un elemento basta con ocultarlo en `tools/redaccion.py`.

---

## 3. Qué hace la app con ellas

- **Abrir**: `proyecto.leer_proyecto(bytes)` → estado en sesión; `curriculo.cargar_materia` aporta el currículo de la materia.
- **Guardar**: `proyecto.guardar_proyecto(estado, materia)` → base nueva en memoria serializada; devuelve bytes y sello.
- **Revisar**: `consistencia.revisar()` comprueba códigos, SA y actividades contra el currículo y ofrece arreglos.
- Detalle de la UI y del modelo de sesión: `MEMORIA.md`.
