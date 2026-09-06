"""Panel de reparto de horas por situación de aprendizaje.

Reproduce en Streamlit lo que en el Excel es la tabla dinámica + gráfico de
sectores de la hoja INFORMES ("DISTRIBUCIÓN DE CARGA TEMPORAL POR SITUACIONES DE
APRENDIZAJE"): el porcentaje de horas de cada SA sobre el total (``HSA`` /
``SUM(HSA)``), un gráfico de tarta, y botones para copiar tabla y gráfico y
pegarlos en Word.
"""

from __future__ import annotations

import base64
import html as html_lib
import json
from io import BytesIO

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from tools.situaciones_aprendizaje import Situacion

# Paleta estable (misma para tabla, leyenda y tarta).
_CMAP = plt.get_cmap("tab20")


def _color_hex(i: int) -> str:
    r, g, b, _ = _CMAP(i % 20)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def hsa_share(situaciones: list[Situacion]) -> list[dict]:
    """Devuelve, por cada SA con horas > 0, su nº, descripción, evaluación,
    horas y porcentaje sobre el total de horas. Se respeta el orden en que
    están en la tabla (el orden en que las metió el profesor)."""
    filas = [
        s
        for s in situaciones
        if s.hsa not in (None, "", 0) and float(s.hsa) > 0
    ]
    total = sum(float(s.hsa) for s in filas)

    out: list[dict] = []
    for i, s in enumerate(filas):
        horas = float(s.hsa)
        out.append(
            {
                "sa": None if s.sa is None else int(s.sa),
                "dsa": s.dsa or "",
                "ev": None if s.ev is None else int(s.ev),
                "horas": int(horas) if horas.is_integer() else horas,
                "pct": (horas / total) if total else 0.0,
                "color": _color_hex(i),
                "etiqueta": f"{'' if s.sa is None else int(s.sa)}: {s.dsa or ''}".strip(": "),
            }
        )
    return out


def build_pie_png(shares: list[dict], *, dpi: int = 150) -> bytes:
    """Gráfico de sectores del reparto de horas, con leyenda 'nº: descripción'."""
    if not shares:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, "Sin horas que representar", ha="center", va="center")
        ax.axis("off")
    else:
        fig, ax = plt.subplots(figsize=(8.5, 5.2))
        valores = [s["horas"] for s in shares]
        colores = [s["color"] for s in shares]
        wedges, _texts, autotexts = ax.pie(
            valores,
            colors=colores,
            autopct=lambda p: f"{p:.1f}%",
            pctdistance=0.78,
            startangle=90,
            counterclock=False,
            wedgeprops={"linewidth": 1, "edgecolor": "white"},
        )
        for t in autotexts:
            t.set_fontsize(8)
            t.set_color("#1a1a1a")
        ax.axis("equal")
        ax.set_title(
            "Distribución de horas por situación de aprendizaje",
            fontsize=12,
            fontweight="bold",
            pad=16,
        )
        ax.legend(
            wedges,
            [s["etiqueta"] for s in shares],
            title="Situación de aprendizaje",
            loc="center left",
            bbox_to_anchor=(1.0, 0.5),
            fontsize=8,
            title_fontsize=9,
            frameon=False,
        )

    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buffer.getvalue()


def _fmt_pct2(value: float) -> str:
    return f"{value * 100:.2f}".replace(".", ",") + " %"


def build_sa_compare_png(
    sa_rows: list[int],
    labels: list[str],
    pct_il: list[float],
    pct_horas: list[float],
    *,
    dpi: int = 150,
) -> bytes:
    """Barras agrupadas: peso de cada SA según los IL asignados vs. según horas."""
    import numpy as np

    n = len(sa_rows)
    fig, ax = plt.subplots(figsize=(max(7.0, n * 0.7), 4.8))
    if n:
        x = np.arange(n)
        w = 0.4
        ax.bar(x - w / 2, [p * 100 for p in pct_il], w, label="Según IL asignados", color="#764ba2")
        ax.bar(x + w / 2, [p * 100 for p in pct_horas], w, label="Según carga de horas", color="#f0a500")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("% sobre el total")
        ax.set_title(
            "Peso de cada situación de aprendizaje: IL asignados vs. carga de horas",
            fontsize=11, fontweight="bold", pad=12,
        )
        ax.legend(fontsize=8, frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
        ax.yaxis.grid(True, color="#e6e6e6")
        ax.set_axisbelow(True)
    else:
        ax.text(0.5, 0.5, "Sin datos", ha="center", va="center")
        ax.axis("off")
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buffer.getvalue()


def render_word_table_html(headers: list[str], rows: list[list]) -> str:
    """Tabla HTML lista para pegar en Word (estilos en línea, sin CSS externo).

    Cabecera centrada horizontal y verticalmente; el resto de celdas centradas
    verticalmente y alineadas a la izquierda."""
    th = (
        'style="border:1px solid #666;padding:5px 9px;background:#000;color:#fff;'
        'text-align:center;vertical-align:middle;font-family:Calibri,Arial,sans-serif;"'
    )
    td = (
        'style="border:1px solid #666;padding:4px 9px;text-align:left;'
        'vertical-align:middle;font-family:Calibri,Arial,sans-serif;"'
    )
    body = []
    for row in rows:
        cells = "".join(
            f"<td {td}>{'' if v is None else html_lib.escape(str(v))}</td>" for v in row
        )
        body.append(f"<tr>{cells}</tr>")
    head = "".join(f"<th {th}>{html_lib.escape(str(h))}</th>" for h in headers)
    return (
        '<table style="border-collapse:collapse;">'
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"
    )


def _table_html(shares: list[dict]) -> str:
    rows = [
        [
            "" if s["sa"] is None else s["sa"],
            s["dsa"],
            "" if s["ev"] is None else s["ev"],
            s["horas"],
            _fmt_pct2(s["pct"]),
        ]
        for s in shares
    ]
    total_h = sum(float(s["horas"]) for s in shares)
    total_h = int(total_h) if float(total_h).is_integer() else total_h
    rows.append(["Total", "", "", total_h, "100,00 %"])
    return render_word_table_html(
        ["SA", "Situación de aprendizaje", "Ev.", "Horas", "% sobre el total"], rows
    )


# Botón pequeño y discreto, sin emojis, para incrustar justo al lado del elemento.
_MINI_BUTTON = r"""
<div style="font-family:Segoe UI,Arial,sans-serif;color-scheme:light;">
  <style>
    .si-mini {
      border:1px solid #c9c9d6; background:#fff; color:#444; border-radius:5px;
      padding:2px 9px; cursor:pointer; font-size:11px; line-height:1.6;
    }
    .si-mini:hover { background:#f2f2fb; }
    .si-mini.si-ok { border-color:#2e7d32; color:#2e7d32; }
    .si-note { font-size:11px; margin-left:6px; color:#777; }
  </style>
  <button type="button" class="si-mini" id="__BTN_ID__" onclick="__FN__()">__LABEL__</button>
  <span class="si-note" id="__BTN_ID__-note"></span>
<script>
  function __FN__() {
    var btn = document.getElementById("__BTN_ID__");
    var note = document.getElementById("__BTN_ID__-note");
    var done = function (okText, noteText, okColor) {
      var original = btn.textContent;
      btn.textContent = okText; btn.classList.add("si-ok");
      note.textContent = noteText || ""; note.style.color = okColor || "#777";
      setTimeout(function () {
        btn.textContent = original; btn.classList.remove("si-ok"); note.textContent = "";
      }, 1800);
    };
    __BODY__
  }
</script>
</div>
"""

_TABLE_BODY = r"""
    var container = document.createElement('div');
    container.innerHTML = __TABLE_JSON__;
    container.style.position = 'fixed'; container.style.left = '-9999px';
    document.body.appendChild(container);
    var range = document.createRange();
    range.selectNodeContents(container);
    var sel = window.getSelection();
    sel.removeAllRanges(); sel.addRange(range);
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    sel.removeAllRanges(); document.body.removeChild(container);
    if (ok) { done('Copiada', 'pega en Word con Ctrl+V'); }
    else { done('Error', 'no se pudo copiar', '#c62828'); }
"""

_IMG_BODY = r"""
    var b64 = "__IMG_B64__";
    var bin = atob(b64); var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) { bytes[i] = bin.charCodeAt(i); }
    var blob = new Blob([bytes], { type: 'image/png' });
    if (!navigator.clipboard || !window.ClipboardItem) {
      done('Error', 'usa "Descargar PNG"', '#c62828'); return;
    }
    navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]).then(
      function () { done('Copiado', 'pega en Word con Ctrl+V'); },
      function () { done('Error', 'usa "Descargar PNG"', '#c62828'); }
    );
"""


def build_table_copy_html(shares: list[dict]) -> str:
    body = _TABLE_BODY.replace("__TABLE_JSON__", json.dumps(_table_html(shares)))
    return (
        _MINI_BUTTON.replace("__BTN_ID__", "si-copy-table")
        .replace("__FN__", "siCopyTable")
        .replace("__LABEL__", "Copiar tabla")
        .replace("__BODY__", body)
    )


def build_html_table_copy_html(table_html: str, *, btn_id: str, fn: str, label: str) -> str:
    body = _TABLE_BODY.replace("__TABLE_JSON__", json.dumps(table_html))
    return (
        _MINI_BUTTON.replace("__BTN_ID__", btn_id)
        .replace("__FN__", fn)
        .replace("__LABEL__", label)
        .replace("__BODY__", body)
    )


def build_image_copy_html(png_bytes: bytes) -> str:
    body = _IMG_BODY.replace("__IMG_B64__", base64.b64encode(png_bytes).decode("ascii"))
    return (
        _MINI_BUTTON.replace("__BTN_ID__", "si-copy-img")
        .replace("__FN__", "siCopyImg")
        .replace("__LABEL__", "Copiar gráfico")
        .replace("__BODY__", body)
    )
