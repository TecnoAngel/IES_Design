"""Redacción de la programación didáctica: qué capítulos tiene y qué lleva cada uno.

Sigue la «Guía para la elaboración de la programación didáctica» de la Junta
de Castilla y León (apartados a–ñ) y, en la forma, la programación entregada
por el centro (más resumida: tablas de resumen y anexos).

Aquí solo está la **definición** (``CAPITULOS``) y los **cálculos** de lo que se
genera solo (``tabla_auto``, ``grafica_png``). La pantalla está en
``ui_redaccion.py`` y el Word en ``tools/programacion_didactica.py``.

Cada capítulo es una pestaña y una lista de elementos, en el orden en que
salen en pantalla y en el Word. Hay cuatro tipos de elemento:

``texto(...)``    Un párrafo (o varios) que escribe el docente. Puede traer un
                  texto propuesto (``defecto``) y un ``rotulo`` que se imprime
                  en negrita delante. Si se deja vacío, no sale en el Word.
``tabla(...)``    Tabla que rellena el docente añadiendo y quitando filas
                  (libros, actividades extraescolares, planes del centro…).
``auto(...)``     Tabla o lista que se genera sola con los datos de «Diseño de
                  la programación» o del currículo. Solo se elige si aparece.
``grafica(...)``  Gráfica generada con los datos de diseño. Solo se elige si
                  aparece.

Para añadir un párrafo a un capítulo basta una línea ``texto(...)`` en su
lista: la pantalla, el guardado y el Word lo recogen solos. Las claves no
deben repetirse ni cambiarse (es con lo que se guarda en el proyecto).

En los textos propuestos se pueden usar estas marcas, que se sustituyen al
crear el proyecto: ``{materia}``, ``{curso}``, ``{la_materia}`` (la materia /
el ámbito), ``{de_la_materia}``, ``{decreto}``, ``{rd}``, ``{orden_ev}`` y
``{norma}`` (la norma que fija el currículo de la materia).
"""

from __future__ import annotations

import re
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Constructores de elementos
# ---------------------------------------------------------------------------


def texto(clave: str, etiqueta: str, ayuda: str = "", defecto: str = "", *,
          rotulo: str | None = None, corto: bool = False, etapas: tuple | None = None,
          cuerpo: str | None = None) -> dict:
    """``rotulo``: título en negrita que se imprime delante en el Word (None =
    ninguno). ``corto``: campo de una línea. ``etapas``: solo en esas etapas."""
    return {"tipo": "texto", "clave": clave, "etiqueta": etiqueta, "ayuda": ayuda,
            "defecto": defecto, "rotulo": rotulo, "corto": corto, "etapas": etapas,
            "cuerpo": cuerpo}


def tabla(clave: str, etiqueta: str, columnas: list[tuple], ayuda: str = "", *,
          filas: list[list[str]] | None = None, rotulo: str | None = None,
          columnas_word: list[str] | None = None, etapas_filas: tuple | None = None,
          cuerpo: str | None = None) -> dict:
    """``columnas``: [(nombre, ancho relativo, True si el texto es largo)].
    ``filas``: filas propuestas. ``columnas_word``: columnas vacías que se
    añaden solo en el Word (para rellenar a mano: valoración, observaciones).
    ``etapas_filas``: las filas propuestas solo se ponen en esas etapas."""
    return {"tipo": "tabla", "clave": clave, "etiqueta": etiqueta, "ayuda": ayuda,
            "columnas": columnas, "filas": filas or [], "rotulo": rotulo,
            "columnas_word": columnas_word or [], "etapas_filas": etapas_filas,
            "etapas": None, "cuerpo": cuerpo}


def auto(clave: str, etiqueta: str, ayuda: str = "", *, activo: bool = True,
         rotulo: str | None = None, cuerpo: str | None = None) -> dict:
    """``activo``: si aparece mientras el docente no diga otra cosa."""
    return {"tipo": "auto", "clave": clave, "etiqueta": etiqueta, "ayuda": ayuda,
            "activo": activo, "rotulo": rotulo, "etapas": None, "cuerpo": cuerpo}


def grafica(clave: str, etiqueta: str, ayuda: str = "", *, activo: bool = True,
            cuerpo: str | None = None) -> dict:
    return {"tipo": "grafica", "clave": clave, "etiqueta": etiqueta, "ayuda": ayuda,
            "activo": activo, "rotulo": None, "etapas": None, "cuerpo": cuerpo}


def _cap(id_: str, pestana: str, titulo: str, guia: str, elementos: list[dict]) -> dict:
    return {"id": id_, "pestana": pestana, "titulo": titulo, "guia": guia, "elementos": elementos}


# ---------------------------------------------------------------------------
# Capítulos
# ---------------------------------------------------------------------------
_PLANES = [
    "Plan de Lectura", "Plan de Convivencia", "Plan de Acogida", "Plan de Acción Tutorial",
    "Plan de Atención a la Diversidad", "Plan de Igualdad", "Plan TIC / Plan Digital",
    "Plan de Contingencia", "Plan de Orientación Académica y Profesional",
]

_IND_AULA = [
    "La programación de aula sigue la normativa vigente y las directrices establecidas en la propuesta curricular.",
    "Los elementos de la programación se adaptan a las características y nivel del grupo clase.",
    "La programación ha facilitado la flexibilidad de las clases, para ajustarse a las necesidades e intereses del alumnado.",
    "Los indicadores de logro abarcan todos los criterios de evaluación establecidos para el nivel.",
    "Todos los indicadores de logro se vinculan al menos con una unidad concreta de trabajo.",
    "Los contenidos de las unidades de trabajo se vinculan a los criterios de evaluación a través de sus indicadores de logro.",
    "Los contenidos están seleccionados y secuenciados con una progresión adecuada a las características del grupo.",
    "Los elementos transversales se concretan en la programación de aula a través de las distintas unidades de trabajo, situaciones de aprendizaje y actividades.",
    "Las unidades de trabajo se concretan y secuencian siguiendo los criterios metodológicos establecidos.",
    "La metodología se adapta a las características del alumnado y a los principios de la propuesta curricular.",
    "Las situaciones de aprendizaje cumplen lo establecido en la propuesta curricular.",
    "Se han programado estrategias y actividades de atención a la diversidad.",
    "Las actividades se han diseñado en función de los contenidos a trabajar, de los criterios de evaluación y de las competencias a desarrollar.",
    "Los criterios, procedimientos e instrumentos de evaluación del progreso del alumnado están establecidos de forma clara y concreta.",
]

_IND_PRACTICA = [
    ("Planificación", "La programación se ha realizado en coordinación con el resto del profesorado que interviene en el grupo."),
    ("Planificación", "Las clases se han planificado de modo flexible."),
    ("Planificación", "Se han planificado actividades y recursos ajustados a la programación de aula y a las necesidades del alumnado."),
    ("Desarrollo del proceso", "Se plantean situaciones introductorias y motivadoras previas al tema y a las actividades que se van a trabajar."),
    ("Desarrollo del proceso", "Se ha mantenido el interés del alumnado partiendo de sus experiencias, con un lenguaje claro y adaptado."),
    ("Desarrollo del proceso", "Los contenidos y actividades se relacionan con los intereses y conocimientos previos del alumnado."),
    ("Desarrollo del proceso", "Se han propuesto actividades variadas (de diagnóstico, de introducción, de motivación, de desarrollo, de síntesis, de consolidación, de refuerzo y de ampliación)."),
    ("Desarrollo del proceso", "Se han utilizado distintos agrupamientos en función del momento, de la tarea y de los recursos."),
    ("Desarrollo del proceso", "Se ha procurado un clima de seguridad y confianza adecuado para el trabajo."),
    ("Desarrollo del proceso", "El tiempo se ha distribuido de forma adecuada."),
    ("Desarrollo del proceso", "Se han utilizado recursos didácticos variados y acordes a las características y necesidades del alumnado."),
    ("Desarrollo del proceso", "Se ha fomentado el respeto y la colaboración entre el alumnado, estableciéndose relaciones fluidas."),
    ("Desarrollo del proceso", "Se ha tenido en cuenta el nivel del alumnado y se ha respetado su ritmo de aprendizaje."),
    ("Desarrollo del proceso", "Se han propuesto actividades de ampliación y refuerzo."),
    ("Desarrollo del proceso", "Ha existido colaboración y coordinación con otros profesionales que inciden en el aula (profesorado de apoyo, especialistas…)."),
    ("Desarrollo del proceso", "Se han adaptado contenidos, actividades, metodología y recursos a los diferentes ritmos y posibilidades de aprendizaje."),
    ("Evaluación", "Se han aplicado los criterios de evaluación establecidos en la programación."),
    ("Evaluación", "Se ha realizado una evaluación inicial teniendo en cuenta la información del curso anterior y, en su caso, la del departamento de orientación."),
    ("Evaluación", "Se ha realizado una evaluación de seguimiento a lo largo del proceso."),
    ("Evaluación", "Se ha realizado una evaluación final."),
    ("Evaluación", "Se han utilizado procedimientos e instrumentos variados de recogida de información."),
    ("Evaluación", "Los instrumentos de evaluación han sido adecuados y ajustados para la evaluación de los aprendizajes."),
    ("Evaluación", "Se han corregido y explicado los trabajos y actividades del alumnado dando pautas para la mejora de sus aprendizajes."),
    ("Evaluación", "Se han utilizado estrategias y procedimientos de autoevaluación y coevaluación."),
    ("Evaluación", "Los criterios de calificación propuestos han sido ajustados y rigurosos."),
    ("Evaluación", "Las familias y el alumnado han sido adecuadamente informados sobre el proceso de evaluación: criterios de calificación y promoción."),
]

CAPITULOS: list[dict] = [
    _cap("portada", "Portada", "Portada",
         "Datos de la portada del documento. La materia y el curso salen del proyecto.",
         [
             texto("portada_curso_academico", "Curso académico", "Por ejemplo: 2026/2027.", corto=True),
             texto("portada_centro", "Centro", "Nombre del centro y localidad.", corto=True),
             texto("portada_departamento", "Departamento", "", corto=True),
             texto("portada_profesorado", "Profesorado que imparte la materia",
                   "Docente o docentes que elaboran la programación.", corto=True),
         ]),

    _cap("a", "a · Introducción",
         "Introducción: conceptualización y características de la materia",
         "Identificar brevemente las características de la materia: su papel en la actividad humana "
         "y en la sociedad actual y futura, su importancia en el currículo, su finalidad, sus "
         "características generales y su contribución a los objetivos de etapa y a las competencias "
         "clave (anexo III del currículo). Puede ser una descripción literaria o más esquemática.",
         [
             texto("a_marco", "Marco normativo",
                   "Normas que regulan la materia o el programa.",
                   "La conceptualización y características {de_la_materia} se establecen en el anexo III "
                   "del {norma}."),
             texto("a_conceptualizacion", "Conceptualización y características de la materia",
                   "Papel de la materia en la actividad humana y en la sociedad, importancia en el "
                   "currículo, finalidad y características generales."),
             texto("a_objetivos", "Contribución a los objetivos de etapa",
                   "En qué medida la materia contribuye al logro de los objetivos de la etapa."),
             texto("a_competencias", "Contribución al desarrollo de las competencias clave",
                   "A qué competencias clave contribuye más la materia y por qué."),
         ]),

    _cap("b", "b · Evaluación inicial", "Diseño de la evaluación inicial",
         "A partir de las directrices de la propuesta curricular: fechas de la evaluación inicial, "
         "técnicas e instrumentos, contenido de las pruebas (criterios de evaluación del curso "
         "anterior) y grado de participación del alumnado (heteroevaluación, autoevaluación, "
         "coevaluación).",
         [
             texto("b_planteamiento", "Planteamiento", "Para qué sirve y en qué se basa.",
                   "De acuerdo con la {orden_ev}, al comienzo del curso se realiza una evaluación inicial "
                   "según el nivel de partida del alumnado, a partir de una selección de criterios de "
                   "evaluación. Esta evaluación constituye la base para programar el proceso de enseñanza "
                   "y aprendizaje, permite identificar los conocimientos previos y detectar posibles "
                   "dificultades de aprendizaje, y es el primer paso de la evaluación continua que se "
                   "desarrolla durante todo el curso."),
             texto("b_instrumentos", "Instrumentos",
                   "Pruebas, observación, información del curso anterior… y qué contiene cada una. "
                   "Una línea por instrumento (empieza la línea con «- » para que salga como lista).",
                   rotulo="Instrumentos"),
             tabla("b_tabla", "Tabla de la evaluación inicial",
                   [("Criterios de evaluación (curso anterior)", 2.2, False),
                    ("Instrumento de evaluación", 2.4, False), ("Nº de sesiones", 1.3, False),
                    ("Fechas", 2.2, False), ("Agente evaluador", 1.8, False)],
                   "Opcional: la tabla que propone la guía. Agente: heteroevaluación, autoevaluación "
                   "o coevaluación."),
             texto("b_uso", "Uso de los resultados", "Qué se hace con lo que se obtiene.",
                   "La evaluación inicial no tiene efectos en la calificación. Sus resultados se analizan "
                   "en la sesión de evaluación inicial del equipo docente y sirven para ajustar el punto "
                   "de partida y el ritmo de las situaciones de aprendizaje, organizar los agrupamientos, "
                   "identificar al alumnado que necesita apoyo y, en su caso, orientar los planes de "
                   "refuerzo.",
                   rotulo="Uso de los resultados"),
         ]),

    _cap("c", "c · Competencias específicas",
         "Competencias específicas y vinculaciones con los descriptores operativos: mapa de "
         "relaciones competenciales",
         "Incorporar las competencias específicas de la materia y su mapa de relaciones "
         "competenciales (vinculación de cada competencia específica con los descriptores "
         "operativos del Perfil de salida). Salen del currículo de la materia.",
         [
             texto("c_intro", "Introducción", "",
                   "Las competencias específicas {de_la_materia} son las establecidas en el anexo III del "
                   "{norma}. El mapa de relaciones competenciales se establece en su anexo IV y se "
                   "reproduce al final de este apartado.\n"
                   "Los descriptores operativos de las competencias clave son el marco de referencia a "
                   "partir del cual se concretan las competencias específicas, que se convierten así en "
                   "un segundo nivel de concreción de las primeras."),
             auto("c_competencias", "Competencias específicas con sus descriptores operativos",
                  "Del currículo de la materia."),
             auto("c_mapa", "Mapa de relaciones competenciales",
                  "Competencia específica × descriptores operativos, del currículo de la materia.",
                  rotulo="Mapa de relaciones competenciales"),
         ]),

    _cap("d", "d · Criterios y contenidos",
         "Criterios de evaluación e indicadores de logro, junto a los contenidos con los que se "
         "asocian",
         "Tres tareas: desglosar los criterios de evaluación en indicadores de logro, desglosar los "
         "contenidos en unidades concretas de trabajo y vincular los contenidos a los criterios a "
         "través de los indicadores de logro. La programación entregada lo resume en una tabla por "
         "criterio (peso, contenidos, transversales, agente evaluador y situaciones de aprendizaje).",
         [
             texto("d_intro", "Introducción", "",
                   "Los criterios de evaluación y los contenidos {de_la_materia} son los establecidos en "
                   "el anexo III del {norma}. Los contenidos se pueden consultar en el anexo I de esta "
                   "programación didáctica y los criterios de evaluación en su anexo III.\n"
                   "Los contenidos de carácter transversal son los determinados en el {decreto} y se "
                   "listan, con la codificación empleada en las tablas siguientes, en el anexo II."),
             texto("d_proceso", "Cómo se han vinculado los elementos", "",
                   "Tras diseñar una serie de indicadores de logro asociados a los distintos criterios de "
                   "evaluación y asignarles un peso, y una vez definidos los instrumentos de evaluación "
                   "adecuados, se ha establecido la vinculación entre los elementos curriculares, los "
                   "agentes evaluadores y las situaciones de aprendizaje, que queda organizada de la "
                   "siguiente forma."),
             auto("d_resumen", "Tabla resumen por criterio de evaluación",
                  "CE, peso, contenidos, contenidos transversales, agente evaluador y situaciones de "
                  "aprendizaje. Sale de «Indicadores de logro»."),
             texto("d_nota", "Nota bajo la tabla", "",
                   "CE: criterio de evaluación; %CE: peso del criterio en la calificación; CT: contenidos "
                   "transversales; AE: agente evaluador; SA: situaciones de aprendizaje. La codificación "
                   "de los contenidos y de los contenidos transversales se describe en los anexos I y II."),
             auto("d_indicadores", "Criterios de evaluación desglosados en indicadores de logro",
                  "Lo pide la guía; la programación entregada no lo lleva. Cada criterio con sus "
                  "indicadores de logro, sus contenidos y sus contenidos transversales.",
                  activo=False, rotulo="Criterios de evaluación desglosados en indicadores de logro"),
         ]),

    _cap("e", "e · Transversales",
         "Contenidos de carácter transversal que se trabajarán desde la materia",
         "Temporalizar cada contenido transversal en las situaciones de aprendizaje del curso e "
         "incorporarlos a los criterios de evaluación a través de los indicadores de logro. Especial "
         "atención a los relacionados con el bienestar emocional y la convivencia escolar.",
         [
             texto("e_intro", "Introducción", "",
                   "Los contenidos de carácter transversal se trabajan des{de_la_materia} a través de los "
                   "indicadores de logro de los criterios de evaluación, tal como se recoge en el apartado "
                   "anterior. Su codificación figura en el anexo II. La tabla siguiente indica en qué "
                   "situaciones de aprendizaje se trabaja cada uno."),
             auto("e_tabla", "Contenidos transversales y situaciones de aprendizaje en que se trabajan",
                  "Sale de los contenidos transversales marcados en «Indicadores de logro»."),
             texto("e_convivencia", "Bienestar emocional y convivencia escolar",
                   "Cómo se atiende de forma especial a los contenidos transversales relacionados con "
                   "el bienestar emocional del alumnado y la mejora de la convivencia."),
         ]),

    _cap("f", "f · Metodología", "Metodología didáctica",
         "Metodología que se va a utilizar, teniendo en cuenta las orientaciones del currículo de la "
         "materia y los principios metodológicos del centro (propuesta curricular): estilos, "
         "estrategias y técnicas de enseñanza, tipos de agrupamientos y organización de tiempos y "
         "espacios.",
         [
             texto("f_principios", "Principios metodológicos", "",
                   "La metodología didáctica es el conjunto de estrategias, procedimientos y acciones "
                   "organizadas y planificadas por el profesorado, de manera consciente y reflexiva, con "
                   "la finalidad de posibilitar el aprendizaje del alumnado y el logro de los objetivos "
                   "planteados, potenciando el desarrollo de las competencias clave desde una perspectiva "
                   "transversal. Se emplearán métodos que se ajusten al nivel competencial inicial del "
                   "alumnado y tengan en cuenta la atención a la diversidad y el respeto por los distintos "
                   "ritmos y estilos de aprendizaje, mediante prácticas de trabajo individual, cooperativo "
                   "y colaborativo.\n"
                   "Con carácter general, la metodología parte de la perspectiva del profesorado como "
                   "orientador, promotor y facilitador del desarrollo competencial del alumnado, buscando "
                   "despertar y mantener su motivación hacia el aprendizaje.",
                   rotulo="Principios metodológicos"),
             texto("f_metodos", "Métodos pedagógicos",
                   "Enfoque general (metodologías activas, aprendizaje significativo, DUA…) y "
                   "principios metodológicos propios del centro.",
                   rotulo="Métodos pedagógicos"),
             texto("f_aula", "Metodologías de aula",
                   "Estilos, estrategias y técnicas concretas que se usan en clase. Una por línea, "
                   "empezando con «- », para que salgan como lista.",
                   rotulo="Metodologías de aula"),
             texto("f_dua", "Pautas DUA en el aula",
                   "Formas de implicación, de representación y de acción y expresión.",
                   rotulo="Pautas DUA en el aula"),
             texto("f_fases", "Fases de la sesión",
                   "Rutina habitual de una sesión: inicio, desarrollo y cierre.",
                   rotulo="Fases de la sesión"),
             tabla("f_agrupamientos", "Tipos de agrupamientos",
                   [("Agrupamiento", 1.4, False), ("Cuándo se usa", 5.0, True)],
                   filas=[["Individual", ""], ["Pequeño grupo", ""], ["Grupo-clase", ""]],
                   rotulo="Tipos de agrupamientos"),
             texto("f_tiempos", "Organización de tiempos y espacios",
                   "Distribución del aula, espacios distintos del aula de referencia, aula virtual…",
                   rotulo="Organización de tiempos y espacios"),
             texto("f_actividades", "Tipos de actividades",
                   "Qué tipos de actividades se van a desarrollar.",
                   rotulo="Tipos de actividades"),
         ]),

    _cap("g", "g · Proyectos significativos", "Concreción de los proyectos significativos",
         "Proyectos significativos y relevantes y resolución colaborativa de problemas que se "
         "desarrollarán desde la materia (disciplinares o interdisciplinares), con el tiempo lectivo "
         "que se les dedica. Una situación de aprendizaje puede constituir un proyecto significativo.",
         [
             texto("g_intro", "Planteamiento",
                   "Qué proyectos se desarrollan, si son disciplinares o interdisciplinares y con qué "
                   "materias, y cuánto tiempo se les dedica."),
             tabla("g_proyectos", "Proyectos",
                   [("Título", 1.8, False), ("Contextualización y resumen", 4.0, True),
                    ("Temporalización", 1.5, False), ("Criterios de evaluación", 1.4, False),
                    ("Aprendizaje interdisciplinar", 2.2, True)],
                   "Opcional: un proyecto por fila."),
         ]),

    _cap("h", "h · Materiales y recursos", "Materiales y recursos de desarrollo curricular",
         "Materiales de desarrollo curricular (elaborados con finalidad educativa: el libro de texto "
         "lo es) y recursos de desarrollo curricular (herramientas a las que se ha dotado de valor "
         "educativo): impresos, digitales e informáticos, audiovisuales y multimedia.",
         [
             tabla("h_libros", "Libros de texto",
                   [("Curso", 1.6, False), ("Editorial", 1.4, False), ("Título", 3.0, False),
                    ("ISBN", 1.6, False)]),
             texto("h_intro", "Materiales y recursos: definición", "",
                   "Se entiende por material de desarrollo curricular el producto diseñado y elaborado con "
                   "una clara finalidad educativa, al objeto de incorporar los contenidos al proceso de "
                   "enseñanza-aprendizaje, y que puede ser utilizado durante la puesta en práctica de las "
                   "situaciones de aprendizaje. Se entiende por recurso de desarrollo curricular la "
                   "herramienta o instrumento al que se le ha dotado de contenido y valor educativo, aunque "
                   "esta no fuera su finalidad original, y que es utilizado por docentes y alumnado.\n"
                   "La elección de los materiales corresponde al departamento didáctico y la de los "
                   "recursos al profesorado, teniendo en cuenta en ambos casos los criterios fijados en la "
                   "propuesta curricular."),
             tabla("h_materiales", "Materiales y recursos por tipo",
                   [("Tipo", 1.6, False), ("Materiales", 3.2, True), ("Recursos", 3.2, True)],
                   filas=[["Impresos", "", ""], ["Digitales e informáticos", "", ""],
                          ["Audiovisuales y multimedia", "", ""], ["Otros", "", ""]]),
         ]),

    _cap("i", "i · Planes del centro",
         "Concreción de planes, programas y proyectos del centro vinculados con el desarrollo del "
         "currículo de la materia",
         "Implicaciones que tienen en la materia los planes, programas y proyectos del centro "
         "(lectura, convivencia, acción tutorial, atención a la diversidad, igualdad, digitalización, "
         "orientación, acogida, contingencia…), concretando el alcance y la participación.",
         [
             texto("i_intro", "Introducción", "",
                   "A continuación se concreta la implicación {de_la_materia} en los planes, programas y "
                   "proyectos del centro."),
             tabla("i_planes", "Planes, programas y proyectos",
                   [("Plan / programa", 1.8, False), ("Implicaciones desde la materia", 4.6, True),
                    ("Temporalización", 1.4, False)],
                   "Quita los que no tenga el centro y añade los que falten.",
                   filas=[[p, "", "En todas las SA"] for p in _PLANES]),
         ]),

    _cap("j", "j · Complementarias y extraescolares", "Actividades complementarias y extraescolares",
         "Actividades complementarias y extraescolares organizadas desde la materia: título, nivel, "
         "temporalización, unidad o situación de aprendizaje vinculada y descripción.",
         [
             tabla("j_actividades", "Actividades",
                   [("Actividad", 1.8, False), ("Breve descripción", 4.2, True),
                    ("Temporalización", 1.5, False), ("SA vinculada", 1.0, False)]),
             texto("j_nota", "Nota", "",
                   "Las actividades concretas, sus fechas y su realización dependerán de la oferta "
                   "disponible y de la aprobación por los órganos del centro."),
         ]),

    _cap("k", "k · Evaluación del alumnado",
         "Evaluación del proceso de aprendizaje del alumnado y vinculación de sus elementos",
         "Qué, cómo, cuándo y quién evalúa, y cómo se califica: técnicas e instrumentos asociados a "
         "los criterios e indicadores de logro (con pruebas orales en todas las materias), momentos "
         "de la evaluación, agentes evaluadores (hetero, auto y coevaluación), criterios de "
         "calificación y adaptación de la evaluación para el alumnado con necesidad específica de "
         "apoyo educativo.",
         [
             texto("k_intro", "Planteamiento general", "",
                   "Los elementos que forman parte del proceso de evaluación son los criterios de "
                   "evaluación (y los indicadores de logro en los que se desglosan), las técnicas e "
                   "instrumentos de evaluación, los momentos de la evaluación y los agentes evaluadores. "
                   "Responden a las cuestiones de qué evaluar, cómo evaluar, cuándo evaluar y quién "
                   "evalúa. El quinto elemento es la calificación de los aprendizajes del alumnado.\n"
                   "La evaluación será continua, inmersa en el proceso de enseñanza y aprendizaje, con el "
                   "fin de detectar las dificultades en el momento en que se produzcan, averiguar sus "
                   "causas y adoptar las medidas necesarias; formativa, proporcionando una información "
                   "constante que permita mejorar tanto los procesos como los resultados; integradora, y "
                   "objetiva, valorando y reconociendo la dedicación, el esfuerzo y el rendimiento del "
                   "alumnado."),
             texto("k_tecnicas", "Técnicas e instrumentos de evaluación",
                   "Describe cada instrumento que se usa (de observación, de desempeño, de "
                   "rendimiento). Tiene que haber pruebas orales. Una línea por instrumento, empezando "
                   "con «- ».",
                   "Las técnicas por emplear serán variadas para facilitar y asegurar la evaluación integral "
                   "y objetiva del alumnado; incluirán propuestas contextualizadas y realistas, propondrán "
                   "situaciones de aprendizaje y admitirán su adaptación a la diversidad del alumnado. Se "
                   "utilizarán los siguientes instrumentos de evaluación, u otros equivalentes:",
                   rotulo="Técnicas e instrumentos de evaluación"),
             auto("k_instrumentos", "Peso de cada instrumento de evaluación",
                  "Sale del instrumento y los pesos de «Indicadores de logro»."),
             grafica("k_grafica_instrumentos", "Gráfica: peso por instrumento de evaluación",
                     "La misma de «Peso final por instrumento»."),
             texto("k_nota_redondeo", "Nota bajo la tabla", "",
                   "* Al ser tablas de visualización de resultados, la suma de los porcentajes podría no "
                   "ser exactamente 100 debido al redondeo."),
             auto("k_detalle", "Instrumento, agente evaluador y situación de aprendizaje de cada "
                  "indicador de logro",
                  "Las tablas de la guía (instrumentos, momentos y agentes por indicador) reunidas "
                  "en una. La programación entregada no la lleva.", activo=False,
                  rotulo="Instrumentos, agentes evaluadores y momentos por indicador de logro"),
             texto("k_momentos", "Momentos de la evaluación", "",
                   "La evaluación será continua, sin perjuicio de la realización, a comienzo de curso, de "
                   "una evaluación inicial. La unidad temporal de programación es la situación de "
                   "aprendizaje. Las técnicas e instrumentos se aplicarán de forma sistemática y continua "
                   "a lo largo de todo el proceso educativo.",
                   rotulo="Momentos de la evaluación"),
             texto("k_agentes", "Agentes evaluadores",
                   "Cómo cuentan la autoevaluación y la coevaluación.",
                   "Se utilizarán la heteroevaluación, la autoevaluación y la coevaluación; el agente "
                   "evaluador de cada criterio figura en la tabla del apartado d). En la autoevaluación, "
                   "la calificación propuesta por el alumno o la alumna deberá estar claramente "
                   "justificada por la rúbrica o la lista de cotejo y no podrá diferir en más de un punto "
                   "de la del profesorado, prevaleciendo en tal caso esta última. En la coevaluación el "
                   "criterio será el mismo, pero la nota final se obtendrá de la media entre ambas.",
                   rotulo="Agentes evaluadores"),
             texto("k_calificacion", "Criterios de calificación",
                   "Cómo se obtiene la nota de cada evaluación y la final.",
                   "La calificación de cada evaluación y la calificación final {de_la_materia} se obtienen "
                   "como media ponderada de las calificaciones de los criterios de evaluación trabajados "
                   "hasta ese momento, con los pesos recogidos en la tabla del apartado d). Los "
                   "instrumentos de evaluación tienen carácter orientativo y podrán sustituirse por otros "
                   "equivalentes que permitan evaluar los mismos criterios.",
                   rotulo="Criterios de calificación"),
             auto("k_pesos_sa", "Peso de cada situación de aprendizaje en la calificación",
                  "Lo pide la guía; la programación entregada no lo lleva.", activo=False,
                  rotulo="Peso de cada situación de aprendizaje"),
             texto("k_formativa", "Evaluación formativa y oportunidades de mejora",
                   "Cuántas veces y cómo se puede mejorar la calificación de un criterio.",
                   "En cuanto a la evaluación formativa, se contempla la posibilidad de, como mínimo, "
                   "permitir al alumnado mejorar una vez la calificación de los criterios de evaluación. "
                   "Si el profesorado determina la necesidad de más oportunidades, su formato se adaptará "
                   "a los ritmos y necesidades de cada grupo.",
                   rotulo="Evaluación formativa"),
             tabla("k_cualitativa", "Traducción entre calificación numérica y cualitativa",
                   [("Calificación cualitativa", 2.0, False), ("Rango numérico", 2.0, False)],
                   "Según lo que fije la propuesta curricular del centro.",
                   filas=[["Insuficiente", "0 – 4,74"], ["Suficiente", "4,75 – 5,74"],
                          ["Bien", "5,75 – 6,74"], ["Notable", "6,75 – 8,74"],
                          ["Sobresaliente", "8,75 – 10"]],
                   etapas_filas=("ESO", "DIVER"),
                   rotulo="Calificación numérica y cualitativa"),
             texto("k_redondeo", "Redondeo",
                   "Criterio de redondeo de la calificación de los criterios y de la materia, según la "
                   "propuesta curricular.",
                   rotulo="Redondeo"),
             texto("k_copia", "Copia o incumplimiento de las normas de una prueba",
                   "Qué ocurre si se sorprende a alguien copiando.",
                   "Si se sorprende a un alumno o alumna copiando, o no siguiendo las instrucciones de una "
                   "prueba, se le retirará el examen y se comunicará la incidencia a la familia. La "
                   "calificación de los criterios de evaluación afectados dependerá de las opciones de "
                   "mejora que plantee el profesorado, tal como se recoge en el apartado de evaluación "
                   "formativa.",
                   rotulo="Actuaciones ante copia o incumplimiento de las normas de una prueba"),
             texto("k_ausencias", "Ausencias justificadas",
                   "Qué pasa con las pruebas y trabajos que no se han podido hacer.",
                   "Cuando un alumno o alumna falte de forma justificada, las prácticas, los trabajos y las "
                   "pruebas que no haya podido realizar podrán adaptarse a su nueva situación. Los "
                   "criterios de evaluación asociados se evaluarán con los mismos pesos y proporciones, "
                   "aunque adaptando los instrumentos a la situación particular.",
                   rotulo="Ausencias justificadas"),
             texto("k_absentismo", "Faltas de asistencia reiteradas",
                   "Cómo se evalúa al alumnado al que no se le puede aplicar la evaluación continua "
                   "por sus faltas de asistencia (según el reglamento del centro).",
                   rotulo="Faltas de asistencia reiteradas"),
             texto("k_recuperacion", "Recuperación de criterios no superados durante el curso",
                   "Cómo y cuándo se recuperan los criterios o las evaluaciones no superadas.",
                   rotulo="Recuperación durante el curso"),
             texto("k_pendientes", "Alumnado con la materia pendiente de cursos anteriores",
                   "Cómo se evalúa y califica la materia pendiente (remite al plan de recuperación "
                   "del apartado l).",
                   rotulo="Alumnado con la materia pendiente de cursos anteriores"),
             texto("k_extraordinaria", "Evaluación extraordinaria",
                   "Qué se evalúa y cómo en la convocatoria extraordinaria.",
                   rotulo="Evaluación extraordinaria", etapas=("BACH",)),
             texto("k_neae", "Adaptación de la evaluación para el alumnado con necesidad específica "
                   "de apoyo educativo",
                   "Adaptación de tiempos, formatos e instrumentos.",
                   rotulo="Adaptación de la evaluación para el alumnado con necesidad específica de "
                          "apoyo educativo"),
         ]),

    _cap("l", "l · Diferencias individuales", "Atención a las diferencias individuales del alumnado",
         "Generalidades sobre la atención al alumnado con necesidad específica de apoyo educativo; "
         "planes específicos de refuerzo, de recuperación y de enriquecimiento curricular; y "
         "adaptaciones curriculares de acceso, no significativas y significativas. Sin datos de "
         "alumnos concretos: perfiles genéricos.",
         [
             texto("l_intro", "Generalidades", "",
                   "Los principios pedagógicos de atención al alumnado y a sus diferencias individuales "
                   "constituyen la pauta ordinaria de la acción educativa. Todo el alumnado, con "
                   "independencia de sus especificidades, tiene derecho a una educación inclusiva y de "
                   "calidad adecuada a sus características y necesidades. Las medidas que se adopten "
                   "buscarán desarrollar el máximo potencial posible del alumnado y en ningún caso podrán "
                   "suponer una discriminación que le impida obtener la titulación correspondiente."),
             tabla("l_dua", "Medidas generales (DUA)",
                   [("Principio", 1.6, False), ("Medidas", 6.0, True)],
                   filas=[["Formas de representación", ""], ["Formas de acción y expresión", ""],
                          ["Formas de implicación", ""]],
                   rotulo="Medidas generales (DUA)"),
             tabla("l_perfiles", "Medidas específicas por perfil de alumnado",
                   [("Perfil", 0.8, False), ("Medidas / planes / adaptaciones", 4.4, True),
                    ("Observaciones", 2.6, True)],
                   "Perfiles genéricos (A, B…), sin nombres ni datos que identifiquen a nadie.",
                   rotulo="Medidas específicas por perfil de alumnado"),
             texto("l_refuerzo", "Plan específico de refuerzo",
                   "Para el alumnado que no ha promocionado el curso anterior.",
                   "Para el alumnado que no haya promocionado el curso anterior se aplicarán planes "
                   "específicos de refuerzo ajustados a lo establecido en la propuesta curricular. Estos "
                   "planes se revisarán periódicamente, en diferentes momentos del curso y, en todo caso, "
                   "a su finalización.",
                   rotulo="Plan específico de refuerzo"),
             texto("l_recuperacion", "Plan específico de recuperación",
                   "Para el alumnado que ha promocionado con la materia pendiente.",
                   "Para el alumnado que haya promocionado con la materia pendiente se diseñarán y "
                   "aplicarán planes de recuperación según lo establecido en la propuesta curricular. "
                   "Estos planes se revisarán periódicamente, en diferentes momentos del curso y, en todo "
                   "caso, a su finalización.",
                   rotulo="Plan específico de recuperación"),
             texto("l_enriquecimiento", "Plan de enriquecimiento curricular",
                   "Para el alumnado cuyo progreso y características lo requieran.",
                   "Para el alumnado cuyo progreso y características lo requieran se aplicará un plan de "
                   "enriquecimiento curricular ajustado a lo establecido en la propuesta curricular, con "
                   "ampliaciones horizontales de contenidos y metodologías como el aprendizaje basado en "
                   "proyectos, la resolución de problemas de cierta complejidad o el aprendizaje "
                   "cooperativo.",
                   rotulo="Plan de enriquecimiento curricular"),
             texto("l_acceso", "Adaptaciones curriculares de acceso",
                   "Recursos espaciales, materiales, personales o de comunicación (mobiliario "
                   "adaptado, ayudas técnicas y tecnológicas…).",
                   rotulo="Adaptaciones curriculares de acceso"),
             texto("l_no_significativas", "Adaptaciones curriculares no significativas",
                   "Cambios en los elementos no prescriptivos: tiempos, actividades, metodología, "
                   "instrumentos…",
                   rotulo="Adaptaciones curriculares no significativas"),
             texto("l_significativas", "Adaptaciones curriculares significativas",
                   "Cambios en los elementos prescriptivos: competencias específicas, criterios de "
                   "evaluación…",
                   rotulo="Adaptaciones curriculares significativas"),
         ]),

    _cap("m", "m · Secuencia", "Secuencia de unidades temporales de programación",
         "Secuencia ordenada de las unidades temporales de programación (aquí, las situaciones de "
         "aprendizaje), con su número de sesiones y su distribución en el tiempo.",
         [
             texto("m_intro", "Introducción", "",
                   "Las unidades temporales de programación permiten ajustar la propuesta didáctica al "
                   "calendario escolar. En esta programación la unidad temporal es la situación de "
                   "aprendizaje. La secuencia de situaciones de aprendizaje del curso es la siguiente:"),
             auto("m_secuencia", "Tabla de situaciones de aprendizaje",
                  "SA, título, evaluación, horas y % sobre el total. Sale de «Situaciones de "
                  "aprendizaje»."),
             grafica("m_grafica_horas", "Gráfica: reparto de horas por situación de aprendizaje",
                     "La misma de «Situaciones de aprendizaje»."),
             texto("m_nota", "Nota bajo la tabla", "",
                   "La secuencia y el número de sesiones tienen carácter orientativo y podrán ajustarse a "
                   "la evolución del grupo, al calendario escolar y a las circunstancias del curso."),
         ]),

    _cap("n", "n · Práctica docente",
         "Orientaciones para la evaluación de la programación de aula y de la práctica docente",
         "A partir de las directrices de la propuesta curricular: qué se evalúa de la programación de "
         "aula (elaboración, contenido, grado de cumplimiento, revisión) y de la práctica docente "
         "(planificación, motivación, proceso de enseñanza-aprendizaje, seguimiento, evaluación), con "
         "qué técnicas e instrumentos, en qué momentos y quién evalúa.",
         [
             texto("n_intro", "Introducción", "",
                   "Estas orientaciones para evaluar la programación de aula y la práctica docente parten "
                   "de las directrices establecidas en la propuesta curricular del centro. La evaluación "
                   "persigue asegurar la calidad de los procesos de enseñanza a través de los siguientes "
                   "objetivos:\n"
                   "- Analizar y detectar si la práctica docente se adecúa a las particularidades del grupo "
                   "y a las necesidades del alumnado.\n"
                   "- Detectar dificultades particulares que puedan repercutir en el proceso de enseñanza.\n"
                   "- Comprobar que la implementación de la programación se ajusta a lo planificado.\n"
                   "- Realizar un análisis individual y colectivo de la labor docente con la intención de "
                   "mejorar en los aspectos posibles.\n"
                   "- Realizar un ejercicio de transparencia sobre la práctica docente de cara al resto de "
                   "la comunidad escolar."),
             texto("n_que", "Qué se evalúa",
                   "Aspectos de la programación de aula y de la práctica docente que se evalúan "
                   "(los indicadores concretos van en las dos tablas del final).",
                   rotulo="Qué se evalúa"),
             texto("n_tecnicas", "Técnicas e instrumentos", "",
                   "- El análisis de la programación de aula.\n"
                   "- La observación.\n"
                   "- Grupos de discusión, en el seno de los órganos de coordinación docente.\n"
                   "- Cuestionarios, bajo la modalidad de autoinforme.\n"
                   "- Diario del profesor, a partir de la reflexión sobre la propia acción educativa.",
                   rotulo="Técnicas e instrumentos"),
             texto("n_momentos", "Momentos", "",
                   "La evaluación será continua, ya que los procesos de enseñanza y la práctica docente "
                   "están en permanente revisión, actualización y mejora. El parámetro temporal de "
                   "referencia será la unidad temporal de programación.",
                   rotulo="Momentos"),
             texto("n_agentes", "Agentes evaluadores", "",
                   "El profesorado, que realizará una autoevaluación sobre la programación de aula que ha "
                   "diseñado y sobre su propia acción docente.",
                   rotulo="Agentes evaluadores"),
             tabla("n_ind_aula", "Indicadores de logro: programación de aula",
                   [("Indicador de logro", 8.0, True)],
                   "En el Word se añaden las columnas de valoración y observaciones, vacías.",
                   filas=[[t] for t in _IND_AULA],
                   columnas_word=["Valoración (de 1 a 5)", "Observaciones y propuestas de mejora"],
                   rotulo="Evaluación de la programación de aula"),
             tabla("n_ind_practica", "Indicadores: práctica docente",
                   [("Ámbito", 2.6, False), ("Indicador", 5.4, True)],
                   "En el Word se añaden las columnas de valoración y observaciones, vacías.",
                   filas=[[a, t] for a, t in _IND_PRACTICA],
                   columnas_word=["Valoración (de 1 a 5)", "Observaciones y propuestas de mejora"],
                   rotulo="Evaluación de la práctica docente"),
         ]),

    _cap("nn", "ñ · Evaluación de la programación",
         "Procedimiento para la evaluación de la programación didáctica",
         "Procedimiento para evaluar la propia programación didáctica: qué evaluar (indicadores de "
         "logro), cómo (instrumentos), cuándo (momentos) y quién (personas). Las conclusiones se "
         "incorporan a la memoria de final de curso.",
         [
             texto("nn_intro", "Introducción", "",
                   "La programación didáctica se evaluará según el procedimiento establecido en este "
                   "apartado. Las conclusiones más importantes se incorporarán al final de curso, junto a "
                   "la evaluación de la propuesta curricular, a la memoria de la programación general "
                   "anual, y serán la base para la elaboración de las programaciones didácticas del curso "
                   "siguiente.\n"
                   "La evaluación y el seguimiento de la programación serán permanentes y continuos, y "
                   "permitirán introducir correcciones o modificaciones. Distintas circunstancias podrán "
                   "motivar ajustes: la evolución del grupo, la incorporación de nuevo alumnado o "
                   "acontecimientos que afecten al centro o a las familias."),
             texto("nn_que", "¿Qué evaluar? Indicadores de logro", "",
                   "Indicadores de logro relativos a la elaboración de la programación didáctica, su "
                   "contenido, la adecuación de sus elementos a la práctica, el grado de cumplimiento de "
                   "lo establecido en ella y su revisión.",
                   rotulo="Qué evaluar"),
             texto("nn_como", "¿Cómo evaluar? Instrumentos", "",
                   "Análisis de la programación, de los resultados académicos del alumnado y de las actas "
                   "del departamento, y cuestionarios de autoevaluación.",
                   rotulo="Cómo evaluar"),
             texto("nn_cuando", "¿Cuándo evaluar? Momentos", "",
                   "De forma continua a lo largo del curso, en las reuniones de departamento; tras cada "
                   "sesión de evaluación y, de forma global, al final del curso.",
                   rotulo="Cuándo evaluar"),
             texto("nn_quien", "¿Quién evalúa?", "",
                   "El profesorado que imparte la materia y el departamento didáctico, bajo la "
                   "coordinación de la jefatura de departamento.",
                   rotulo="Quién evalúa"),
         ]),

    _cap("anexos", "Anexos", "Anexos",
         "Anexos que se generan solos con el currículo de la materia. Los apartados n) y ñ) van "
         "también como anexos (IV y V), como en la programación entregada.",
         [
             texto("anexo1_intro", "Anexo I · Introducción", "",
                   "Para poder vincular más adecuadamente los contenidos a los indicadores de logro de "
                   "cada criterio de evaluación, se han subdividido y codificado los contenidos de "
                   "{la_materia} recogidos en el anexo III del {norma}.", cuerpo="anexo_1"),
             auto("anexo_contenidos", "Anexo I · Tabla de contenidos de la materia",
                  "Código y contenido, agrupados por bloque. De la base de contenidos del programa.",
                  cuerpo="anexo_1"),
             texto("anexo2_intro", "Anexo II · Introducción", "",
                   "Los contenidos de carácter transversal que se trabajan en {la_materia}, determinados "
                   "en el {decreto}, quedan codificados de la siguiente forma:", cuerpo="anexo_2"),
             auto("anexo_transversales", "Anexo II · Tabla de contenidos transversales",
                  "Código y contenido transversal de la etapa.", cuerpo="anexo_2"),
             auto("anexo_criterios", "Anexo III · Competencias específicas y criterios de evaluación",
                  "Cada competencia específica con sus criterios y los descriptores de cada uno.",
                  cuerpo="anexo_3"),
             auto("anexo_mapa_criterial", "Anexo III · Mapa de relaciones criteriales",
                  "Criterio de evaluación × descriptores operativos.",
                  rotulo="Mapa de relaciones criteriales", cuerpo="anexo_3"),
         ]),
]

# Cuerpos del Word: uno por capítulo (salvo la portada, que son datos sueltos)
# y uno por anexo generado.
CUERPOS = [c["id"] for c in CAPITULOS if c["id"] not in ("portada", "anexos")] + [
    "anexo_1", "anexo_2", "anexo_3"
]


# ---------------------------------------------------------------------------
# Elementos de una materia y valores iniciales
# ---------------------------------------------------------------------------
_NORMAS = {
    "ESO": {
        "rd": "Real Decreto 217/2022, de 29 de marzo",
        "decreto": "Decreto 39/2022, de 29 de septiembre",
        "orden_ev": "Orden EDU/424/2024, de 9 de mayo",
    },
    "BACH": {
        "rd": "Real Decreto 243/2022, de 5 de abril",
        "decreto": "Decreto 40/2022, de 29 de septiembre",
        "orden_ev": "Orden EDU/425/2024, de 9 de mayo",
    },
}
_ORDEN_DIVER = "Orden EDU/1332/2023, de 14 de noviembre"


def etapa_app(materia: dict) -> str:
    return materia.get("etapa_app") or materia.get("etapa") or "ESO"


def marcas(materia: dict) -> dict[str, str]:
    """Valores de las marcas ``{…}`` de los textos propuestos para una materia."""
    et = etapa_app(materia)
    n = _NORMAS["BACH" if et == "BACH" else "ESO"]
    diver = et == "DIVER"
    return {
        "materia": materia.get("nombre", ""),
        "curso": f"{materia.get('curso', '')}º",
        "la_materia": "el ámbito" if diver else "la materia",
        "de_la_materia": "del ámbito" if diver else "de la materia",
        "rd": n["rd"],
        "decreto": n["decreto"],
        "orden_ev": n["orden_ev"],
        "norma": _ORDEN_DIVER if diver else n["decreto"],
    }


def _sustituir(txt: str, m: dict[str, str]) -> str:
    return re.sub(r"\{(\w+)\}", lambda k: m.get(k.group(1), k.group(0)), txt)


def elementos(cap: dict, etapa: str) -> list[dict]:
    """Elementos de un capítulo que tocan en esa etapa."""
    return [e for e in cap["elementos"] if not e.get("etapas") or etapa in e["etapas"]]


def todos(etapa: str | None = None) -> list[tuple[dict, dict]]:
    """[(capítulo, elemento)] de toda la redacción."""
    return [
        (c, e) for c in CAPITULOS for e in c["elementos"]
        if etapa is None or not e.get("etapas") or etapa in e["etapas"]
    ]


def filas_dicts(elem: dict, filas: list[list[str]]) -> list[dict[str, str]]:
    nombres = [c[0] for c in elem["columnas"]]
    return [dict(zip(nombres, f)) for f in filas]


def valores_iniciales(materia: dict) -> dict:
    """Redacción de un proyecto que aún no tiene nada escrito: los textos
    propuestos (con sus marcas ya sustituidas), las filas propuestas de las
    tablas y qué tablas y gráficas automáticas aparecen."""
    m = marcas(materia)
    et = etapa_app(materia)
    out: dict[str, dict] = {"textos": {}, "tablas": {}, "opciones": {}}
    for _c, e in todos():
        if e["tipo"] == "texto":
            out["textos"][e["clave"]] = _sustituir(e["defecto"], m)
        elif e["tipo"] == "tabla":
            pone = not e.get("etapas_filas") or et in e["etapas_filas"]
            out["tablas"][e["clave"]] = filas_dicts(e, e["filas"]) if pone else []
        else:
            out["opciones"][e["clave"]] = bool(e["activo"])
    return out


def completar(redaccion: dict | None, materia: dict) -> dict:
    """Lo guardado en el proyecto sobre los valores iniciales: lo que el
    docente ya ha tocado manda (aunque lo haya dejado vacío); lo demás, lo
    propuesto."""
    out = valores_iniciales(materia)
    for parte in ("textos", "tablas", "opciones"):
        out[parte].update((redaccion or {}).get(parte, {}))
    return out


def fila_vacia(elem: dict) -> dict[str, str]:
    return {c[0]: "" for c in elem["columnas"]}


def tabla_con_datos(filas: list[dict]) -> list[dict]:
    """Filas con algo escrito."""
    return [f for f in filas if any(str(v or "").strip() for v in f.values())]


def filas_utiles(elem: dict, filas: list[dict]) -> list[dict]:
    """Filas que van al Word. Si la tabla tiene columnas de texto largo
    (planes del centro, agrupamientos…), una fila propuesta en la que solo
    está el nombre y falta ese texto todavía no cuenta."""
    largas = [c[0] for c in elem["columnas"] if c[2]]
    if not largas:
        return tabla_con_datos(filas)
    return [f for f in filas if any(str(f.get(c, "") or "").strip() for c in largas)]


def pendientes(redaccion: dict, etapa: str) -> list[tuple[str, str]]:
    """[(pestaña, etiqueta)] de los textos que siguen vacíos (para avisar)."""
    return [
        (c["pestana"], e["etiqueta"]) for c, e in todos(etapa)
        if e["tipo"] == "texto" and not str(redaccion["textos"].get(e["clave"], "")).strip()
    ]


# ---------------------------------------------------------------------------
# Lo que se genera solo
# ---------------------------------------------------------------------------
def _s(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _pct(v: float) -> str:
    return f"{v * 100:.2f}".replace(".", ",") + " %"


def _tokens(v: Any) -> list[str]:
    return [t for t in re.split(r"[,;\s]+", _s(v)) if t]


def _num_sa(v: Any):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def preparar(*, cur: dict, sits: list[dict], il_rows: list[dict], ce_p: dict[str, float]) -> dict:
    """Reúne lo que necesitan las tablas y gráficas automáticas.

    ``cur``: lo que devuelve ``curriculo.cargar_materia``. ``sits``: filas de
    la tabla de situaciones (en su orden). ``il_rows``: indicadores ya
    recalculados (con IL y PIL%)."""
    from tools.info_familias import pesos_il

    total_p = sum(float(v or 0) for v in ce_p.values())
    return {
        "cur": cur,
        "sits": [s for s in sits if _num_sa(s.get("SA")) is not None],
        "il_rows": il_rows,
        "ce_p": ce_p,
        "pct_ce": {ce: (float(ce_p.get(ce, 0) or 0) / total_p if total_p else 0.0)
                   for ce in cur["ce_list"]},
        "w_il": pesos_il(il_rows, ce_p),
    }


def _descriptores(d: dict) -> list[str]:
    return [x["cod"] for x in d["cur"]["elementos"].get("descriptores", [])]


def _orden_sa(d: dict) -> list[dict]:
    """Situaciones por evaluación y, dentro, en el orden de su tabla."""
    return sorted(d["sits"], key=lambda s: _num_sa(s.get("EV")) or 9)


def _t_competencias(d):
    cur = d["cur"]
    return (["Nº", "Competencia específica", "Descriptores del Perfil de salida"],
            [[n, txt, cur["comp_descriptores"].get(n, "")] for n, txt in cur["competencias"].items()])


def _matriz(filas: list[tuple[str, set[str]]], cols: list[str], cabecera: str):
    return ([cabecera] + cols, [[n] + ["X" if c in marc else "" for c in cols] for n, marc in filas])


def _t_mapa(d):
    cur = d["cur"]
    filas = [(f"CE{n}", set(_tokens(cur["comp_descriptores"].get(n, "")))) for n in cur["competencias"]]
    return _matriz(filas, _descriptores(d), "CE")


def _t_mapa_criterial(d):
    cur = d["cur"]
    return _matriz([(ce, set(cur["ce_do"].get(ce, []))) for ce in cur["ce_list"]],
                   _descriptores(d), "Criterio")


def _t_resumen(d):
    from tools.indicadores_logro import resumen_por_ce

    cur = d["cur"]
    ae: dict[str, list[str]] = {}
    for r in d["il_rows"]:
        a = _s(r.get("AE"))
        if a and a not in ae.setdefault(_s(r.get("CE")), []):
            ae[_s(r.get("CE"))].append(a)
    filas = [
        [r["CE"], _pct(r["pct"]), r["CONTENIDOS"], r["CT"], "/".join(ae.get(r["CE"], [])), r["SA"]]
        for r in resumen_por_ce(d["il_rows"], cur["ce_list"], cur["ce_ced"], d["ce_p"])
    ]
    return ["CE", "%CE", "Contenidos", "CT", "AE", "SA"], filas


def _t_indicadores(d):
    filas = []
    for ce in d["cur"]["ce_list"]:
        for r in (r for r in d["il_rows"] if _s(r.get("CE")) == ce):
            filas.append([ce, _s(r.get("IL")), _s(r.get("DIL")),
                          ", ".join(_tokens(r.get("CON"))), ", ".join(_tokens(r.get("CT")))])
    return ["CE", "IL", "Indicador de logro", "Contenidos", "CT"], filas


def _t_transversales_sa(d):
    usados: dict[str, list[int]] = {}
    for r in d["il_rows"]:
        n = _num_sa(r.get("SA"))
        for t in _tokens(r.get("CT")):
            if n is not None and n not in usados.setdefault(t, []):
                usados[t].append(n)
    return (["Código", "Contenido transversal", "SA"],
            [[t["num"], t["desc"], ", ".join(str(n) for n in sorted(usados.get(t["num"], []))) or "—"]
             for t in d["cur"]["elementos"].get("transversales", [])])


def _instrumentos(d) -> list[tuple[str, float]]:
    por: dict[str, float] = {}
    for r in d["il_rows"]:
        ie = _s(r.get("IE"))
        if ie:
            por[ie] = por.get(ie, 0.0) + d["w_il"].get(_s(r.get("IL")), 0.0)
    return sorted(por.items(), key=lambda kv: -kv[1])


def _t_instrumentos(d):
    ins = _instrumentos(d)
    filas = [[k, _pct(v)] for k, v in ins]
    if filas:
        filas.append(["Total", _pct(sum(v for _k, v in ins))])
    return ["Instrumento de evaluación", "% acumulado"], filas


def _t_detalle(d):
    filas = []
    for ce in d["cur"]["ce_list"]:
        for r in (r for r in d["il_rows"] if _s(r.get("CE")) == ce):
            n = _num_sa(r.get("SA"))
            filas.append([ce, _s(r.get("IL")), _s(r.get("IE")), _s(r.get("AE")),
                          "" if n is None else str(n)])
    return ["CE", "IL", "Instrumento de evaluación", "Agente evaluador", "SA"], filas


def _t_pesos_sa(d):
    por: dict[int, float] = {}
    for r in d["il_rows"]:
        n = _num_sa(r.get("SA"))
        if n is not None:
            por[n] = por.get(n, 0.0) + d["w_il"].get(_s(r.get("IL")), 0.0)
    filas = [[str(_num_sa(s["SA"])), _s(s.get("DSA")), _pct(por.get(_num_sa(s["SA"]), 0.0))]
             for s in _orden_sa(d)]
    if filas:
        filas.append(["Total", "", _pct(sum(por.values()))])
    return ["SA", "Situación de aprendizaje", "Peso"], filas


def _horas(s) -> float:
    try:
        return float(s.get("HSA") or 0)
    except (TypeError, ValueError):
        return 0.0


def _t_secuencia(d):
    total = sum(_horas(s) for s in d["sits"])
    filas = [
        [str(_num_sa(s["SA"])), _s(s.get("DSA")), _s(_num_sa(s.get("EV")) or ""),
         f"{_horas(s):g}", _pct(_horas(s) / total if total else 0.0)]
        for s in _orden_sa(d)
    ]
    if filas:
        filas.append(["Total", "", "", f"{total:g}", _pct(1.0 if total else 0.0)])
    return ["SA", "Situación de aprendizaje", "Ev.", "Horas", "% sobre el total"], filas


def _t_contenidos(d):
    """Las filas con el código vacío son el nombre del bloque (el Word las
    pinta como banda)."""
    filas, bloque = [], None
    for c in d["cur"]["elementos"].get("contenidos", []):
        if c.get("bloque") and c["bloque"] != bloque:
            bloque = c["bloque"]
            filas.append(["", bloque])
        filas.append([c["cod"], c.get("desc", "")])
    return ["Código", "Contenido"], filas


def _t_transversales(d):
    return (["Código", "Contenido transversal"],
            [[t["num"], t["desc"]] for t in d["cur"]["elementos"].get("transversales", [])])


def _t_criterios(d):
    cur = d["cur"]
    filas = []
    for n, txt in cur["competencias"].items():
        filas.append(["", f"Competencia específica {n}. {txt}"])
        for ce in cur["ce_list"]:
            if str(cur["ce_comp"].get(ce)) == str(n):
                do = ", ".join(cur["ce_do"].get(ce, []))
                filas.append([ce, cur["ce_ced"].get(ce, "") + (f" ({do})" if do else "")])
    return ["CE", "Criterio de evaluación"], filas


_TABLAS: dict[str, Callable[[dict], tuple[list[str], list[list[str]]]]] = {
    "c_competencias": _t_competencias,
    "c_mapa": _t_mapa,
    "d_resumen": _t_resumen,
    "d_indicadores": _t_indicadores,
    "e_tabla": _t_transversales_sa,
    "k_instrumentos": _t_instrumentos,
    "k_detalle": _t_detalle,
    "k_pesos_sa": _t_pesos_sa,
    "m_secuencia": _t_secuencia,
    "anexo_contenidos": _t_contenidos,
    "anexo_transversales": _t_transversales,
    "anexo_criterios": _t_criterios,
    "anexo_mapa_criterial": _t_mapa_criterial,
}


def tabla_auto(clave: str, datos: dict) -> tuple[list[str], list[list[str]]]:
    """(cabeceras, filas) de una tabla automática. ``datos`` = ``preparar(...)``."""
    return _TABLAS[clave](datos)


def grafica_png(clave: str, datos: dict, *, grises: bool = True) -> bytes | None:
    """PNG de una gráfica automática (None si aún no hay datos). Por defecto en
    blanco y negro, como el resto del documento."""
    from tools.situaciones_informe import build_pie_png_simple

    if clave == "k_grafica_instrumentos":
        ins = _instrumentos(datos)
        if not ins:
            return None
        return build_pie_png_simple([k for k, _v in ins], [v for _k, v in ins],
                                    titulo="Peso por instrumento de evaluación",
                                    leyenda="Instrumento", grises=grises)
    if clave == "m_grafica_horas":
        sits = [s for s in _orden_sa(datos) if _horas(s)]
        if not sits:
            return None
        return build_pie_png_simple(
            [f"SA {_num_sa(s['SA'])}: {_s(s.get('DSA'))}" for s in sits], [_horas(s) for s in sits],
            titulo="Reparto de horas por situación de aprendizaje", leyenda="Situación",
            grises=grises,
        )
    raise KeyError(clave)
