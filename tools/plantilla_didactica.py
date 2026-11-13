"""Construye la plantilla Word (docxtpl) por defecto de la programación
didáctica: ``templates/programacion_didactica_template.docx``.

Lleva la portada y el título de cada capítulo (los de la guía de la Junta,
a–m, y los anexos I–V, como en la programación entregada); el cuerpo de cada
uno lo rellena ``tools/programacion_didactica.py`` en su etiqueta
``{{p cap_… }}``.

Se puede retocar luego a mano en Word (estilos, cabecera del centro, orden de
los capítulos…) siempre que se respeten las etiquetas ``{{ … }}`` /
``{%p … %}``. Para regenerarla:

    .venv\\Scripts\\python.exe -m tools.plantilla_didactica
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from tools.redaccion import CAPITULOS

ROJO = RGBColor(0xA6, 0x18, 0x2E)
TINTA = RGBColor(0x22, 0x1C, 0x18)

# Capítulos que van en el cuerpo (los demás, como anexos).
EN_CUERPO = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m"]
LETRA = {"nn": "ñ"}


def _estilos(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.font.color.rgb = TINTA
    normal.paragraph_format.space_after = Pt(6)
    for nombre, tam in (("Title", 26), ("Heading 1", 14), ("Heading 2", 12)):
        st = doc.styles[nombre]
        st.font.name = "Calibri"
        st.font.size = Pt(tam)
        st.font.bold = True
        st.font.color.rgb = ROJO
        st.paragraph_format.keep_with_next = True
    doc.styles["Heading 1"].paragraph_format.space_before = Pt(18)
    doc.styles["Heading 1"].paragraph_format.space_after = Pt(8)
    for sec in doc.sections:
        sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
        sec.left_margin = sec.right_margin = Cm(2.0)
        sec.top_margin = sec.bottom_margin = Cm(2.0)


def _p(doc: Document, texto: str = "", *, bold: bool = False, center: bool = False,
       size: float | None = None, color: RGBColor | None = None, antes: float = 0):
    p = doc.add_paragraph()
    if antes:
        p.paragraph_format.space_before = Pt(antes)
    if texto:
        r = p.add_run(texto)
        r.bold = bold
        if size:
            r.font.size = Pt(size)
        if color is not None:
            r.font.color.rgb = color
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def _numero_de_pagina(doc: Document) -> None:
    p = doc.sections[0].footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    campo = OxmlElement("w:fldSimple")
    campo.set(qn("w:instr"), "PAGE")
    p._p.append(campo)


def build_document() -> Document:
    doc = Document()
    _estilos(doc)
    _numero_de_pagina(doc)

    # ── Portada
    _p(doc, antes=120)
    t = doc.add_paragraph("PROGRAMACIÓN DIDÁCTICA", style="Title")
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _p(doc, "{{ materia }}", bold=True, center=True, size=20, color=TINTA, antes=12)
    _p(doc, "{{ curso }}", bold=True, center=True, size=16)
    # (cada dato de la portada solo sale si está relleno)
    for dato, texto, tam, antes in (
        ("curso_academico", "Curso {{ curso_academico }}", 14, 24),
        ("centro", "{{ centro }}", 13, 60),
        ("departamento", "Departamento: {{ departamento }}", 12, 0),
        ("profesorado", "Profesorado: {{ profesorado }}", 12, 0),
    ):
        _p(doc, f"{{%p if {dato} %}}")
        _p(doc, texto, center=True, size=tam, antes=antes)
        _p(doc, "{%p endif %}")

    # ── Capítulos a) … m)
    por_id = {c["id"]: c for c in CAPITULOS}
    primero = True
    for cid in EN_CUERPO:
        cap = por_id[cid]
        h = doc.add_heading(f"{LETRA.get(cid, cid)}) {cap['titulo']}.", level=1)
        if primero:
            h.paragraph_format.page_break_before = True
            primero = False
        _p(doc, f"{{{{p cap_{cid} }}}}")

    # ── Anexos
    def anexo(titulo: str, cuerpo: str, condicion: str | None = None) -> None:
        if condicion:
            _p(doc, f"{{%p if {condicion} %}}")
        h = doc.add_heading(titulo, level=1)
        h.paragraph_format.page_break_before = True
        _p(doc, f"{{{{p cap_{cuerpo} }}}}")
        if condicion:
            _p(doc, "{%p endif %}")

    anexo("ANEXO I. Contenidos de {{ materia }} · {{ curso }}", "anexo_1", "hay_anexo_1")
    anexo("ANEXO II. Contenidos de carácter transversal", "anexo_2", "hay_anexo_2")
    anexo("ANEXO III. Competencias específicas y criterios de evaluación de {{ materia }} · "
          "{{ curso }}", "anexo_3", "hay_anexo_3")
    anexo(f"ANEXO IV. {por_id['n']['titulo']}", "n")
    anexo(f"ANEXO V. {por_id['nn']['titulo']}", "nn")
    return doc


def build_template_bytes() -> bytes:
    buf = BytesIO()
    build_document().save(buf)
    return buf.getvalue()


if __name__ == "__main__":
    destino = (
        Path(__file__).resolve().parent.parent / "templates" / "programacion_didactica_template.docx"
    )
    destino.write_bytes(build_template_bytes())
    print(f"Plantilla escrita en {destino}")
