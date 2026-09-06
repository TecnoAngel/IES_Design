"""Calendario escolar oficial de Castilla y León + cálculo exacto de días
lectivos y sesiones por evaluación.

La parte de descarga/parseo del calendario JCyL es la misma que en IES_Creator
(`tools/sessions_calculator.py`). Aquí, en vez de estimar sesiones por
"semanas netas × horas semanales × factor de seguridad", se cuenta día a día:
el profesor indica cuántas sesiones de su materia tiene cada día de la semana
(normalmente 0, 1 o 2) y se recorren todas las fechas de cada trimestre
descontando festivos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

DEFAULT_CALENDAR_URL = "https://www.educa.jcyl.es/es/informacion/calendario-escolar-2026-2027"

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]

_MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11,
    "diciembre": 12,
}

_SECUNDARIA_RE = re.compile(r"-\s*educaci[oó]n secundaria obligatoria\b", re.IGNORECASE)
_NAVIDAD_RE = re.compile(r"vacaciones de navidad", re.IGNORECASE)
_SEMANA_SANTA_RE = re.compile(r"vacaciones de semana santa", re.IGNORECASE)
_YEAR_IN_REF_RE = re.compile(r"_(\d{4})_")


@dataclass
class HolidayGroup:
    """Un festivo/día no lectivo con nombre propio (puede abarcar varios días)."""

    name: str
    category: str
    days: set[date] = field(default_factory=set)

    @property
    def start(self) -> date:
        return min(self.days)

    @property
    def end(self) -> date:
        return max(self.days)


@dataclass
class SchoolCalendar:
    course_start: date
    course_end: date
    christmas_days: set[date] = field(default_factory=set)
    easter_days: set[date] = field(default_factory=set)
    other_holidays: list[HolidayGroup] = field(default_factory=list)
    source_url: str = ""

    @property
    def holiday_days(self) -> set[date]:
        return self.christmas_days | self.easter_days


@dataclass
class _GridEvent:
    day: date
    event_type: str
    title: str


def _parse_grid_events(soup: BeautifulSoup) -> list[_GridEvent]:
    """Recorre la rejilla mensual del calendario (tablas <table class="month">)."""
    events: list[_GridEvent] = []
    for month_table in soup.select("table.month"):
        caption = month_table.find("caption")
        if caption is None:
            continue
        month_num = _MESES.get(caption.get_text(strip=True).lower())
        if month_num is None:
            continue

        for td in month_table.select("td.calendarCustomFestiveCell"):
            classes = td.get("class") or []
            event_type = next(
                (c[len("eventType"):] for c in classes if c.startswith("eventType")), None
            )
            if event_type is None:
                continue

            title = (td.get("title") or "").strip()
            anchor = td.find("a")
            day_text = anchor.get_text(strip=True) if anchor is not None else td.get_text(strip=True)
            try:
                day_num = int(day_text)
            except ValueError:
                continue

            year = None
            if anchor is not None:
                ref = anchor.get("href") or anchor.get("name") or ""
                match = _YEAR_IN_REF_RE.search(ref)
                if match:
                    year = int(match.group(1))
            if year is None:
                continue

            try:
                day = date(year, month_num, day_num)
            except ValueError:
                continue

            events.append(_GridEvent(day=day, event_type=event_type, title=title))

    return events


def _parse_calendar_html(html: str, source_url: str) -> SchoolCalendar:
    soup = BeautifulSoup(html, "html.parser")
    events = _parse_grid_events(soup)
    if not events:
        raise ValueError(
            "No se han encontrado eventos en el calendario. Puede que haya cambiado su estructura."
        )

    course_start = None
    course_end = None
    christmas_days: set[date] = set()
    easter_days: set[date] = set()
    holiday_groups: dict[str, HolidayGroup] = {}

    for ev in events:
        event_type = ev.event_type.lower()
        if event_type.startswith("iniciodecurso"):
            if course_start is None and _SECUNDARIA_RE.search(ev.title):
                course_start = ev.day
        elif event_type.startswith("findecurso"):
            if course_end is None and _SECUNDARIA_RE.search(ev.title):
                course_end = ev.day
        elif event_type == "vacacionesescolares":
            if _NAVIDAD_RE.search(ev.title):
                christmas_days.add(ev.day)
            elif _SEMANA_SANTA_RE.search(ev.title):
                easter_days.add(ev.day)
        elif event_type in ("fiestaslaborales", "diasnolectivos"):
            group = holiday_groups.setdefault(
                ev.title, HolidayGroup(name=ev.title, category=ev.event_type)
            )
            group.days.add(ev.day)

    if course_start is None or course_end is None:
        raise ValueError(
            "No se han podido localizar las fechas de inicio/fin de curso de Educación "
            "Secundaria Obligatoria en la página. Puede que haya cambiado su estructura."
        )

    other_holidays = sorted(holiday_groups.values(), key=lambda g: min(g.days))

    return SchoolCalendar(
        course_start=course_start,
        course_end=course_end,
        christmas_days=christmas_days,
        easter_days=easter_days,
        other_holidays=other_holidays,
        source_url=source_url,
    )


def fetch_school_calendar(url: str = DEFAULT_CALENDAR_URL) -> SchoolCalendar:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    response.raise_for_status()
    return _parse_calendar_html(response.text, url)


def default_trimester_ranges(
    calendar: SchoolCalendar,
) -> tuple[tuple[date, date], tuple[date, date], tuple[date, date]]:
    """Propone una división en 3 trimestres en torno a Navidad y Semana Santa."""
    christmas_start = min(calendar.christmas_days) if calendar.christmas_days else None
    christmas_end = max(calendar.christmas_days) if calendar.christmas_days else None
    easter_start = min(calendar.easter_days) if calendar.easter_days else None
    easter_end = max(calendar.easter_days) if calendar.easter_days else None

    t1_end = (christmas_start - timedelta(days=1)) if christmas_start else calendar.course_start
    t2_start = (christmas_end + timedelta(days=1)) if christmas_end else calendar.course_start
    t2_end = (easter_start - timedelta(days=1)) if easter_start else calendar.course_end
    t3_start = (easter_end + timedelta(days=1)) if easter_end else calendar.course_end

    return (
        (calendar.course_start, t1_end),
        (t2_start, t2_end),
        (t3_start, calendar.course_end),
    )


def trimester_index_for_date(day: date, trimester_ranges: list[tuple[date, date]]) -> int | None:
    for i, (start, end) in enumerate(trimester_ranges):
        if start <= day <= end:
            return i
    return None


@dataclass
class ConteoEvaluacion:
    dias_lectivos: int          # días de L-V dentro del rango que no son festivos
    dias_con_clase: int         # de esos, los que tienen alguna sesión de la materia
    sesiones: int               # nº total de sesiones de la materia
    festivos_restados: int      # días de L-V del rango que caían en festivo
    sesiones_ajustadas: int = 0  # sesiones tras aplicar el margen de seguridad


def contar_evaluacion(
    start: date,
    end: date,
    sesiones_por_dia: dict[int, int],
    holiday_days: set[date],
    margen_seguridad: float = 0.0,
) -> ConteoEvaluacion:
    """Recorre día a día ``start``…``end`` (ambos incluidos).

    ``sesiones_por_dia``: ``{0: nº lunes, 1: nº martes, … 4: nº viernes}``.
    ``holiday_days``: fechas no lectivas (Navidad, Semana Santa, festivos
    autonómicos/locales marcados).
    ``margen_seguridad``: fracción (0–1) de sesiones que se prevé perder
    (excursiones, actividades, imprevistos); ``sesiones_ajustadas`` =
    ``round(sesiones · (1 − margen_seguridad))``.
    """
    if end < start:
        return ConteoEvaluacion(0, 0, 0, 0, 0)

    dias_lectivos = 0
    dias_con_clase = 0
    sesiones = 0
    festivos = 0
    d = start
    paso = timedelta(days=1)
    while d <= end:
        if d.weekday() < 5:  # L-V
            if d in holiday_days:
                festivos += 1
            else:
                dias_lectivos += 1
                n = int(sesiones_por_dia.get(d.weekday(), 0) or 0)
                if n > 0:
                    dias_con_clase += 1
                    sesiones += n
        d += paso
    ajustadas = round(sesiones * (1 - max(0.0, min(margen_seguridad, 1.0))))
    return ConteoEvaluacion(dias_lectivos, dias_con_clase, sesiones, festivos, ajustadas)
