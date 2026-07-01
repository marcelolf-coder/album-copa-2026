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
    build_map, pais_label,
    _texto_whatsapp, _html_impressao,
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
# Constantes de UI
# ---------------------------------------------------------------------------

COLS_GRID = 3


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
        alteracoes: dict = {}

        chunks = [time_df.iloc[i: i + COLS_GRID] for i in range(0, len(time_df), COLS_GRID)]
        for chunk in chunks:
            cols = st.columns(COLS_GRID)
            for col_i, (_, fig) in enumerate(chunk.iterrows()):
                with cols[col_i]:
                    key = f"{prefix}{fig['Codigo']}"
                    reps_key = f"reps_{fig['Codigo']}"
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
                        if reps_key not in st.session_state:
                            st.session_state[reps_key] = max(1, reps_atual)
                        qtd = st.session_state[reps_key]
                        c_menos, c_qtd, c_mais = st.columns([1, 1, 1])
                        with c_menos:
                            if st.button("−", key=f"menos_{fig['Codigo']}", use_container_width=True):
                                st.session_state[reps_key] = max(1, qtd - 1)
                                st.rerun()
                        with c_qtd:
                            st.markdown(
                                f"<div style='text-align:center;font-size:0.85rem;padding-top:6px'>"
                                f"{st.session_state[reps_key]}x</div>",
                                unsafe_allow_html=True,
                            )
                        with c_mais:
                            if st.button("+", key=f"mais_{fig['Codigo']}", use_container_width=True):
                                st.session_state[reps_key] = qtd + 1
                                st.rerun()
                        novas_reps = st.session_state[reps_key]
                    else:
                        if reps_key in st.session_state:
                            del st.session_state[reps_key]
                        novas_reps = reps_atual

                    if novo != fig["Status"] or (novo == "repetida" and novas_reps != reps_atual):
                        alteracoes[int(fig["_row"])] = (novo, novas_reps)

        label = f"💾 Salvar {len(alteracoes)} alteração(ões)" if alteracoes else "💾 Salvar"
        if st.button(label, type="primary", use_container_width=True, key="salvar_time", disabled=not alteracoes):
            updates = [(row, st_val, reps) for row, (st_val, reps) in alteracoes.items()]
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
    st.components.v1.html(f"""
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
