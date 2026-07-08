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
import unicodedata

import gspread
import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_js_eval import streamlit_js_eval

from logic import (
    STATUS_OPTIONS, STATUS_ICON, STATUS_LABEL,
    BANDEIRAS, PAIS_ALIAS, TEAMS, FWC_CODES, _FLAG_BY_PREFIX,
    LEGENDS, LEGENDS_VARIAÇÕES, LEGENDS_COR, LEGENDS_EMOJI,
    build_map, pais_label,
    _texto_whatsapp, _texto_whatsapp_trocas, _html_impressao,
    _pre_processar, _extrair_codigos,
    _classificar_pacote, _parsear_entrada_pacote,
)

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

streamlit_js_eval(js_expressions="try { localStorage.removeItem('stActiveTheme'); } catch (e) {}", key="force_light_theme")

# ---------------------------------------------------------------------------
# Constantes de UI
# ---------------------------------------------------------------------------

COLS_GRID = 3


# ---------------------------------------------------------------------------
# Conexão com Google Sheets
# ---------------------------------------------------------------------------

@st.cache_resource
def get_spreadsheet():
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
    return gc.open_by_key(sheet_id)


@st.cache_resource
def get_worksheet():
    return get_spreadsheet().sheet1


@st.cache_resource
def get_worksheet_legends():
    sh = get_spreadsheet()
    try:
        ws = sh.worksheet("Legends")
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title="Legends", rows=100, cols=4)
        header = ["Jogador", "Pais", "Variacao", "Status"]
        rows = [header] + [
            [jogador, pais, var, "faltante"]
            for _, pais, jogador in LEGENDS
            for var in LEGENDS_VARIAÇÕES
        ]
        ws.update(rows, "A1")
    return ws


_LEGENDS_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "legends.csv")


def _init_legends_csv():
    if not os.path.exists(_LEGENDS_CSV):
        import csv
        with open(_LEGENDS_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["Prefix", "Jogador", "Pais", "Variacao", "Status"])
            for prefix, pais, jogador in LEGENDS:
                for var in LEGENDS_VARIAÇÕES:
                    writer.writerow([prefix, jogador, pais, var, "faltante"])


def _load_legends_csv() -> dict:
    import csv
    _init_legends_csv()
    result = {}
    with open(_LEGENDS_CSV, newline="", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            prefix = row.get("Prefix", "")
            var = row.get("Variacao", "")
            status = row.get("Status", "faltante")
            if prefix and var:
                result[(prefix, var)] = (status, i)
    return result


def _salvar_legend_csv(prefix: str, variacao: str, status: str):
    import csv
    _init_legends_csv()
    rows = []
    with open(_LEGENDS_CSV, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        if row["Prefix"] == prefix and row["Variacao"] == variacao:
            row["Status"] = status
            break
    with open(_LEGENDS_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Prefix", "Jogador", "Pais", "Variacao", "Status"])
        writer.writeheader()
        writer.writerows(rows)


@st.cache_data(ttl=30)
def load_legends() -> dict:
    """Retorna {(prefix, variacao): (status, row_num)}. Tenta Sheets, cai para CSV."""
    try:
        ws = get_worksheet_legends()
        records = ws.get_all_records()
        prefix_map = {jogador: prefix for prefix, _, jogador in LEGENDS}
        result = {}
        for i, r in enumerate(records):
            prefix = prefix_map.get(r.get("Jogador", ""))
            var = r.get("Variacao", "")
            status = r.get("Status", "faltante")
            if prefix and var:
                result[(prefix, var)] = (status, i + 2)
        return result
    except Exception:
        return _load_legends_csv()


def salvar_legend(row_num: int, status: str, prefix: str = "", variacao: str = ""):
    # Grava no Sheets
    try:
        ws = get_worksheet_legends()
        ws.update_cell(row_num, 4, status)
    except Exception:
        pass
    # Grava no CSV (sempre)
    if prefix and variacao:
        _salvar_legend_csv(prefix, variacao, status)
    load_legends.clear()


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
    df["Codigo"] = df["Codigo"].astype(str).str.strip().str.zfill(2).where(
        df["Codigo"].astype(str).str.strip().str.match(r"^\d+$"),
        df["Codigo"].astype(str).str.strip(),
    )
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
# OCR — engine com cache de sessão
# ---------------------------------------------------------------------------

@st.cache_resource
def get_ocr():
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR()


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "time_sel" not in st.session_state:
    st.session_state.time_sel = None


# ---------------------------------------------------------------------------
# Abas
# ---------------------------------------------------------------------------

tab_resumo, tab_time, tab_busca, tab_scanner, tab_pacote, tab_listas, tab_legends = st.tabs(
    ["📊 Resumo", "🏳️ Por Time", "🔍 Busca", "📷 Scanner", "📦 Pacote", "📋 Listas", "⭐ Legends"]
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

    if st.session_state.get("_resumo_selecionado"):
        _sel = st.session_state.pop("_resumo_selecionado")
        st.session_state.time_sel = _sel
        st.info(f"**{pais_label(_sel)}** selecionado — vá para a aba **Por Time** para ver e editar.")

    for _i, (_, _r) in enumerate(stats.iterrows()):
        _pt = _r["Tenho"] / _r["Total"] * 100
        _ck = " ✅" if _r["✅"] else ""
        _pais = _r["Pais"]
        _col_btn, _col_bar = st.columns([2, 3])
        with _col_btn:
            if st.button(
                f"{_r['Seleção']}{_ck}",
                key=f"resumo_{_pais}",
                use_container_width=True,
            ):
                st.session_state["_resumo_selecionado"] = _pais
                st.rerun()
        with _col_bar:
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:8px;height:38px;'>"
                f"<div style='flex:1;background:#E2E8F0;border-radius:99px;height:10px;overflow:hidden;'>"
                f"<div style='background:linear-gradient(90deg,#B8720A,#E8B800);width:{_pt:.0f}%;height:100%;border-radius:99px;'></div>"
                f"</div>"
                f"<span style='font-size:0.76rem;color:#64748B;white-space:nowrap;'>{int(_r['Tenho'])}/{int(_r['Total'])}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # Seções especiais
    st.divider()
    st.subheader("Seções especiais")

    _especiais = [
        ("📖 Introdução",          "_INTRO_",    df[df["Codigo"] == "00"]),
        ("⭐ FWC — Host Countries", "_FWC_HOST_", df[df["Codigo"].isin([f"FWC{i}" for i in range(1, 9)])]),
        ("🏆 FWC — History",       "_FWC_HIST_", df[df["Codigo"].isin([f"FWC{i}" for i in range(9, 20)])]),
        ("🥤 Coca-Cola",           "_CC_",       df[df["Codigo"].str.startswith("CC", na=False)]),
    ]

    for _label, _key_esp, _df_esp in _especiais:
        if _df_esp.empty:
            continue
        _tenho_esp = int(_df_esp["Status"].isin(["tenho", "repetida"]).sum())
        _total_esp = len(_df_esp)
        _pt_esp = _tenho_esp / _total_esp * 100 if _total_esp else 0
        _ck_esp = " ✅" if _tenho_esp == _total_esp else ""
        _col_btn, _col_bar = st.columns([2, 3])
        with _col_btn:
            if st.button(
                f"{_label}{_ck_esp}",
                key=f"resumo_esp_{_key_esp}",
                use_container_width=True,
            ):
                st.session_state.time_sel = _key_esp
                st.info(f"**{_label}** selecionado — vá para a aba **Por Time** para ver e editar.")
        with _col_bar:
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:8px;height:38px;'>"
                f"<div style='flex:1;background:#E2E8F0;border-radius:99px;height:10px;overflow:hidden;'>"
                f"<div style='background:linear-gradient(90deg,#B8720A,#E8B800);width:{_pt_esp:.0f}%;height:100%;border-radius:99px;'></div>"
                f"</div>"
                f"<span style='font-size:0.76rem;color:#64748B;white-space:nowrap;'>{_tenho_esp}/{_total_esp}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )


# ── Por Time ─────────────────────────────────────────────────────────────────
with tab_time:
    df = load_df()
    _excluir_especiais = (
        df["Codigo"].str.startswith("FWC", na=False) |
        df["Codigo"].str.startswith("CC", na=False) |
        (df["Codigo"] == "00")
    )
    def _sem_acento(s):
        return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii").upper()

    paises = sorted(df[~_excluir_especiais]["Pais"].unique(), key=_sem_acento)

    pais_tenho = {
        p: int(df[df["Pais"] == p]["Status"].isin(["tenho", "repetida"]).sum())
        for p in paises
    }

    if st.session_state.time_sel is None:
        # ── Grid de seleção ──────────────────────────────────────────────────
        st.caption("Toque em uma seleção para ver e editar as figurinhas.")

        intro_df = df[df["Codigo"] == "00"]
        intro_tenho = int(intro_df["Status"].isin(["tenho", "repetida"]).sum())
        intro_total = len(intro_df)
        intro_check = " ✅" if intro_tenho == intro_total else ""

        fwc_host_codes = [f"FWC{i}" for i in range(1, 9)]
        fwc_host_df = df[df["Codigo"].isin(fwc_host_codes)]
        fwc_host_tenho = int(fwc_host_df["Status"].isin(["tenho", "repetida"]).sum())
        fwc_host_total = len(fwc_host_df)
        fwc_host_check = " ✅" if fwc_host_tenho == fwc_host_total else ""

        col_intro, col_fwc_host = st.columns(2)
        with col_intro:
            if st.button(
                f"📖 Introdução  {intro_tenho}/{intro_total}{intro_check}",
                use_container_width=True,
                key="card_intro",
            ):
                st.session_state.time_sel = "_INTRO_"
                st.rerun()
        with col_fwc_host:
            if st.button(
                f"⭐ FWC — Host Countries  {fwc_host_tenho}/{fwc_host_total}{fwc_host_check}",
                use_container_width=True,
                key="card_fwc_host",
            ):
                st.session_state.time_sel = "_FWC_HOST_"
                st.rerun()

        st.write("")

        for i in range(0, len(paises), 3):
            chunk = paises[i:i + 3]
            cols_g = st.columns(3)
            for col, pais in zip(cols_g, chunk):
                tenho_p = pais_tenho[pais]
                check = " ✅" if tenho_p == 20 else ""
                flag = BANDEIRAS.get(pais, "")
                with col:
                    if st.button(
                        f"{flag} {pais}  {tenho_p}/20{check}",
                        key=f"card_{pais}",
                        use_container_width=True,
                    ):
                        st.session_state.time_sel = pais
                        st.rerun()

        st.write("")

        fwc_hist_codes = [f"FWC{i}" for i in range(9, 20)]
        fwc_hist_df = df[df["Codigo"].isin(fwc_hist_codes)]
        fwc_hist_tenho = int(fwc_hist_df["Status"].isin(["tenho", "repetida"]).sum())
        fwc_hist_total = len(fwc_hist_df)
        fwc_hist_check = " ✅" if fwc_hist_tenho == fwc_hist_total else ""

        cc_df = df[df["Codigo"].str.startswith("CC", na=False)]
        cc_tenho = int(cc_df["Status"].isin(["tenho", "repetida"]).sum())
        cc_total = len(cc_df)
        cc_check = " ✅" if cc_tenho == cc_total else ""

        col_fwc_hist, col_cc = st.columns(2)
        with col_fwc_hist:
            if st.button(
                f"🏆 FWC — History  {fwc_hist_tenho}/{fwc_hist_total}{fwc_hist_check}",
                use_container_width=True,
                key="card_fwc_hist",
            ):
                st.session_state.time_sel = "_FWC_HIST_"
                st.rerun()
        with col_cc:
            if st.button(
                f"🥤 Coca-Cola  {cc_tenho}/{cc_total}{cc_check}",
                use_container_width=True,
                key="card_cc",
            ):
                st.session_state.time_sel = "_CC_"
                st.rerun()

    else:
        # ── Detalhe do time ──────────────────────────────────────────────────
        escolha = st.session_state.time_sel

        _sequencia = ["_INTRO_", "_FWC_HOST_"] + [nome for _, nome in TEAMS] + ["_FWC_HIST_", "_CC_"]
        _idx_atual = _sequencia.index(escolha) if escolha in _sequencia else -1
        _anterior = _sequencia[_idx_atual - 1] if _idx_atual > 0 else None
        _proximo = _sequencia[_idx_atual + 1] if _idx_atual >= 0 and _idx_atual + 1 < len(_sequencia) else None

        def _label_secao(key: str) -> str:
            especiais = {"_INTRO_": "📖 Introdução", "_FWC_HOST_": "⭐ FWC — Host Countries",
                         "_FWC_HIST_": "🏆 FWC — History", "_CC_": "🥤 Coca-Cola"}
            if key in especiais:
                return especiais[key]
            return f"{BANDEIRAS.get(key, '')} {key}"

        col_voltar, col_ant, col_prox = st.columns([1, 2, 2])
        with col_voltar:
            if st.button("← Lista", key="voltar_time", use_container_width=True):
                st.session_state.time_sel = None
                st.rerun()
        with col_ant:
            if _anterior is not None:
                if st.button(f"← {_label_secao(_anterior)}", key="ant_time", use_container_width=True):
                    st.session_state.time_sel = _anterior
                    st.rerun()
        with col_prox:
            if _proximo is not None:
                if st.button(f"{_label_secao(_proximo)} →", key="prox_time", use_container_width=True):
                    st.session_state.time_sel = _proximo
                    st.rerun()

        if escolha == "_INTRO_":
            time_df = df[df["Codigo"] == "00"].copy()
            st.subheader("📖 Introdução")
        elif escolha == "_FWC_HOST_":
            time_df = df[df["Codigo"].isin([f"FWC{i}" for i in range(1, 9)])].copy()
            st.subheader("⭐ FWC — Host Countries")
        elif escolha == "_FWC_HIST_":
            time_df = df[df["Codigo"].isin([f"FWC{i}" for i in range(9, 20)])].copy()
            st.subheader("🏆 FWC — History")
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

        st.progress(tenho_time / total_time if total_time > 0 else 0.0)
        st.caption(f"{tenho_time}/{total_time} figurinhas")
        if tenho_time == total_time:
            st.success("Time completo! 🏆")

        st.divider()
        st.caption("Toque no ícone para alterar o status de cada figurinha.")

        prefix = f"grid_{escolha}_"
        with st.form(key=f"form_{escolha}"):
            alteracoes_form: dict = {}

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

                        reps_atual = int(fig["Repetidas"])
                        if novo == "repetida":
                            novas_reps = st.number_input(
                                "Qtd",
                                min_value=1,
                                value=max(1, reps_atual),
                                step=1,
                                key=f"reps_{fig['Codigo']}",
                                label_visibility="collapsed",
                            )
                        else:
                            novas_reps = reps_atual

            label = f"💾 Salvar"
            submitted = st.form_submit_button(label, type="primary", use_container_width=True)

        if submitted:
            for chunk in [time_df.iloc[i: i + COLS_GRID] for i in range(0, len(time_df), COLS_GRID)]:
                for _, fig in chunk.iterrows():
                    key = f"{prefix}{fig['Codigo']}"
                    novo = st.session_state.get(key, fig["Status"])
                    reps_atual = int(fig["Repetidas"])
                    novas_reps = int(st.session_state.get(f"reps_{fig['Codigo']}", reps_atual)) if novo == "repetida" else reps_atual
                    if novo != fig["Status"] or (novo == "repetida" and novas_reps != reps_atual):
                        alteracoes_form[int(fig["_row"])] = (novo, novas_reps)

            if alteracoes_form:
                updates = [(row, st_val, reps) for row, (st_val, reps) in alteracoes_form.items()]
                with st.spinner("Salvando..."):
                    salvar(updates)
                df_novo = load_df()
                if escolha == "_INTRO_":
                    time_novo = df_novo[df_novo["Codigo"] == "00"]
                elif escolha == "_FWC_HOST_":
                    time_novo = df_novo[df_novo["Codigo"].isin([f"FWC{i}" for i in range(1, 9)])]
                elif escolha == "_FWC_HIST_":
                    time_novo = df_novo[df_novo["Codigo"].isin([f"FWC{i}" for i in range(9, 20)])]
                elif escolha == "_CC_":
                    time_novo = df_novo[df_novo["Codigo"].str.startswith("CC", na=False)]
                else:
                    time_novo = df_novo[df_novo["Pais"] == escolha]
                if time_novo["Status"].isin(["tenho", "repetida"]).sum() == len(time_novo):
                    st.balloons()
                st.success("Salvo!")
            st.rerun()


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
            encontrados = _extrair_codigos(img, codigos_validos, get_ocr())

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
            c1, c2, c3 = st.columns(3)

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

            with c3:
                if st.button("🔴 Faltante", use_container_width=True, key="scan_falt"):
                    salvar([(int(fig["_row"]), "faltante", 0)])
                    st.success(f"{fig['Codigo']} marcado como **faltante**!")
                    st.rerun()


# ── Pacote ────────────────────────────────────────────────────────────────────
with tab_pacote:
    st.subheader("📦 Adicionar figurinhas")
    st.caption("Digite os códigos (BRA3, BRA 3) ou números sequenciais (182), separados por espaço, vírgula ou linha.")

    entrada = st.text_area(
        "Figurinhas:",
        placeholder="BRA3 BRA5 ARG 2\n182 185 210",
        height=120,
        label_visibility="collapsed",
        key="pacote_entrada",
    )

    if st.button("🔍 Verificar figurinhas", type="primary", use_container_width=True, key="pacote_btn"):
        if not entrada.strip():
            st.error("Nenhuma figurinha digitada.")
        else:
            num_map = build_map()
            df_atual = load_df()
            by_code = df_atual.set_index("Codigo")
            codigos_validos = set(by_code.index)
            status_map = {
                code: (row["Status"], int(row["Repetidas"]), int(row["_row"]))
                for code, row in by_code.iterrows()
            }

            numeros, invalidos = _parsear_entrada_pacote(entrada, num_map, codigos_validos)

            if not numeros and not invalidos:
                st.error("Nenhuma figurinha reconhecida.")
            else:
                novas, ja_coletadas, repetidas_lst, desconhecidos, updates = _classificar_pacote(
                    numeros, num_map, status_map
                )
                st.session_state["pacote_preview"] = (novas, ja_coletadas, repetidas_lst, invalidos, updates)
                st.rerun()

    if "pacote_preview" in st.session_state:
        novas, ja_coletadas, repetidas_lst, invalidos, updates = st.session_state["pacote_preview"]

        st.divider()
        st.write("**Preview — o que será salvo:**")

        if novas:
            st.success(f"🟢 {len(novas)} nova(s) — passam para **tenho**")
            st.code("\n".join(code for _, code in novas), language=None)

        if ja_coletadas:
            st.warning(f"🟡 {len(ja_coletadas)} já coletada(s) — passam para **repetida**")
            st.code("\n".join(code for _, code in ja_coletadas), language=None)

        if repetidas_lst:
            st.warning(f"🟡 {len(repetidas_lst)} repetida(s) — contador incrementado")
            st.code("\n".join(f"{code}  (extras: {qtd})" for _, code, qtd in repetidas_lst), language=None)

        if invalidos:
            st.error(f"⚠️ Não reconhecidos: {', '.join(invalidos)}")

        if updates:
            if st.button("✅ Confirmar e salvar", type="primary", use_container_width=True, key="pacote_confirmar"):
                with st.spinner("Salvando no Google Sheets..."):
                    salvar(updates)
                del st.session_state["pacote_preview"]
                df_total = load_df()
                total_tenho = int(df_total["Status"].isin(["tenho", "repetida"]).sum())
                st.success(f"Salvo! Total no álbum: **{total_tenho}/980** ({total_tenho/980*100:.1f}%)")
                st.rerun()
        else:
            st.info("Nenhuma atualização necessária.")
            del st.session_state["pacote_preview"]


# ── Listas ────────────────────────────────────────────────────────────────────
with tab_listas:
    df = load_df()
    faltantes = df[df["Status"] == "faltante"]
    repetidas = df[df["Status"] == "repetida"]

    opcao_impressao = st.radio(
        "O que imprimir:",
        ["Somente faltantes", "Somente para trocar", "Faltantes + Para trocar"],
        horizontal=True,
    )
    incluir_faltantes = opcao_impressao != "Somente para trocar"
    incluir_trocas = opcao_impressao != "Somente faltantes"

    html_bytes = _html_impressao(faltantes, repetidas, incluir_trocas, incluir_faltantes).encode("utf-8")
    nome_arquivo = f"album_copa2026_{datetime.date.today().strftime('%Y%m%d')}.html"
    _opcao_key = opcao_impressao.replace(" ", "_").lower()
    st.download_button(
        label="🖨️ Baixar para impressão (A4)",
        data=html_bytes,
        file_name=nome_arquivo,
        mime="text/html",
        use_container_width=True,
        key=f"dl_{_opcao_key}",
    )
    st.caption("Abra o arquivo baixado no navegador e pressione Ctrl+P para imprimir.")

    texto_wpp = _texto_whatsapp(faltantes, repetidas, incluir_faltantes, incluir_trocas)
    texto_json = json.dumps(texto_wpp)
    # window.parent.open() contorna o sandbox do iframe e abre no contexto do frame pai.
    # api.whatsapp.com/send?text= abre o seletor de contatos no WhatsApp mobile.
    # key no html garante que o componente é recriado ao mudar a seleção do radio.
    st.iframe(f"""
<script>var WPP_TEXT = {texto_json};</script>
<button onclick="window.parent.open('https://api.whatsapp.com/send?text=' + encodeURIComponent(WPP_TEXT), '_blank')"
  style="width:100%; padding:0.55rem 1rem; font-size:1rem; font-weight:600;
         background:#25D366; color:#FFFFFF; border:none; border-radius:8px; cursor:pointer;">
  💬 Exportar WhatsApp
</button>
<!-- key:{_opcao_key} -->
""", height=52)
    st.caption("Abre o WhatsApp com a lista pronta — escolha o contato para enviar.")

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
        st.caption("Cole as figurinhas que **faltam ao seu amigo** — aceita códigos (BRA3, BRA 3) ou números sequenciais.")

        lista_amigo = st.text_area(
            "Faltantes do amigo:",
            placeholder="BRA3 BRA5 ARG 2\n1 5 12 27 45",
            height=100,
            label_visibility="collapsed",
            key="troca_entrada",
        )

        if st.button("🔍 Ver trocas possíveis", use_container_width=True, key="troca_btn"):
            num_map = build_map()
            codigos_validos = set(num_map.values())
            numeros_amigo, invalidos = _parsear_entrada_pacote(lista_amigo, num_map, codigos_validos)

            if not numeros_amigo:
                st.error("Nenhuma figurinha reconhecida.")
            else:
                if invalidos:
                    st.warning(f"⚠️ Não reconhecidos (ignorados): {', '.join(invalidos)}")
                codigos_faltam_amigo = {num_map[n] for n in numeros_amigo if n in num_map}

                posso_oferecer = repetidas[repetidas["Codigo"].isin(codigos_faltam_amigo)]
                nao_tenho_rep = codigos_faltam_amigo - set(repetidas["Codigo"])
                posso_emprestar = df[
                    df["Codigo"].isin(nao_tenho_rep) & (df["Status"] == "tenho")
                ]

                st.markdown(f"**{len(codigos_faltam_amigo)}** figurinhas na lista do amigo analisadas.")
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
                    st.session_state["troca_wpp_df"] = posso_oferecer

                if not posso_oferecer.empty and "troca_wpp_df" in st.session_state:
                    _wpp_df = st.session_state["troca_wpp_df"]
                    _texto_troca = _texto_whatsapp_trocas(_wpp_df)
                    _texto_troca_json = json.dumps(_texto_troca)
                    st.iframe(f"""
<script>var WPP_TEXT = {_texto_troca_json};</script>
<button onclick="window.parent.open('https://api.whatsapp.com/send?text=' + encodeURIComponent(WPP_TEXT), '_blank')"
  style="width:100%; padding:0.55rem 1rem; font-size:1rem; font-weight:600;
         background:#25D366; color:#FFFFFF; border:none; border-radius:8px; cursor:pointer;">
  💬 Enviar oferta pelo WhatsApp
</button>
""", height=52)
                    st.caption("Abre o WhatsApp com a lista de figurinhas que você pode oferecer.")


# ── Legends ───────────────────────────────────────────────────────────────────
with tab_legends:
    st.subheader("⭐ Extra Stickers — Legends")
    st.caption("Figurinhas especiais que saem aleatoriamente nos pacotes (média: 1 a cada 100 pacotes). Não colam no álbum. Disponíveis em 4 variações.")

    _legends_data = load_legends()

    # Contadores globais
    _total_leg = len(LEGENDS) * len(LEGENDS_VARIAÇÕES)
    _tenho_leg = sum(
        1 for _prefix, _, _ in LEGENDS for _var in LEGENDS_VARIAÇÕES
        if _legends_data.get((_prefix, _var), ("faltante",))[0] in ("tenho", "repetida")
    )
    _pct_leg = _tenho_leg / _total_leg * 100

    st.markdown(f"""
<div style="margin:8px 0 4px;">
  <div style="background:#E2E8F0;border-radius:99px;height:14px;overflow:hidden;">
    <div style="background:linear-gradient(90deg,#B8720A,#E8B800);width:{_pct_leg:.1f}%;height:100%;border-radius:99px;"></div>
  </div>
</div>
<p style="font-size:0.82rem;color:#64748B;margin:2px 0 14px;text-align:right;">
  <strong style="color:#0D1B2A;">{_tenho_leg}</strong> de {_total_leg} variações coletadas
  &nbsp;·&nbsp; <strong style="color:#C8962B;">{_pct_leg:.1f}%</strong>
</p>
""", unsafe_allow_html=True)

    st.divider()

    for _prefix, _pais, _jogador in LEGENDS:
        _flag = BANDEIRAS.get(_pais, "")
        _tenho_p = sum(
            1 for _var in LEGENDS_VARIAÇÕES
            if _legends_data.get((_prefix, _var), ("faltante",))[0] in ("tenho", "repetida")
        )
        _completo = " ✅" if _tenho_p == len(LEGENDS_VARIAÇÕES) else ""

        with st.expander(f"{_flag} **{_jogador}** — {_pais}{_completo}  ({_tenho_p}/{len(LEGENDS_VARIAÇÕES)})"):
            for _i in range(0, len(LEGENDS_VARIAÇÕES), 2):
                _chunk = LEGENDS_VARIAÇÕES[_i:_i + 2]
                _cols = st.columns(2)
                for _col, _var in zip(_cols, _chunk):
                    with _col:
                        _entry = _legends_data.get((_prefix, _var), ("faltante", None))
                        _status, _row_num = _entry
                        _cor_texto, _cor_bg = LEGENDS_COR[_var]
                        _emoji_var = LEGENDS_EMOJI[_var]

                        st.markdown(
                            f"<div style='background:{_cor_bg};border-radius:10px;padding:10px 12px;margin-bottom:6px;'>"
                            f"<div style='font-weight:700;font-size:0.9rem;color:{_cor_texto};'>"
                            f"{_emoji_var} {_var.capitalize()}</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                        _c1, _c2, _c3 = st.columns(3)
                        with _c1:
                            if st.button("🟢", key=f"leg_{_prefix}_{_var}_tenho", use_container_width=True,
                                         help="Tenho", type="primary" if _status == "tenho" else "secondary"):
                                if _row_num:
                                    salvar_legend(_row_num, "tenho", _prefix, _var)
                                st.rerun()
                        with _c2:
                            if st.button("🟡", key=f"leg_{_prefix}_{_var}_rep", use_container_width=True,
                                         help="Repetida", type="primary" if _status == "repetida" else "secondary"):
                                if _row_num:
                                    salvar_legend(_row_num, "repetida", _prefix, _var)
                                st.rerun()
                        with _c3:
                            if st.button("🔴", key=f"leg_{_prefix}_{_var}_falt", use_container_width=True,
                                         help="Faltante", type="primary" if _status == "faltante" else "secondary"):
                                if _row_num:
                                    salvar_legend(_row_num, "faltante", _prefix, _var)
                                st.rerun()
