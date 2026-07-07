"""
Gera album_impressao.html para impressão em folha A4.
Lê os dados do album.csv e cria um grid colorido por status.

Uso:
  python imprimir.py
  — Abre album_impressao.html no navegador
  — Use Ctrl+P > Salvar como PDF ou imprimir diretamente
"""
import csv
import os
import sys
import webbrowser

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "album.csv")
HTML_PATH = os.path.join(BASE_DIR, "album_impressao.html")

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }

@page {
    size: A4 portrait;
    margin: 8mm;
}

body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 7pt;
    background: white;
    color: #111;
    width: 194mm;
}

/* ---- Cabeçalho ---- */
.page-header {
    text-align: center;
    margin-bottom: 3mm;
    border-bottom: 0.8px solid #1565C0;
    padding-bottom: 2mm;
}
.page-header h1 {
    font-size: 12pt;
    color: #1565C0;
    font-weight: bold;
}
.page-header .subtitle {
    font-size: 8pt;
    color: #555;
    margin-top: 1mm;
}

/* ---- Legenda ---- */
.legend {
    display: flex;
    gap: 6mm;
    justify-content: center;
    align-items: center;
    margin-bottom: 3mm;
    font-size: 7.5pt;
}
.leg {
    display: flex;
    align-items: center;
    gap: 1.5mm;
}
.leg-box {
    width: 7mm;
    height: 3.5mm;
    border: 0.4px solid #888;
    display: inline-block;
}
.leg-box.tenho    { background: #b7dfb7; }
.leg-box.repetida { background: #fff176; }
.leg-box.faltante { background: #ffcdd2; }
.leg-box.vazio    { background: #ffffff; }

/* ---- Seção FWC ---- */
.fwc-block {
    border: 0.6px solid #555;
    margin-bottom: 3mm;
    break-inside: avoid;
}
.fwc-header {
    background: #B71C1C;
    color: white;
    font-weight: bold;
    font-size: 7.5pt;
    padding: 1mm 2mm;
    text-align: center;
}
.fwc-grid {
    display: grid;
    grid-template-columns: repeat(10, 1fr);
}

/* ---- Grid de times ---- */
.teams-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.5mm;
}

.team-block {
    border: 0.6px solid #555;
    break-inside: avoid;
}
.team-header {
    background: #1565C0;
    color: white;
    font-weight: bold;
    font-size: 7pt;
    padding: 1mm 1.5mm;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.stickers-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
}

/* ---- Célula de figurinha ---- */
.sticker {
    padding: 0.8mm 0.2mm;
    text-align: center;
    border: 0.3px solid #ccc;
    font-size: 5.8pt;
    min-height: 4.8mm;
    display: flex;
    align-items: center;
    justify-content: center;
}

.tenho    { background: #b7dfb7; }
.repetida { background: #fff176; }
.faltante { background: #ffcdd2; }

/* ---- Rodapé ---- */
.footer {
    margin-top: 4mm;
    border-top: 0.5px solid #aaa;
    padding-top: 1.5mm;
    font-size: 6.5pt;
    color: #777;
    text-align: center;
}

/* ---- Print ---- */
@media print {
    body {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
    .teams-grid {
        /* força quebra de página quando necessário */
        orphans: 0;
        widows: 0;
    }
}
"""


def sticker_cell(code, status):
    cls = status if status in ("tenho", "repetida", "faltante") else "faltante"
    return f'<div class="sticker {cls}">{code}</div>'


def team_block(name, stickers):
    cells = "".join(sticker_cell(code, st) for code, st in stickers)
    safe = name.replace("&", "&amp;").replace("<", "&lt;")
    return (
        f'<div class="team-block">'
        f'<div class="team-header">{safe}</div>'
        f'<div class="stickers-grid">{cells}</div>'
        f'</div>'
    )


def main():
    if not os.path.exists(CSV_PATH):
        print("album.csv não encontrado. Execute gerar_album.py primeiro.")
        return

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    # Separar seção FWC dos times
    fwc = [r for r in rows if r["Codigo"] == "00" or r["Codigo"].startswith("FWC")]
    team_rows = [r for r in rows if r not in fwc]

    # Agrupar por time (mantendo a ordem do CSV)
    teams_order = []
    teams_data = {}
    for r in team_rows:
        sec = r["Secao"]
        if sec not in teams_data:
            teams_data[sec] = []
            teams_order.append(sec)
        teams_data[sec].append((r["Codigo"], r.get("Status", "faltante")))

    # Estatísticas
    total = len(rows)
    tenho = sum(1 for r in rows if r.get("Status", "") in ("tenho", "repetida"))
    repetidas = sum(1 for r in rows if r.get("Status", "") == "repetida")
    faltante_n = total - tenho
    pct = tenho / total * 100

    # HTML: bloco FWC
    fwc_cells = "".join(sticker_cell(r["Codigo"], r.get("Status", "faltante")) for r in fwc)
    fwc_html = (
        f'<div class="fwc-block">'
        f'<div class="fwc-header">FIFA World Cup 2026 — Introdução &amp; Museu '
        f'({len(fwc)} figurinhas)</div>'
        f'<div class="fwc-grid">{fwc_cells}</div>'
        f'</div>'
    )

    # HTML: times
    teams_html = "\n".join(team_block(t, teams_data[t]) for t in teams_order)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Álbum Panini — Copa do Mundo 2026</title>
  <style>{CSS}</style>
</head>
<body>

<div class="page-header">
  <h1>Álbum Panini — FIFA World Cup 2026&trade;</h1>
  <div class="subtitle">
    {tenho} de {total} figurinhas ({pct:.1f}%) &nbsp;|&nbsp;
    Faltam: {faltante_n} &nbsp;|&nbsp; Repetidas: {repetidas}
  </div>
</div>

<div class="legend">
  <div class="leg"><div class="leg-box tenho"></div> Tenho</div>
  <div class="leg"><div class="leg-box repetida"></div> Repetida (para trocar)</div>
  <div class="leg"><div class="leg-box faltante"></div> Faltante</div>
</div>

{fwc_html}

<div class="teams-grid">
{teams_html}
</div>

<div class="footer">
  Gerado por album_copa_2026 &nbsp;|&nbsp; {total} figurinhas &nbsp;|&nbsp; 48 seleções
</div>

</body>
</html>"""

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Gerado: {HTML_PATH}")
    print("Abrindo no navegador... Use Ctrl+P para imprimir em A4.")
    webbrowser.open(HTML_PATH)


if __name__ == "__main__":
    main()
