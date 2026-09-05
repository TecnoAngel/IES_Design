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
    horas y porcentaje sobre el total de horas. Ordenado por nº de SA (como la
    tabla dinámica del Excel)."""
    filas = [
        s
        for s in situaciones
        if s.hsa not in (None, "", 0) and float(s.hsa) > 0
    ]
    total = sum(float(s.hsa) for s in filas)
    filas.sort(key=lambda s: (s.sa is None, s.sa if s.sa is not None else 0))

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


def _table_html(shares: list[dict]) -> str:
    """Tabla en HTML lista para pegar en Word (bordes en línea, sin CSS externo)."""
    th = (
        'style="border:1px solid #666;padding:4px 8px;background:#000;color:#fff;'
        'text-align:left;font-family:Calibri,Arial,sans-serif;"'
    )
    td = 'style="border:1px solid #666;padding:4px 8px;font-family:Calibri,Arial,sans-serif;"'
    tdc = td.replace("padding:4px 8px;", "padding:4px 8px;text-align:center;")

    filas = []
    for s in shares:
        pct = f"{s['pct'] * 100:.2f}".replace(".", ",") + " %"
        filas.append(
            f"<tr>"
            f"<td {tdc}>{'' if s['sa'] is None else s['sa']}</td>"
            f"<td {td}>{html_lib.escape(s['dsa'])}</td>"
            f"<td {tdc}>{'' if s['ev'] is None else s['ev']}</td>"
            f"<td {tdc}>{s['horas']}</td>"
            f"<td {tdc}>{pct}</td>"
            f"</tr>"
        )

    total_h = sum(float(s["horas"]) for s in shares)
    total_h = int(total_h) if float(total_h).is_integer() else total_h
    filas.append(
        f'<tr><td {td}><b>Total</b></td><td {td}></td><td {tdc}></td>'
        f'<td {tdc}><b>{total_h}</b></td><td {tdc}><b>100,00 %</b></td></tr>'
    )

    return (
        '<table style="border-collapse:collapse;">'
        f"<thead><tr>"
        f"<th {th}>SA</th><th {th}>Situación de aprendizaje</th>"
        f"<th {th}>Ev.</th><th {th}>Horas</th><th {th}>% sobre el total</th>"
        f"</tr></thead><tbody>{''.join(filas)}</tbody></table>"
    )


_COPY_TEMPLATE = r"""
<div style="font-family:Segoe UI,Arial,sans-serif;color:#222;color-scheme:light;">
  <style>
    #si-wrap { color-scheme: light; }
    #si-wrap button {
      border:none; border-radius:8px; padding:9px 14px; margin:0 8px 8px 0;
      cursor:pointer; font-size:13px; font-weight:600; color:#fff;
      background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
    }
    #si-wrap button:hover { opacity:.9; }
    #si-wrap button.si-ok { background:#2e7d32; }
    #si-msg { font-size:12px; color:#2e7d32; margin-left:4px; }
    #si-table-preview {
      margin-top:10px; max-height:260px; overflow:auto; border:1px solid #e3e3ef;
      border-radius:8px; padding:8px; background:#fff;
    }
  </style>
  <div id="si-wrap">
    <button type="button" id="si-btn-table" onclick="siCopyTable()">📋 Copiar tabla (para Word)</button>
    <button type="button" id="si-btn-img" onclick="siCopyImg()">🖼️ Copiar gráfico (para Word)</button>
    <span id="si-msg"></span>
    <div id="si-table-preview">__TABLE_HTML__</div>
  </div>
</div>
<script>
  var SI_TABLE_HTML = __TABLE_JSON__;
  var SI_IMG_B64 = "__IMG_B64__";

  function siFlash(btnId, okText) {
    var btn = document.getElementById(btnId);
    var original = btn.textContent;
    btn.textContent = okText; btn.classList.add('si-ok');
    setTimeout(function () { btn.textContent = original; btn.classList.remove('si-ok'); }, 1600);
  }
  function siMsg(text, color) {
    var m = document.getElementById('si-msg');
    m.textContent = text; m.style.color = color || '#2e7d32';
    setTimeout(function () { m.textContent = ''; }, 2600);
  }

  function siCopyTable() {
    var container = document.createElement('div');
    container.innerHTML = SI_TABLE_HTML;
    container.style.position = 'fixed'; container.style.left = '-9999px';
    document.body.appendChild(container);
    var range = document.createRange();
    range.selectNodeContents(container);
    var sel = window.getSelection();
    sel.removeAllRanges(); sel.addRange(range);
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    sel.removeAllRanges(); document.body.removeChild(container);
    if (ok) { siFlash('si-btn-table', '✓ Tabla copiada'); siMsg('Pega en Word con Ctrl+V.'); }
    else { siMsg('No se ha podido copiar la tabla.', '#c62828'); }
  }

  function siB64ToBlob(b64, mime) {
    var bin = atob(b64); var len = bin.length; var bytes = new Uint8Array(len);
    for (var i = 0; i < len; i++) { bytes[i] = bin.charCodeAt(i); }
    return new Blob([bytes], { type: mime });
  }

  function siCopyImg() {
    var blob = siB64ToBlob(SI_IMG_B64, 'image/png');
    if (!navigator.clipboard || !window.ClipboardItem) {
      siMsg('Tu navegador no deja copiar imágenes; usa el botón de descarga.', '#c62828');
      return;
    }
    navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]).then(
      function () { siFlash('si-btn-img', '✓ Gráfico copiado'); siMsg('Pega en Word con Ctrl+V.'); },
      function () { siMsg('No se ha podido copiar el gráfico; usa el botón de descarga.', '#c62828'); }
    );
  }
</script>
"""


def build_copy_component_html(shares: list[dict], png_bytes: bytes) -> str:
    table_html = _table_html(shares)
    out = _COPY_TEMPLATE
    out = out.replace("__TABLE_HTML__", table_html)
    out = out.replace("__TABLE_JSON__", json.dumps(table_html))
    out = out.replace("__IMG_B64__", base64.b64encode(png_bytes).decode("ascii"))
    return out
