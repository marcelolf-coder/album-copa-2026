"""
Album Panini — Copa do Mundo 2026
Web app mobile-friendly via Streamlit.

Deploy: https://share.streamlit.io
Secrets necessários:
  sheet_id = "id-da-sua-planilha"
  [google_service_account]
  type = "service_account"
  project_id = "..."
  private_key_id = "..."
  private_key = "-----BEGIN RSA PRIVATE KEY-----\\n..."
  client_email = "..."
  ... (cole o JSON da service account aqui)
"""
import datetime
import json
import os
import re

import gspread
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(
    page_title="Album Copa 2026",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* ── Copa 2026 — Redesign ── */

/* Fundo branco em todos os contêineres principais */
html, body,
.stApp, .main,
section[data-testid="stMain"],
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stMainBlockContainer"],
.stMainBlockContainer,
[data-testid="block-container"],
.block-container,
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stBottom"] {
    background-color: #FFFFFF !important;
    color: #0D1B2A !important;
}

/* Header */
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] {
    background-color: #FFFFFF !important;
    border-bottom: 1px solid #E2E8F0 !important;
}

/* Sidebar */
[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
[data-testid="stSidebarContent"] {
    background-color: #EEF2FF !important;
}

/* Fundo secundário: inputs, selects, expanders, métricas */
[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div,
[data-baseweb="base-input"],
[data-testid="stTextInput"] > div > div,
[data-testid="stTextArea"] > div > div,
[data-testid="stSelectbox"] > div > div,
[data-testid="stExpanderDetails"],
.streamlit-expanderHeader,
[data-testid="stExpander"] > details,
[data-testid="metric-container"],
[data-testid="stMetricContainer"],
[data-testid="stCaptionContainer"] {
    background-color: #EEF2FF !important;
    color: #0D1B2A !important;
}

/* Texto — sem 'div'/'span' para não sobrescrever estilos inline do hero banner */
p, label, h1, h2, h3, h4, h5, h6, li { color: #0D1B2A !important; }
/* Botões primários sempre texto branco */
button[data-testid="baseButton-primary"],
button[data-testid="baseButton-primary"] * { color: #FFFFFF !important; }

/* Botões primários — azul FIFA (data-testid é o atributo real no DOM) */
button[data-testid="baseButton-primary"] {
    background-color: #003DA5 !important;
    border-color: #003DA5 !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 0.55rem 1rem !important;
    transition: background-color 0.2s !important;
}
button[data-testid="baseButton-primary"]:hover {
    background-color: #002d7a !important;
    border-color: #002d7a !important;
}

/* Botões secundários */
button[data-testid="baseButton-secondary"] {
    background-color: #F8FAFC !important;
    color: #0D1B2A !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}
button[data-testid="baseButton-secondary"]:hover {
    background-color: #EEF2FF !important;
    border-color: #003DA5 !important;
    color: #003DA5 !important;
}

/* Tabs */
div[data-testid="stTabs"] > div:first-child { overflow-x: auto; white-space: nowrap; }
button[data-baseweb="tab"] {
    color: #64748B !important;
    background-color: transparent !important;
    font-weight: 500 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    border-bottom-color: #C8962B !important;
    color: #003DA5 !important;
    font-weight: 700 !important;
}
[data-testid="stTabContent"] { background-color: #FFFFFF !important; }

/* Métricas */
div[data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 700 !important; color: #0D1B2A !important; }
div[data-testid="stMetricLabel"] { font-size: 0.8rem !important; font-weight: 600 !important; color: #64748B !important; }
div[data-testid="stMetricDelta"] { color: #C8962B !important; }

/* Grid de seleções */
div[data-testid="column"] { padding: 0 2px !important; }
div[data-testid="stSelectbox"] label { font-size: 0.75rem !important; color: #0D1B2A !important; }
div[data-testid="stSelectbox"] div   { font-size: 0.75rem !important; color: #0D1B2A !important; }

/* Links */
a { color: #003DA5 !important; }

/* Override dark mode do sistema */
@media (prefers-color-scheme: dark) {
    html, body, .stApp, .main,
    section[data-testid="stMain"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMainBlockContainer"],
    [data-testid="block-container"] {
        background-color: #FFFFFF !important;
        color: #0D1B2A !important;
    }
    [data-testid="stHeader"] { background-color: #FFFFFF !important; }
    p, label { color: #0D1B2A !important; }
}

/* Cards do grid de times — gradiente sutil + sombra */
div[data-testid="column"] button[data-testid="baseButton-secondary"] {
    background: linear-gradient(145deg, #FFFFFF, #F4F7FF) !important;
    border: 1.5px solid #D1D5DB !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07) !important;
    padding: 0.5rem 0.25rem !important;
    font-size: 0.75rem !important;
    line-height: 1.5 !important;
    min-height: 68px !important;
    white-space: pre-line !important;
    color: #0D1B2A !important;
}
div[data-testid="column"] button[data-testid="baseButton-secondary"]:hover {
    background: linear-gradient(145deg, #EEF2FF, #DBEAFE) !important;
    border-color: #003DA5 !important;
    color: #003DA5 !important;
    box-shadow: 0 3px 10px rgba(0,61,165,0.18) !important;
}
</style>
""", unsafe_allow_html=True)

# Injeta CSS de fundo branco diretamente no <head> via JS, garantindo que
# nosso <style> fique SEMPRE POR ÚLTIMO na cascata.
# MutationObserver reinsere o bloco toda vez que o Streamlit reinjectar
# seu CSS de modo escuro, garantindo que nunca perdemos a disputa de cascata.
streamlit_js_eval(js_expressions="""
(function () {
    try { localStorage.removeItem('stActiveTheme'); } catch (e) {}

    var ID = 'copa-theme-override';
    var CSS = [
        'html,body{background-color:#FFFFFF!important;color:#1E293B!important}',
        '.stApp{background-color:#FFFFFF!important;color:#1E293B!important}',
        '[data-testid="stAppViewContainer"]{background-color:#FFFFFF!important}',
        'section[data-testid="stMain"]{background-color:#FFFFFF!important}',
        '[data-testid="stMainBlockContainer"]{background-color:#FFFFFF!important}',
        '[data-testid="block-container"]{background-color:#FFFFFF!important}',
        '[data-testid="stHeader"]{background-color:#FFFFFF!important}'
    ].join('');

    function inject() {
        var old = document.getElementById(ID);
        if (old) old.remove();
        var s = document.createElement('style');
        s.id = ID;
        s.textContent = CSS;
        (document.head || document.documentElement).appendChild(s);
    }

    inject();

    new MutationObserver(function (mutations) {
        for (var i = 0; i < mutations.length; i++) {
            var nodes = mutations[i].addedNodes;
            for (var j = 0; j < nodes.length; j++) {
                if (nodes[j].tagName === 'STYLE' && nodes[j].id !== ID) {
                    setTimeout(inject, 10);
                    return;
                }
            }
        }
    }).observe(document.head || document.documentElement, { childList: true });
})()
""", key="force_light_theme")

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

STATUS_OPTIONS = ["faltante", "tenho", "repetida"]
STATUS_ICON = {"tenho": "🟢", "repetida": "🟡", "faltante": "🔴"}
STATUS_LABEL = {s: f"{STATUS_ICON[s]} {s}" for s in STATUS_OPTIONS}
COLS_GRID = 3

BANDEIRAS = {
    "México": "🇲🇽", "África do Sul": "🇿🇦", "Coreia do Sul": "🇰🇷",
    "Tchéquia": "🇨🇿", "Canadá": "🇨🇦", "Bósnia e Herzegovina": "🇧🇦",
    "Catar": "🇶🇦", "Suíça": "🇨🇭", "Brasil": "🇧🇷", "Marrocos": "🇲🇦",
    "Haiti": "🇭🇹", "Escócia": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "EUA": "🇺🇸", "Paraguai": "🇵🇾",
    "Austrália": "🇦🇺", "Turquia": "🇹🇷", "Alemanha": "🇩🇪", "Curaçao": "🇨🇼",
    "Costa do Marfim": "🇨🇮", "Equador": "🇪🇨", "Países Baixos": "🇳🇱",
    "Japão": "🇯🇵", "Suécia": "🇸🇪", "Tunísia": "🇹🇳", "Bélgica": "🇧🇪",
    "Egito": "🇪🇬", "Irã": "🇮🇷", "Nova Zelândia": "🇳🇿", "Espanha": "🇪🇸",
    "Cabo Verde": "🇨🇻", "Arábia Saudita": "🇸🇦", "Uruguai": "🇺🇾",
    "França": "🇫🇷", "Senegal": "🇸🇳", "Iraque": "🇮🇶", "Noruega": "🇳🇴",
    "Argentina": "🇦🇷", "Argélia": "🇩🇿", "Áustria": "🇦🇹", "Jordânia": "🇯🇴",
    "Portugal": "🇵🇹", "Congo RD": "🇨🇩", "Uzbequistão": "🇺🇿",
    "Colômbia": "🇨🇴", "Inglaterra": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Croácia": "🇭🇷",
    "Gana": "🇬🇭", "Panamá": "🇵🇦",
}

PAIS_ALIAS = {
    "HOLANDA": "Países Baixos", "HOLLAND": "Países Baixos",
    "NETHERLANDS": "Países Baixos", "PAÍSES BAIXOS": "Países Baixos",
    "PAISES BAIXOS": "Países Baixos",
    "COREIA": "Coreia do Sul", "KOREA": "Coreia do Sul",
    "ALEMANHA": "Alemanha", "GERMANY": "Alemanha",
    "COSTA DO MARFIM": "Costa do Marfim", "IVORY COAST": "Costa do Marfim",
    "NOVA ZELÂNDIA": "Nova Zelândia", "NEW ZEALAND": "Nova Zelândia",
    "NOVA ZELANDIA": "Nova Zelândia",
    "ARÁBIA SAUDITA": "Arábia Saudita", "SAUDI ARABIA": "Arábia Saudita",
    "ARABIA SAUDITA": "Arábia Saudita",
    "BÓSNIA": "Bósnia e Herzegovina", "BOSNIA": "Bósnia e Herzegovina",
    "BOSNIA E HERZEGOVINA": "Bósnia e Herzegovina",
    "AFRICA DO SUL": "África do Sul", "SOUTH AFRICA": "África do Sul",
}

TEAMS = [
    ("MEX", "México"), ("RSA", "África do Sul"), ("KOR", "Coreia do Sul"),
    ("CZE", "Tchéquia"), ("CAN", "Canadá"), ("BIH", "Bósnia e Herzegovina"),
    ("QAT", "Catar"), ("SUI", "Suíça"), ("BRA", "Brasil"), ("MAR", "Marrocos"),
    ("HAI", "Haiti"), ("SCO", "Escócia"), ("USA", "EUA"), ("PAR", "Paraguai"),
    ("AUS", "Austrália"), ("TUR", "Turquia"), ("GER", "Alemanha"), ("CUW", "Curaçao"),
    ("CIV", "Costa do Marfim"), ("ECU", "Equador"), ("NED", "Países Baixos"),
    ("JPN", "Japão"), ("SWE", "Suécia"), ("TUN", "Tunísia"), ("BEL", "Bélgica"),
    ("EGY", "Egito"), ("IRN", "Irã"), ("NZL", "Nova Zelândia"), ("ESP", "Espanha"),
    ("CPV", "Cabo Verde"), ("KSA", "Arábia Saudita"), ("URU", "Uruguai"),
    ("FRA", "França"), ("SEN", "Senegal"), ("IRQ", "Iraque"), ("NOR", "Noruega"),
    ("ARG", "Argentina"), ("ALG", "Argélia"), ("AUT", "Áustria"), ("JOR", "Jordânia"),
    ("POR", "Portugal"), ("COD", "Congo RD"), ("UZB", "Uzbequistão"),
    ("COL", "Colômbia"), ("ENG", "Inglaterra"), ("CRO", "Croácia"),
    ("GHA", "Gana"), ("PAN", "Panamá"),
]

FWC_CODES = [f"FWC{i}" for i in range(1, 20)]


def build_map() -> dict:
    m = {1: "00"}
    for i, code in enumerate(FWC_CODES):
        m[i + 2] = code
    for t_idx, (prefix, _) in enumerate(TEAMS):
        start = 21 + t_idx * 20
        for j in range(1, 21):
            m[start + j - 1] = f"{prefix}{j}"
    return m


def pais_label(pais: str) -> str:
    flag = BANDEIRAS.get(pais, "")
    return f"{flag} {pais}" if flag else pais


# ---------------------------------------------------------------------------
# Conexão com Google Sheets
# ---------------------------------------------------------------------------

@st.cache_resource
def get_worksheet():
    try:
        creds_info = dict(st.secrets["google_service_account"])
        sheet_id = st.secrets["sheet_id"]
    except Exception:
        base = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base, "service_account.json")) as f:
            creds_info = json.load(f)
        with open(os.path.join(base, "sheet_config.json")) as f:
            sheet_id = json.load(f)["sheet_id"]

    gc = gspread.service_account_from_dict(creds_info)
    return gc.open_by_key(sheet_id).sheet1


@st.cache_data(ttl=30)
def load_df() -> pd.DataFrame:
    ws = get_worksheet()
    df = pd.DataFrame(ws.get_all_records())
    df["Status"] = (
        df["Status"].astype(str).str.lower().str.strip().fillna("faltante")
    )
    df["Status"] = df["Status"].where(df["Status"].isin(STATUS_OPTIONS), "faltante")
    df["Repetidas"] = pd.to_numeric(df.get("Repetidas", 0), errors="coerce").fillna(0).astype(int)
    df["Descricao"] = df["Descricao"].astype(str)
    df["_row"] = range(2, len(df) + 2)
    return df


def salvar(updates: list):
    """updates: lista de (linha_planilha, status, repetidas)"""
    ws = get_worksheet()
    cells = []
    for row, status, reps in updates:
        cells.append(gspread.Cell(row, 4, status))
        cells.append(gspread.Cell(row, 5, str(reps)))
    ws.update_cells(cells, value_input_option="RAW")
    load_df.clear()


def _form_figurinha(fig):
    """Renderiza o formulário de edição de status de uma figurinha."""
    st.info(f"**{fig['Codigo']}** — {pais_label(fig['Pais'])} / {fig['Descricao']}")

    novo_status = st.radio(
        "Status:",
        STATUS_OPTIONS,
        index=STATUS_OPTIONS.index(fig["Status"]),
        horizontal=True,
        format_func=lambda s: STATUS_LABEL[s],
        key=f"radio_{fig['Codigo']}",
    )

    novas_reps = int(fig["Repetidas"])
    if novo_status == "repetida":
        novas_reps = st.number_input(
            "Cópias extras (para troca):",
            min_value=1,
            value=max(1, novas_reps),
            step=1,
            key=f"reps_{fig['Codigo']}",
        )

    if st.button("✅ Salvar", type="primary", use_container_width=True, key=f"btn_{fig['Codigo']}"):
        with st.spinner("Salvando..."):
            salvar([(int(fig["_row"]), novo_status, int(novas_reps))])
        st.success(f"**{fig['Codigo']}** → {STATUS_LABEL[novo_status]}")
        st.rerun()


# ---------------------------------------------------------------------------
# Impressão A4
# ---------------------------------------------------------------------------

def _html_impressao(faltantes: pd.DataFrame, repetidas: pd.DataFrame) -> str:
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    total_f = len(faltantes)
    total_r = len(repetidas)

    blocos_falt = []
    for pais, grupo in faltantes.groupby("Pais", sort=True):
        linhas = "\n".join(
            f"{r['Codigo']} — {r['Descricao']}"
            for _, r in grupo.iterrows()
        )
        blocos_falt.append(
            f'<div class="pais">'
            f'<div class="pais-nome">{pais} ({len(grupo)})</div>'
            f'<div class="codigos">{linhas}</div>'
            f'</div>'
        )
    grid_falt = "\n".join(blocos_falt) if blocos_falt else "<p>Nenhuma figurinha faltando!</p>"

    linhas_rep = []
    for pais, grupo in repetidas.groupby("Pais", sort=True):
        for _, fig in grupo.iterrows():
            extras = int(fig["Repetidas"])
            sufixo = f" +{extras}x" if extras > 0 else ""
            linhas_rep.append(f"{fig['Codigo']} — {fig['Descricao']}{sufixo}")
    grid_rep = "<br>".join(linhas_rep) if linhas_rep else "Nenhuma figurinha para trocar."

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Album Copa 2026 - Impressao</title>
<style>
  @page {{ size: A4 portrait; margin: 12mm; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: Arial, sans-serif; font-size: 8.5pt; color: #111; }}
  h1 {{ font-size: 13pt; text-align: center; margin-bottom: 2mm; }}
  .meta {{ text-align: center; font-size: 7.5pt; color: #555; margin-bottom: 5mm; }}
  h2 {{ font-size: 10pt; background: #eee; padding: 1.5mm 2mm; margin: 4mm 0 3mm;
        border-left: 3px solid #333; }}
  .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 3mm; }}
  .pais {{ break-inside: avoid; border: 0.3mm solid #ccc; border-radius: 1.5mm;
           padding: 1.5mm 2mm; }}
  .pais-nome {{ font-weight: bold; font-size: 7.5pt; margin-bottom: 0.8mm; }}
  .codigos {{ font-size: 7pt; color: #333; line-height: 1.5; white-space: pre-line; }}
  .page-break {{ page-break-after: always; height: 0; }}
  .rep-box {{ border: 0.3mm solid #ccc; border-radius: 1.5mm; padding: 3mm 4mm;
              font-size: 8pt; line-height: 1.8; }}
  .footer {{ margin-top: 6mm; text-align: center; font-size: 7pt; color: #888; }}
</style>
</head>
<body>

<h1>&#9917; Album Copa do Mundo 2026</h1>
<p class="meta">Gerado em {hoje} &bull; {total_f} faltantes &bull; {total_r} tipos para trocar</p>

<h2>&#10060; Figurinhas Faltantes &mdash; {total_f} figurinhas</h2>
<div class="grid">
{grid_falt}
</div>

<div class="page-break"></div>

<h1>&#9917; Album Copa do Mundo 2026</h1>
<p class="meta">Gerado em {hoje}</p>

<h2>&#128260; Para Trocar &mdash; {total_r} tipos</h2>
<div class="rep-box">{grid_rep}</div>

<p class="footer">Abra no navegador e pressione Ctrl+P para imprimir em A4</p>
</body>
</html>"""


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------

@st.cache_resource
def get_ocr():
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR()


_CODIGO_RE = re.compile(
    r'\b(FWC|CC|ALG|ARG|AUS|AUT|BEL|BIH|BRA|CAN|CIV|COD|COL|CPV|CRO|CUW|CZE|'
    r'ECU|EGY|ENG|ESP|FRA|GER|GHA|HAI|IRN|IRQ|JOR|JPN|KOR|KSA|MAR|MEX|NED|'
    r'NOR|NZL|PAN|PAR|POR|QAT|RSA|SCO|SEN|SUI|SWE|TUN|TUR|URU|USA|UZB)\s*(\d{1,2})\b',
    re.IGNORECASE,
)


def _pre_processar(img: Image.Image) -> np.ndarray:
    img = img.convert("L")
    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    return np.array(img.convert("RGB"))


def _extrair_codigos(foto: Image.Image, codigos_validos: set) -> list:
    arr = _pre_processar(foto)
    ocr = get_ocr()
    resultado, _ = ocr(arr)
    if not resultado:
        return []

    encontrados = []
    for _, texto, confianca in resultado:
        if confianca < 0.5:
            continue
        texto_limpo = texto.strip().upper().replace(" ", "")
        for m in _CODIGO_RE.finditer(texto_limpo):
            codigo = m.group(1).upper() + m.group(2)
            if codigo in codigos_validos:
                encontrados.append(codigo)
    return list(dict.fromkeys(encontrados))


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "time_sel" not in st.session_state:
    st.session_state.time_sel = None


# ---------------------------------------------------------------------------
# Abas
# ---------------------------------------------------------------------------

tab_resumo, tab_time, tab_busca, tab_scanner, tab_pacote, tab_listas = st.tabs(
    ["📊 Resumo", "🏳️ Por Time", "🔍 Busca", "📷 Scanner", "📦 Pacote", "📋 Listas"]
)


# ── Resumo ───────────────────────────────────────────────────────────────────
with tab_resumo:
    st.markdown("""
<div style="background:linear-gradient(135deg,#001F5B 0%,#003DA5 55%,#1565C0 100%);
     border-radius:16px;padding:24px 20px;margin-bottom:4px;text-align:center;
     box-shadow:0 4px 20px rgba(0,61,165,0.25);">
  <div style="font-size:0.78rem;color:rgba(255,255,255,0.65);letter-spacing:2px;
              text-transform:uppercase;margin-bottom:4px;">
    🏆 FIFA World Cup 2026
  </div>
  <div style="font-size:1.9rem;font-weight:900;color:#FFFFFF;letter-spacing:-0.5px;
              margin-bottom:10px;">
    ⚽ Álbum de Figurinhas
  </div>
  <div style="font-size:1rem;color:rgba(255,255,255,0.88);margin-bottom:10px;">
    🇺🇸 EUA &nbsp;·&nbsp; 🇲🇽 México &nbsp;·&nbsp; 🇨🇦 Canadá
  </div>
  <div style="display:inline-block;background:rgba(255,255,255,0.12);
              border-radius:20px;padding:4px 14px;
              font-size:0.8rem;color:#FFD700;font-weight:600;">
    Junho — Julho 2026
  </div>
</div>
""", unsafe_allow_html=True)

    if st.button("🔄 Atualizar dados", use_container_width=True, type="primary"):
        load_df.clear()
        st.rerun()

    df = load_df()
    total = len(df)
    tenho_n = df["Status"].isin(["tenho", "repetida"]).sum()
    faltante_n = (df["Status"] == "faltante").sum()
    repetida_n = (df["Status"] == "repetida").sum()

    _pct = tenho_n / total * 100
    st.markdown(f"""
<div style="margin:14px 0 2px;">
  <div style="background:#E2E8F0;border-radius:99px;height:18px;overflow:hidden;
              box-shadow:inset 0 1px 3px rgba(0,0,0,0.08);">
    <div style="background:linear-gradient(90deg,#B8720A,#E8B800);
                width:{_pct:.1f}%;height:100%;border-radius:99px;
                box-shadow:0 1px 4px rgba(200,150,43,0.4);"></div>
  </div>
</div>
<p style="font-size:0.82rem;color:#64748B;margin:4px 0 10px;text-align:right;">
  <strong style="color:#0D1B2A;">{int(tenho_n)}</strong> de {int(total)} figurinhas
  &nbsp;·&nbsp; <strong style="color:#C8962B;">{_pct:.1f}%</strong> completo
</p>
""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 Tenho", int(tenho_n))
    c2.metric("🔴 Faltam", int(faltante_n))
    c3.metric("🟡 Repetidas", int(repetida_n))

    st.divider()
    st.subheader("Por seleção")

    # Excluir FWC, sticker 00 e CC da tabela de seleções
    _excluir_mask = (
        df["Codigo"].str.startswith("FWC", na=False) |
        df["Codigo"].str.startswith("CC", na=False) |
        (df["Codigo"] == "00")
    )
    times_df = df[~_excluir_mask]
    stats = (
        times_df.groupby("Pais")["Status"]
        .apply(lambda s: pd.Series({
            "Tenho": s.isin(["tenho", "repetida"]).sum(),
            "Total": len(s),
        }))
        .unstack()
        .reset_index()
    )
    stats["Progresso"] = stats.apply(lambda r: f"{int(r['Tenho'])}/{int(r['Total'])}", axis=1)
    stats["✅"] = stats["Tenho"] == stats["Total"]
    stats = stats.sort_values("Tenho", ascending=False)
    stats["Seleção"] = stats["Pais"].apply(pais_label)

    _rows = ""
    for _i, (_, _r) in enumerate(stats.iterrows()):
        _pt = _r["Tenho"] / _r["Total"] * 100
        _bg = "#FAFBFF" if _i % 2 == 0 else "#FFFFFF"
        _ck = "✅" if _r["✅"] else ""
        _rows += f"""<tr style="background:{_bg};">
          <td style="padding:7px 10px;font-size:0.83rem;color:#0D1B2A;border-bottom:1px solid #F1F5F9;">{_r["Seleção"]}</td>
          <td style="padding:7px 10px;border-bottom:1px solid #F1F5F9;">
            <div style="display:flex;align-items:center;gap:7px;">
              <div style="flex:1;background:#E2E8F0;border-radius:99px;height:10px;overflow:hidden;min-width:60px;">
                <div style="background:linear-gradient(90deg,#B8720A,#E8B800);width:{_pt:.0f}%;height:100%;border-radius:99px;"></div>
              </div>
              <span style="font-size:0.76rem;color:#64748B;white-space:nowrap;">{int(_r["Tenho"])}/{int(_r["Total"])}</span>
            </div>
          </td>
          <td style="padding:7px 10px;text-align:center;font-size:0.9rem;border-bottom:1px solid #F1F5F9;">{_ck}</td>
        </tr>"""

    st.markdown(f"""
<div style="border-radius:10px;overflow:hidden;border:1px solid #E2E8F0;margin-top:8px;">
  <table style="width:100%;border-collapse:collapse;background:#FFFFFF;">
    <thead>
      <tr style="background:#EEF2FF;">
        <th style="padding:9px 10px;text-align:left;font-size:0.78rem;color:#003DA5;font-weight:700;letter-spacing:0.03em;border-bottom:2px solid #D1D5DB;">SELEÇÃO</th>
        <th style="padding:9px 10px;text-align:left;font-size:0.78rem;color:#003DA5;font-weight:700;letter-spacing:0.03em;border-bottom:2px solid #D1D5DB;">PROGRESSO</th>
        <th style="padding:9px 10px;text-align:center;font-size:0.78rem;color:#003DA5;font-weight:700;letter-spacing:0.03em;border-bottom:2px solid #D1D5DB;">OK</th>
      </tr>
    </thead>
    <tbody>{_rows}</tbody>
  </table>
</div>
""", unsafe_allow_html=True)


# ── Por Time ─────────────────────────────────────────────────────────────────
with tab_time:
    df = load_df()
    _excluir_especiais = (
        df["Codigo"].str.startswith("FWC", na=False) |
        df["Codigo"].str.startswith("CC", na=False) |
        (df["Codigo"] == "00")
    )
    _teams_order = {nome: i for i, (_, nome) in enumerate(TEAMS)}
    paises = sorted(df[~_excluir_especiais]["Pais"].unique(), key=lambda p: _teams_order.get(p, 999))

    pais_tenho = {
        p: int(df[df["Pais"] == p]["Status"].isin(["tenho", "repetida"]).sum())
        for p in paises
    }

    if st.session_state.time_sel is None:
        # ── Grid de seleção ──────────────────────────────────────────────────
        st.caption("Toque em uma seleção para ver e editar as figurinhas.")

        fwc_df = df[df["Codigo"].str.startswith("FWC", na=False) | (df["Codigo"] == "00")]
        fwc_tenho = int(fwc_df["Status"].isin(["tenho", "repetida"]).sum())
        fwc_total = len(fwc_df)
        fwc_check = " ✅" if fwc_tenho == fwc_total else ""

        cc_df = df[df["Codigo"].str.startswith("CC", na=False)]
        cc_tenho = int(cc_df["Status"].isin(["tenho", "repetida"]).sum())
        cc_total = len(cc_df)
        cc_check = " ✅" if cc_tenho == cc_total else ""

        col_fwc, col_cc = st.columns(2)
        with col_fwc:
            if st.button(
                f"⭐ FWC  {fwc_tenho}/{fwc_total}{fwc_check}",
                use_container_width=True,
                key="card_fwc",
            ):
                st.session_state.time_sel = "_FWC_"
                st.rerun()
        with col_cc:
            if st.button(
                f"🥤 Coca-Cola  {cc_tenho}/{cc_total}{cc_check}",
                use_container_width=True,
                key="card_cc",
            ):
                st.session_state.time_sel = "_CC_"
                st.rerun()

        st.write("")

        cols_g = st.columns(3)
        for i, pais in enumerate(paises):
            tenho_p = pais_tenho[pais]
            check = " ✅" if tenho_p == 20 else ""
            flag = BANDEIRAS.get(pais, "")
            with cols_g[i % 3]:
                if st.button(
                    f"{flag} {pais}  {tenho_p}/20{check}",
                    key=f"card_{pais}",
                    use_container_width=True,
                ):
                    st.session_state.time_sel = pais
                    st.rerun()

    else:
        # ── Detalhe do time ──────────────────────────────────────────────────
        escolha = st.session_state.time_sel

        if st.button("← Voltar", key="voltar_time"):
            st.session_state.time_sel = None
            st.rerun()

        if escolha == "_FWC_":
            time_df = df[df["Codigo"].str.startswith("FWC", na=False) | (df["Codigo"] == "00")].copy()
            st.subheader("⭐ FIFA World Cup 2026")
        elif escolha == "_CC_":
            time_df = df[df["Codigo"].str.startswith("CC", na=False)].copy()
            st.subheader("🥤 Coca-Cola — Figurinhas Promocionais")
            st.caption("Encontradas embaixo do rótulo de garrafas Coca-Cola (600ml e 2,5L).")
        else:
            time_df = df[df["Pais"] == escolha].copy()
            st.subheader(pais_label(escolha))

        time_df = time_df.reset_index(drop=True)
        tenho_time = int(time_df["Status"].isin(["tenho", "repetida"]).sum())
        total_time = len(time_df)

        st.progress(tenho_time / total_time)
        st.caption(f"{tenho_time}/{total_time} figurinhas")
        if tenho_time == total_time:
            st.success("Time completo! 🏆")

        st.divider()
        st.caption("Toque no ícone para alterar o status de cada figurinha.")

        prefix = f"grid_{escolha}_"
        alteracoes: dict = {}

        chunks = [time_df.iloc[i: i + COLS_GRID] for i in range(0, len(time_df), COLS_GRID)]
        for chunk in chunks:
            cols = st.columns(COLS_GRID)
            for col_i, (_, fig) in enumerate(chunk.iterrows()):
                with cols[col_i]:
                    key = f"{prefix}{fig['Codigo']}"
                    idx_atual = STATUS_OPTIONS.index(fig["Status"])
                    novo = st.selectbox(
                        fig["Codigo"],
                        STATUS_OPTIONS,
                        index=idx_atual,
                        key=key,
                        format_func=lambda s: STATUS_ICON[s],
                    )
                    nome = fig["Descricao"]
                    if nome and nome not in ("nan", fig["Codigo"]):
                        st.caption(nome)
                    if novo != fig["Status"]:
                        alteracoes[int(fig["_row"])] = (novo, int(fig["Repetidas"]))

        if alteracoes:
            label = f"💾 Salvar {len(alteracoes)} alteração(ões)"
            if st.button(label, type="primary", use_container_width=True, key="salvar_time"):
                updates = [(row, st_val, reps) for row, (st_val, reps) in alteracoes.items()]
                with st.spinner("Salvando..."):
                    salvar(updates)
                df_novo = load_df()
                if escolha == "_FWC_":
                    time_novo = df_novo[
                        df_novo["Codigo"].str.startswith("FWC", na=False) | (df_novo["Codigo"] == "00")
                    ]
                elif escolha == "_CC_":
                    time_novo = df_novo[df_novo["Codigo"].str.startswith("CC", na=False)]
                else:
                    time_novo = df_novo[df_novo["Pais"] == escolha]
                if time_novo["Status"].isin(["tenho", "repetida"]).sum() == len(time_novo):
                    st.balloons()
                st.success("Salvo!")
                st.rerun()
        else:
            st.info("Altere o ícone de alguma figurinha para habilitar o salvar.")


# ── Busca ─────────────────────────────────────────────────────────────────────
with tab_busca:
    st.subheader("Buscar figurinha")
    st.caption("Digite o código (ex: BRA5) ou parte do nome do jogador (ex: Messi, Vini).")

    df = load_df()

    query = st.text_input(
        "Busca",
        placeholder="BRA5 ou Vinícius",
        label_visibility="collapsed",
    ).strip()

    if query:
        q_upper = query.upper()

        match_codigo = df[df["Codigo"] == q_upper]

        if not match_codigo.empty:
            resultados = match_codigo
        else:
            mask_desc = df["Descricao"].str.contains(query, case=False, na=False)

            pais_alvo = PAIS_ALIAS.get(q_upper)
            if pais_alvo:
                mask_pais = df["Pais"] == pais_alvo
            else:
                mask_pais = df["Pais"].str.contains(query, case=False, na=False)

            resultados = df[mask_desc | mask_pais]

        if resultados.empty:
            st.error(f"Nenhuma figurinha encontrada para **{query}**.")
        elif len(resultados) == 1:
            _form_figurinha(resultados.iloc[0])
        else:
            opcoes_label = [
                f"{r['Codigo']} — {r['Descricao']} ({pais_label(r['Pais'])})"
                for _, r in resultados.iterrows()
            ]
            escolha_idx = st.selectbox(
                f"{len(resultados)} figurinhas encontradas — selecione:",
                range(len(opcoes_label)),
                format_func=lambda i: opcoes_label[i],
            )
            _form_figurinha(resultados.iloc[escolha_idx])


# ── Scanner ───────────────────────────────────────────────────────────────────
with tab_scanner:
    st.subheader("Scanner de figurinha")
    st.caption("Fotografe o código impresso na figurinha (ex: BRA5). Mantenha boa iluminação.")

    df = load_df()
    codigos_validos = set(df["Codigo"].tolist())

    foto = st.camera_input("Apontar câmera para o código da figurinha")

    if foto:
        with st.spinner("Lendo código..."):
            img = Image.open(foto)
            encontrados = _extrair_codigos(img, codigos_validos)

        if not encontrados:
            st.error("Nenhum código reconhecido. Tente com mais luz ou mais perto do código.")
        else:
            codigo_lido = encontrados[0]
            if len(encontrados) > 1:
                codigo_lido = st.selectbox(
                    "Mais de um código detectado — confirme qual é:",
                    encontrados,
                )

            fig = df[df["Codigo"] == codigo_lido].iloc[0]
            st.success(f"Código detectado: **{fig['Codigo']}**")
            st.info(f"**{fig['Codigo']}** — {pais_label(fig['Pais'])} / {fig['Descricao']}")
            st.caption(f"Status atual: {STATUS_LABEL[fig['Status']]}")

            st.divider()
            st.write("**Confirmar como:**")
            c1, c2 = st.columns(2)

            with c1:
                if st.button("🟢 Tenho", use_container_width=True, key="scan_tenho"):
                    reps = int(fig["Repetidas"])
                    salvar([(int(fig["_row"]), "tenho", reps)])
                    st.success(f"{fig['Codigo']} marcado como **tenho**!")
                    st.rerun()

            with c2:
                if st.button("🟡 Repetida", use_container_width=True, key="scan_rep"):
                    reps = max(1, int(fig["Repetidas"]) + 1)
                    salvar([(int(fig["_row"]), "repetida", reps)])
                    st.success(f"{fig['Codigo']} marcado como **repetida** ({reps}x)!")
                    st.rerun()


# ── Pacote ────────────────────────────────────────────────────────────────────
with tab_pacote:
    st.subheader("📦 Adicionar figurinhas")
    st.caption("Digite os números do pacote separados por espaço, vírgula ou linha.")

    entrada = st.text_area(
        "Números:",
        placeholder="27 80 85 89 107\n120 125 132 136 160",
        height=120,
        label_visibility="collapsed",
        key="pacote_entrada",
    )

    if st.button("✅ Adicionar figurinhas", type="primary", use_container_width=True, key="pacote_btn"):
        numeros_raw = re.split(r"[,\s\n]+", entrada.strip())
        numeros = [int(n) for n in numeros_raw if n.strip().isdigit()]

        if not numeros:
            st.error("Nenhum número válido encontrado.")
        else:
            num_map = build_map()
            df_atual = load_df()
            by_code = df_atual.set_index("Codigo")

            novas, repetidas_lst, desconhecidos = [], [], []
            updates = []

            for n in sorted(set(numeros)):
                code = num_map.get(n)
                if not code or code not in by_code.index:
                    desconhecidos.append(n)
                    continue
                row_data = by_code.loc[code]
                status = row_data["Status"]
                reps_atual = int(row_data["Repetidas"])
                row_num = int(row_data["_row"])

                if status == "faltante":
                    updates.append((row_num, "tenho", 0))
                    novas.append((n, code))
                elif status == "tenho":
                    updates.append((row_num, "repetida", 1))
                    repetidas_lst.append((n, code, 1))
                else:
                    nova_qtd = reps_atual + 1
                    updates.append((row_num, "repetida", nova_qtd))
                    repetidas_lst.append((n, code, nova_qtd))

            if updates:
                with st.spinner("Salvando no Google Sheets..."):
                    salvar(updates)

                df_total = load_df()
                total_tenho = int(df_total["Status"].isin(["tenho", "repetida"]).sum())

                if novas:
                    st.success(f"✅ {len(novas)} figurinha(s) nova(s) adicionada(s)!")
                    st.code("\n".join(f"{n:>4}  {code}" for n, code in novas), language=None)

                if repetidas_lst:
                    st.warning(f"🟡 {len(repetidas_lst)} repetida(s) registrada(s).")
                    st.code(
                        "\n".join(f"{n:>4}  {code}  (extras: {qtd})" for n, code, qtd in repetidas_lst),
                        language=None,
                    )

                if desconhecidos:
                    st.error(f"⚠️ Números não encontrados: {desconhecidos}")

                st.info(f"📊 Total no álbum agora: **{total_tenho}/980** ({total_tenho/980*100:.1f}%)")
            else:
                st.warning("Nenhuma atualização necessária.")


# ── Listas ────────────────────────────────────────────────────────────────────
with tab_listas:
    df = load_df()
    faltantes = df[df["Status"] == "faltante"]
    repetidas = df[df["Status"] == "repetida"]

    html_bytes = _html_impressao(faltantes, repetidas).encode("utf-8")
    nome_arquivo = f"album_copa2026_{datetime.date.today().strftime('%Y%m%d')}.html"
    st.download_button(
        label="🖨️ Baixar para impressão (A4)",
        data=html_bytes,
        file_name=nome_arquivo,
        mime="text/html",
        use_container_width=True,
    )
    st.caption("Abra o arquivo baixado no navegador e pressione Ctrl+P para imprimir.")

    st.divider()

    sub_falt, sub_rep, sub_troca = st.tabs(["❌ Faltantes", "🔄 Para trocar", "🤝 Trocas"])

    with sub_falt:
        st.caption(f"{len(faltantes)} figurinhas faltando")

        if faltantes.empty:
            st.success("Album completo! 🏆")
        else:
            for pais, grupo in faltantes.groupby("Pais", sort=True):
                linhas = "\n".join(
                    f"{r['Codigo']} — {r['Descricao']}"
                    for _, r in grupo.iterrows()
                )
                with st.expander(f"{pais_label(pais)} — {len(grupo)} faltando"):
                    st.code(linhas, language=None)

    with sub_rep:
        st.caption(f"{len(repetidas)} tipos de figurinhas repetidas")

        if repetidas.empty:
            st.info("Nenhuma repetida ainda.")
        else:
            linhas = []
            for _, fig in repetidas.iterrows():
                extras = int(fig["Repetidas"])
                sufixo = f"  (+{extras} extra{'s' if extras != 1 else ''})" if extras > 0 else ""
                linhas.append(f"{fig['Codigo']} — {fig['Descricao']} ({pais_label(fig['Pais'])}){sufixo}")

            st.code("\n".join(linhas), language=None)
            st.caption("Copie a lista acima e compartilhe com quem quiser trocar!")

    with sub_troca:
        st.caption("Cole os números das figurinhas que **faltam ao seu amigo** para ver o que você pode oferecer.")

        lista_amigo = st.text_area(
            "Faltantes do amigo:",
            placeholder="1 5 12 27 45 80 102...",
            height=100,
            label_visibility="collapsed",
            key="troca_entrada",
        )

        if st.button("🔍 Ver trocas possíveis", use_container_width=True, key="troca_btn"):
            numeros_raw = re.split(r"[,\s\n]+", lista_amigo.strip())
            numeros_amigo = {int(n) for n in numeros_raw if n.strip().isdigit()}

            if not numeros_amigo:
                st.error("Nenhum número válido encontrado.")
            else:
                num_map = build_map()
                codigos_faltam_amigo = {num_map[n] for n in numeros_amigo if n in num_map}

                posso_oferecer = repetidas[repetidas["Codigo"].isin(codigos_faltam_amigo)]
                nao_tenho_rep = codigos_faltam_amigo - set(repetidas["Codigo"])
                posso_emprestar = df[
                    df["Codigo"].isin(nao_tenho_rep) & (df["Status"] == "tenho")
                ]

                st.markdown(f"**{len(numeros_amigo)}** figurinhas na lista do amigo analisadas.")
                st.divider()

                if posso_oferecer.empty:
                    st.warning("Você não tem nenhuma repetida que falta ao seu amigo.")
                else:
                    st.success(f"✅ Você pode oferecer **{len(posso_oferecer)}** figurinha(s) (suas repetidas):")
                    linhas = [
                        f"{fig['Codigo']} — {fig['Descricao']} ({pais_label(fig['Pais'])})  +{int(fig['Repetidas'])}x"
                        for _, fig in posso_oferecer.iterrows()
                    ]
                    st.code("\n".join(linhas), language=None)

                if not posso_emprestar.empty:
                    st.info(
                        f"ℹ️ Você **tem** (sem repetida) mais **{len(posso_emprestar)}** que o amigo precisa "
                        f"— estas você só pode oferecer se quiser abrir mão da sua cópia:"
                    )
                    linhas2 = [
                        f"{r['Codigo']} — {r['Descricao']} ({pais_label(r['Pais'])})"
                        for _, r in posso_emprestar.iterrows()
                    ]
                    st.code("\n".join(linhas2), language=None)
