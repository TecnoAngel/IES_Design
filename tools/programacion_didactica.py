"""Word de la programación didáctica (docxtpl + python-docx).

La plantilla (``templates/programacion_didactica_template.docx`` o la que suba
el docente) lleva la portada y los títulos de los capítulos; aquí se rellena
el cuerpo de cada uno. Etiquetas de la plantilla:

- Portada: ``{{ materia }}``, ``{{ curso }}``, ``{{ curso_academico }}``,
  ``{{ centro }}``, ``{{ departamento }}``, ``{{ profesorado }}``.
- Cuerpo de cada capítulo: ``{{p cap_a }}`` … ``{{p cap_m }}``, ``{{p cap_n }}``,
  ``{{p cap_nn }}`` (ñ) y de los anexos generados ``{{p cap_anexo_1 }}``,
  ``{{p cap_anexo_2 }}``, ``{{p cap_anexo_3 }}``.
- ``hay_anexo_1`` … ``hay_anexo_3`` (y ``hay_<capítulo>``): si ese cuerpo
  tiene algo, para poder quitar su título con ``{%p if … %}``.

El cuerpo de un capítulo se construye recorriendo sus elementos (ver
``tools/redaccion.py``): cada texto con algo escrito, cada tabla con filas y
cada tabla o gráfica automática marcada para aparecer.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import jinja2
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docxtpl import DocxTemplate

from tools import redaccion as red
from tools.info_familias import _fijar_anchos, _fila
from tools.programacion_aula import _set_cell_background, _set_table_borders

DEFAULT_TEMPLATE = (
    Path(__file__).resolve().parent.parent / "templates" / "programacion_didactica_template.docx"
)
_JINJA_ENV = jinja2.Environment(undefined=jinja2.ChainableUndefined)

ANCHO_CM = 17.0          # ancho útil de la página (A4 con márgenes de 2 cm)
# Todo en blanco y negro (petición del usuario, 2026-11-14): grises y letra negra.
HEADER_FILL = "D9D9D9"   # fondo de la cabecera de las tablas
BANDA_FILL = "F2F2F2"    # fondo de las filas de bloque / competencia
SIN_COMPLETAR = "(pendiente de completar)"

# Anchos (cm) de las tablas automáticas. Las que no están aquí se reparten a
# partes iguales.
ANCHOS = {
    "d_resumen": [1.1, 1.6, 7.3, 2.2, 1.8, 3.0],
    "d_indicadores": [1.1, 1.4, 8.5, 3.6, 2.4],
    "e_tabla": [1.5, 11.5, 4.0],
    "k_instrumentos": [9.0, 4.0],
    "k_detalle": [1.3, 1.6, 7.0, 3.6, 3.5],
    "k_pesos_sa": [1.5, 11.5, 4.0],
    "m_secuencia": [1.3, 9.2, 1.3, 1.8, 3.4],
    "anexo_contenidos": [1.8, 15.2],
    "anexo_transversales": [1.6, 15.4],
    "anexo_criterios": [1.4, 15.6],
}
MATRICES = {"c_mapa", "anexo_mapa_criterial"}
CENTRADAS = {"CE", "%CE", "IL", "SA", "AE", "CT", "Ev.", "Horas", "% sobre el total", "Peso",
             "% acumulado", "Código"}


def _read_bytes(source: Any) -> bytes:
    if isinstance(source, (bytes, bytearray)):
        return bytes(source)
    if hasattr(source, "getvalue"):
        return source.getvalue()
    if hasattr(source, "read"):
        return source.read()
    return Path(source).read_bytes()


# ---------------------------------------------------------------------------
# Piezas
# ---------------------------------------------------------------------------
def _run(p, texto: str, *, size: float | None = None, bold: bool = False, italic: bool = False,
         color: RGBColor | None = None):
    r = p.add_run(texto)
    r.bold, r.italic = bold or None, italic or None
    if size:
        r.font.size = Pt(size)
    if color is not None:
        r.font.color.rgb = color
    return r


def _rotulo(sub, texto: str) -> None:
    p = sub.add_paragraph()
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(8)
    _run(p, texto.rstrip(":") + ":", bold=True)


def _encabezado_extra(sub, numero: str, texto: str, nivel: int) -> None:
    """Encabezado de un párrafo añadido por el docente: negrita, con su número
    (k.1 · k.1.1); el subapartado, además, en cursiva y algo sangrado."""
    p = sub.add_paragraph()
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(10 if nivel == 1 else 6)
    if nivel == 2:
        p.paragraph_format.left_indent = Cm(0.5)
    _run(p, f"{numero}  {texto.strip()}", bold=True, italic=(nivel == 2))


def _parrafos(sub, texto: str) -> None:
    """Un párrafo por línea; las líneas que empiezan por «- », «• » o «– »
    salen como lista (sin depender de los estilos de lista de la plantilla)."""
    for linea in texto.replace("\r", "").split("\n"):
        linea = linea.strip()
        if not linea:
            continue
        p = sub.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if linea[:2] in ("- ", "• ", "– "):
            p.paragraph_format.left_indent = Cm(0.9)
            p.paragraph_format.first_line_indent = Cm(-0.4)
            p.paragraph_format.space_after = Pt(2)
            _run(p, "•  " + linea[2:].strip())
        else:
            _run(p, linea)


def _celda(cell, texto: str, *, size: float, bold: bool = False, center: bool = False,
           color: RGBColor | None = None) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lineas = str(texto or "").replace("\r", "").split("\n")
    for i, linea in enumerate(lineas):
        if i:
            p.add_run().add_break()
        _run(p, linea, size=size, bold=bold, color=color)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def _espacio(sub) -> None:
    p = sub.add_paragraph()
    p.paragraph_format.space_after = Pt(2)


def _tabla(sub, headers: list[str], rows: list[list[str]], widths: list[float] | None = None,
           *, size: float = 8.5, centrar: set[int] | None = None) -> None:
    """Tabla con cabecera carmín. Una fila cuyo primer valor está vacío y solo
    tiene texto en el segundo es una **banda** (nombre de bloque o competencia):
    ocupa todo el ancho. La fila «Total» va en negrita."""
    n = len(headers)
    widths = widths or [ANCHO_CM / n] * n
    centrar = centrar if centrar is not None else {i for i, h in enumerate(headers) if h in CENTRADAS}
    t = sub.add_table(rows=1, cols=n)
    _set_table_borders(t)
    t.autofit = False
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        _celda(c, h.upper(), size=size, bold=True, center=True)
        _set_cell_background(c, HEADER_FILL)
    _fila(t.rows[0], cabecera=True)
    juntas = len(rows) <= 14
    for k, vals in enumerate(rows, 1):
        row = t.add_row()
        cells = row.cells
        banda = n > 1 and not str(vals[0]).strip() and not any(str(v).strip() for v in vals[2:])
        if banda:
            m = cells[0].merge(cells[-1])
            _celda(m, vals[1], size=size, bold=True)
            _set_cell_background(m, BANDA_FILL)
            _fila(row, con_siguiente=True)
            continue
        total = str(vals[0]).strip().lower().startswith("total")
        for i, v in enumerate(vals):
            _celda(cells[i], v, size=size, bold=total, center=i in centrar)
        _fila(row, con_siguiente=juntas and k < len(rows))
    _fijar_anchos(t, widths)
    _espacio(sub)


def _matriz(sub, headers: list[str], rows: list[list[str]]) -> None:
    """Mapa de relaciones (muchas columnas estrechas): cabeceras en vertical y
    letra pequeña para que quepa en una página en vertical."""
    n = len(headers)
    w0 = 1.5
    widths = [w0] + [(ANCHO_CM - w0) / (n - 1)] * (n - 1)
    t = sub.add_table(rows=1, cols=n)
    _set_table_borders(t)
    t.autofit = False
    # Celdas casi sin margen lateral
    mar = OxmlElement("w:tblCellMar")
    for lado in ("left", "right"):
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:w"), "15")
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    t._tbl.tblPr.append(mar)
    cab = t.rows[0]
    alto = OxmlElement("w:trHeight")
    alto.set(qn("w:val"), str(int(1.5 * 567)))
    cab._tr.get_or_add_trPr().append(alto)
    for i, h in enumerate(headers):
        c = cab.cells[i]
        _celda(c, h, size=5.5, bold=True, center=True)
        _set_cell_background(c, HEADER_FILL)
        if i:
            d = OxmlElement("w:textDirection")
            d.set(qn("w:val"), "btLr")
            c._tc.get_or_add_tcPr().append(d)
    _fila(cab, cabecera=True)
    for k, vals in enumerate(rows, 1):
        row = t.add_row()
        cells = row.cells
        for i, v in enumerate(vals):
            _celda(cells[i], v, size=6.5 if i == 0 else 6, bold=i == 0, center=True)
        _fila(row, con_siguiente=k < len(rows))
    _fijar_anchos(t, widths)
    _espacio(sub)


def _competencias(sub, rows: list[list[str]]) -> None:
    """Competencias específicas como texto: «1. …» y debajo sus descriptores."""
    for n, txt, do in rows:
        p = sub.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.keep_with_next = bool(do)
        p.paragraph_format.space_after = Pt(2)
        _run(p, f"{n}. ", bold=True)
        _run(p, txt)
        if do:
            p = sub.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.6)
            _run(p, "Descriptores del Perfil de salida: ", italic=True, size=9.5)
            _run(p, do, size=9.5)


def _imagen(sub, png: bytes, ancho_cm: float = 12.5) -> None:
    sub.add_picture(BytesIO(png), width=Cm(ancho_cm))
    sub.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER


# ---------------------------------------------------------------------------
# Elementos
# ---------------------------------------------------------------------------
def _pon_tabla_docente(sub, elem: dict, filas: list[dict]) -> bool:
    cols = [c[0] for c in elem["columnas"]]
    pesos = [float(c[1]) for c in elem["columnas"]]
    utiles = red.filas_utiles(elem, filas)
    if not utiles:
        return False
    # Fuera las columnas que nadie ha rellenado
    quedan = [i for i, c in enumerate(cols) if any(str(f.get(c, "")).strip() for f in utiles)]
    headers = [cols[i] for i in quedan]
    w = [pesos[i] for i in quedan]
    rows = [[str(f.get(cols[i], "")).strip() for i in quedan] for f in utiles]
    extra = elem.get("columnas_word") or []
    if extra:
        base = sum(w)
        w += [base * 0.27, base * 0.6][: len(extra)] + [base * 0.3] * max(0, len(extra) - 2)
        headers += extra
        rows = [r + [""] * len(extra) for r in rows]
    total = sum(w)
    if elem.get("rotulo"):
        _rotulo(sub, elem["rotulo"])
    _tabla(sub, headers, rows, [ANCHO_CM * x / total for x in w], size=9, centrar=set())
    return True


def _pon_auto(sub, elem: dict, datos: dict) -> bool:
    headers, rows = red.tabla_auto(elem["clave"], datos)
    if not rows:
        return False
    if elem.get("rotulo"):
        _rotulo(sub, elem["rotulo"])
    clave = elem["clave"]
    if clave == "c_competencias":
        _competencias(sub, rows)
    elif clave in MATRICES:
        _matriz(sub, headers, rows)
    else:
        _tabla(sub, headers, rows, ANCHOS.get(clave),
               size=8 if clave in ("d_resumen", "d_indicadores", "anexo_contenidos") else 8.5)
    return True


def _cuerpos(tpl: DocxTemplate, redaccion: dict, datos: dict, etapa: str) -> dict[str, tuple]:
    """{cuerpo: (subdocumento, tiene_algo)}"""
    out = {c: [tpl.new_subdoc(), False] for c in red.CUERPOS}
    for cap, elem in red.todos(etapa):
        cuerpo = elem.get("cuerpo") or cap["id"]
        if cuerpo not in out:
            continue  # portada
        sub = out[cuerpo][0]
        clave, tipo = elem["clave"], elem["tipo"]
        puesto = False
        if tipo == "texto":
            txt = str(redaccion["textos"].get(clave, "")).strip()
            if txt:
                if elem.get("rotulo"):
                    _rotulo(sub, elem["rotulo"])
                _parrafos(sub, txt)
                puesto = True
        elif tipo == "tabla":
            puesto = _pon_tabla_docente(sub, elem, redaccion["tablas"].get(clave, []))
        elif redaccion["opciones"].get(clave):
            if clave == "k_categorias":
                titulo = str(redaccion["textos"].get("k_categorias_titulo", "")).strip()
                puesto = _pon_auto(
                    sub, dict(elem, rotulo=titulo or None),
                    dict(datos, niveles=red.niveles_categorias(redaccion)))
            elif tipo == "auto":
                puesto = _pon_auto(sub, elem, datos)
            else:
                png = red.grafica_png(clave, datos)
                if png:
                    _imagen(sub, png)
                    puesto = True
        out[cuerpo][1] = out[cuerpo][1] or puesto
    # Párrafos que ha añadido el docente, al final de su capítulo. Sin texto no
    # sale nada (tampoco su encabezado).
    for cuerpo, item in out.items():
        sub = item[0]
        lista = red.extras_de(redaccion, cuerpo)
        numeros = red.numerar_extras(lista, cuerpo)
        for e in lista:
            if not red.extra_util(e):
                continue
            if e["id"] in numeros:
                _encabezado_extra(sub, numeros[e["id"]], e["encabezado"], e["nivel"])
            _parrafos(sub, e["texto"])
            item[1] = True
    for cuerpo, (sub, hay) in out.items():
        if not hay:
            _run(sub.add_paragraph(), SIN_COMPLETAR, italic=True)
    return {k: (v[0], v[1]) for k, v in out.items()}


# ---------------------------------------------------------------------------
# Documento
# ---------------------------------------------------------------------------
def plantilla_por_defecto() -> bytes:
    if DEFAULT_TEMPLATE.exists():
        return DEFAULT_TEMPLATE.read_bytes()
    from tools.plantilla_didactica import build_template_bytes

    return build_template_bytes()


def generar_docx(*, materia: dict, redaccion: dict, datos: dict, template_source: Any = None) -> bytes:
    """``redaccion``: {"textos", "tablas", "opciones"} completos (ver
    ``redaccion.completar``). ``datos``: ``redaccion.preparar(...)``."""
    from tools.curriculo import ETAPA_NOMBRE

    tpl_bytes = _read_bytes(template_source) if template_source is not None else plantilla_por_defecto()
    tpl = DocxTemplate(BytesIO(tpl_bytes))
    etapa = red.etapa_app(materia)

    tx = redaccion["textos"]
    ctx: dict[str, Any] = {
        "materia": materia.get("nombre", ""),
        "curso": f"{materia.get('curso', '')}º {ETAPA_NOMBRE.get(etapa, etapa)}",
        "curso_academico": str(tx.get("portada_curso_academico", "")).strip(),
        "centro": str(tx.get("portada_centro", "")).strip(),
        "departamento": str(tx.get("portada_departamento", "")).strip(),
        "profesorado": str(tx.get("portada_profesorado", "")).strip(),
    }
    for cuerpo, (sub, hay) in _cuerpos(tpl, redaccion, datos, etapa).items():
        ctx[f"cap_{cuerpo}"] = sub
        ctx[f"hay_{cuerpo}"] = hay

    tpl.render(ctx, jinja_env=_JINJA_ENV)
    out = BytesIO()
    tpl.save(out)
    return out.getvalue()
