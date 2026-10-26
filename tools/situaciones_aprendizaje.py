"""Situaciones de aprendizaje: estructura y cálculos.

Cada SA tiene ``SA`` (nº), ``EV`` (evaluación/trimestre 1-3), ``DSA``
(descripción/título) y ``HSA`` (horas). Se guardan en el proyecto
(``proyecto.guardar_proyecto``, tabla ``situaciones``) junto con las horas
previstas por trimestre, las fechas de cada evaluación, las horas por día de la
semana y el festivo local (tabla ``config``).
"""

from __future__ import annotations

from dataclasses import dataclass

TRIMESTRES = (1, 2, 3)


@dataclass
class Situacion:
    sa: int | None
    ev: int | None
    dsa: str
    hsa: float | None


def acumulado_por_trimestre(situaciones: list[Situacion]) -> dict[int, float]:
    acc = {tri: 0.0 for tri in TRIMESTRES}
    for s in situaciones:
        if s.ev in TRIMESTRES and s.hsa:
            acc[int(s.ev)] += float(s.hsa)
    return acc
