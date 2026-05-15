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

st.set_page_config(
    page_title="Album Copa 2026",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* Aumenta métricas */
div[data-testid="stMetricValue"] { font-size: 2rem !important; }
/* Compacta colunas do grid */
div[data-testid="column"] { padding: 0 2px !important; }
/* Selectbox menor */
div[data-testid="stSelectbox"] label { font-size: 0.75rem !important; }
div[data-testid="stSelectbox"] div { font-size: 0.75rem !important; }
/* Tabs com scroll em telas pequenas */
div[data-testid="stTabs"] > div:first-child { overflow-x: auto; }
/* Botão primário ocupa largura total */
.stButton > button[kind="primary"] { font-size: 1rem; padding: 0.6rem; }
</style>
""", unsafe_allow_html=True)

STATUS_OPTIONS = ["faltante", "tenho", "repetida"]

PAIS_ISO2 = {
    "México": "mx", "África do Sul": "za", "Coreia do Sul": "kr",
    "Tchéquia": "cz", "Canadá": "ca", "Bósnia e Herzegovina": "ba",
    "Catar": "qa", "Suíça": "ch", "Brasil": "br", "Marrocos": "ma",
    "Haiti": "ht", "Escócia": "gb-sct", "EUA": "us", "Paraguai": "py",
    "Austrália": "au", "Turquia": "tr", "Alemanha": "de", "Curaçao": "cw",
    "Costa do Marfim": "ci", "Equador": "ec", "Países Baixos": "nl",
    "Japão": "jp", "Suécia": "se", "Tunísia": "tn", "Bélgica": "be",
    "Egito": "eg", "Irã": "ir", "Nova Zelândia": "nz", "Espanha": "es",
    "Cabo Verde": "cv", "Arábia Saudita": "sa", "Uruguai": "uy",
    "França": "fr", "Senegal": "sn", "Iraque": "iq", "Noruega": "no",
    "Argentina": "ar", "Argélia": "dz", "Áustria": "at", "Jordânia": "jo",
    "Portugal": "pt", "Congo RD": "cd", "Uzbequistão": "uz",
    "Colômbia": "co", "Inglaterra": "gb-eng", "Croácia": "hr",
    "Gana": "gh", "Panamá": "pa",
}


def pais_label(pais: str) -> str:
    """Texto simples — para selectbox e expander (não suportam HTML)."""
    return pais


def pais_md(pais: str) -> str:
    """HTML com imagem de bandeira via flagcdn.com — para st.markdown(unsafe_allow_html=True)."""
    iso2 = PAIS_ISO2.get(pais, "")
    if not iso2:
        return pais
    img = (f'<img src="https://flagcdn.com/20x15/{iso2}.png" '
           f'style="vertical-align:middle;margin-right:5px;border-radius:2px">')
    return f"{img}{pais}"


def flag_url(pais: str) -> str:
    iso2 = PAIS_ISO2.get(pais, "")
    return f"https://flagcdn.com/20x15/{iso2}.png" if iso2 else ""


# Aliases para nomes populares de países que diferem do nome oficial no álbum
PAIS_ALIAS = {
    "HOLANDA": "Países Baixos",
    "HOLLAND": "Países Baixos",
    "NETHERLANDS": "Países Baixos",
    "PAÍSES BAIXOS": "Países Baixos",
    "COREIA": "Coreia do Sul",
    "KOREA": "Coreia do Sul",
    "ALEMANHA": "Alemanha",
    "GERMANY": "Alemanha",
    "COSTA DO MARFIM": "Costa do Marfim",
    "IVORY COAST": "Costa do Marfim",
    "NOVA ZELÂNDIA": "Nova Zelândia",
    "NEW ZEALAND": "Nova Zelândia",
    "ARÁBIA SAUDITA": "Arábia Saudita",
    "SAUDI ARABIA": "Arábia Saudita",
    "BÓSNIA": "Bósnia e Herzegovina",
    "BOSNIA": "Bósnia e Herzegovina",
    "AFRICA DO SUL": "África do Sul",
    "SOUTH AFRICA": "África do Sul",
    "PAISES BAIXOS": "Países Baixos",
    "ARABIA SAUDITA": "Arábia Saudita",
    "NOVA ZELANDIA": "Nova Zelândia",
    "BOSNIA E HERZEGOVINA": "Bósnia e Herzegovina",
}
STATUS_ICON = {"tenho": "🟢", "repetida": "🟡", "faltante": "🔴"}
STATUS_LABEL = {s: f"{STATUS_ICON[s]} {s}" for s in STATUS_OPTIONS}

COLS_GRID = 3  # colunas no grid de figurinhas


# ---------------------------------------------------------------------------
# Conexão com Google Sheets
# ---------------------------------------------------------------------------

@st.cache_resource
def get_worksheet():
    try:
        creds_info = dict(st.secrets["google_service_account"])
        sheet_id = st.secrets["sheet_id"]
    except Exception:
        # Desenvolvimento local: lê arquivos da pasta do projeto
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
    # Linha real na planilha (linha 1 = cabeçalho, dados começam em 2)
    df["_row"] = range(2, len(df) + 2)
    return df


def salvar(updates: list[tuple[int, str, int]]):
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
    st.markdown(
        f'<div style="background:#d1ecf1;border-left:4px solid #0ea5e9;'
        f'padding:0.6rem 1rem;border-radius:0.4rem;margin-bottom:0.5rem">'
        f'<b>{fig["Codigo"]}</b> — {pais_md(fig["Pais"])} / {fig["Descricao"]}'
        f'</div>',
        unsafe_allow_html=True,
    )

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
    r'\b(FWC|ALG|ARG|AUS|AUT|BEL|BIH|BRA|CAN|CIV|COD|COL|CPV|CRO|CUW|CZE|'
    r'ECU|EGY|ENG|ESP|FRA|GER|GHA|HAI|IRN|IRQ|JOR|JPN|KOR|KSA|MAR|MEX|NED|'
    r'NOR|NZL|PAN|PAR|POR|QAT|RSA|SCO|SEN|SUI|SWE|TUN|TUR|URU|USA|UZB)\s*(\d{1,2})\b',
    re.IGNORECASE,
)


def _pre_processar(img: Image.Image) -> np.ndarray:
    img = img.convert("L")                          # escala de cinza
    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    return np.array(img.convert("RGB"))


def _extrair_codigos(foto: Image.Image, codigos_validos: set) -> list[str]:
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
    return list(dict.fromkeys(encontrados))  # sem duplicatas, mantém ordem


# ---------------------------------------------------------------------------
# Abas
# ---------------------------------------------------------------------------

tab_resumo, tab_time, tab_busca, tab_scanner, tab_listas = st.tabs(
    ["📊 Resumo", "🏳️ Por Time", "🔍 Busca", "📷 Scanner", "📋 Listas"]
)


# ── Resumo ──────────────────────────────────────────────────────────────────
with tab_resumo:
    st.title("⚽ Album Copa 2026")

    if st.button("🔄 Atualizar", use_container_width=True):
        load_df.clear()
        st.rerun()

    df = load_df()
    total = len(df)
    tenho_n = df["Status"].isin(["tenho", "repetida"]).sum()
    faltante_n = (df["Status"] == "faltante").sum()
    repetida_n = (df["Status"] == "repetida").sum()

    st.progress(int(tenho_n) / total)
    st.caption(f"{tenho_n} de {total} ({tenho_n/total*100:.1f}% completo)")

    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 Tenho", int(tenho_n))
    c2.metric("🔴 Faltam", int(faltante_n))
    c3.metric("🟡 Repetidas", int(repetida_n))

    st.divider()
    st.subheader("Por seleção")

    times_df = df[~(df["Codigo"].str.startswith("FWC") | (df["Codigo"] == "00"))]
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
    stats["_flag"] = stats["Pais"].apply(flag_url)

    st.dataframe(
        stats[["_flag", "Pais", "Progresso", "✅"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "_flag": st.column_config.ImageColumn(" ", width="small"),
            "✅": st.column_config.CheckboxColumn(disabled=True),
        },
    )


# ── Por Time ────────────────────────────────────────────────────────────────
with tab_time:
    df = load_df()

    paises = sorted(
        df[~(df["Codigo"].str.startswith("FWC") | (df["Codigo"] == "00"))]["Pais"].unique()
    )
    opcoes = ["⭐ FIFA World Cup 2026 (FWC)"] + list(paises)

    escolha = st.selectbox("Seleção:", opcoes, label_visibility="collapsed")

    if escolha.startswith("⭐"):
        time_df = df[df["Codigo"].str.startswith("FWC") | (df["Codigo"] == "00")].copy()
    else:
        time_df = df[df["Pais"] == escolha].copy()

    time_df = time_df.reset_index(drop=True)

    tenho_time = time_df["Status"].isin(["tenho", "repetida"]).sum()
    st.caption(f"{tenho_time}/{len(time_df)} figurinhas deste time")

    st.divider()
    st.caption("Toque no ícone para alterar o status de cada figurinha.")

    prefix = f"grid_{escolha}_"
    alteracoes: dict[int, tuple[str, int]] = {}

    chunks = [time_df.iloc[i : i + COLS_GRID] for i in range(0, len(time_df), COLS_GRID)]
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
        if st.button(label, type="primary", use_container_width=True):
            updates = [(row, st_val, reps) for row, (st_val, reps) in alteracoes.items()]
            with st.spinner("Salvando..."):
                salvar(updates)
            st.success("Salvo!")
            st.rerun()
    else:
        st.info("Altere o ícone de alguma figurinha para habilitar o salvar.")


# ── Busca ────────────────────────────────────────────────────────────────────
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

        # 1. Tenta código exato
        match_codigo = df[df["Codigo"] == q_upper]

        if not match_codigo.empty:
            resultados = match_codigo
        else:
            # 2. Busca por descrição (nome do jogador)
            mask_desc = df["Descricao"].str.contains(query, case=False, na=False)

            # 3. Busca por país (nome oficial ou alias popular)
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
                f"{r['Codigo']} — {r['Descricao']} ({r['Pais']})"
                for _, r in resultados.iterrows()
            ]
            escolha_idx = st.selectbox(
                f"{len(resultados)} figurinhas encontradas — selecione:",
                range(len(opcoes_label)),
                format_func=lambda i: opcoes_label[i],
            )
            _form_figurinha(resultados.iloc[escolha_idx])


# ── Scanner ──────────────────────────────────────────────────────────────────
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
            st.markdown(
                f'<div style="background:#d1ecf1;border-left:4px solid #0ea5e9;'
                f'padding:0.6rem 1rem;border-radius:0.4rem;margin-bottom:0.5rem">'
                f'<b>{fig["Codigo"]}</b> — {pais_md(fig["Pais"])} / {fig["Descricao"]}'
                f'</div>',
                unsafe_allow_html=True,
            )
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


# ── Listas ───────────────────────────────────────────────────────────────────
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

    sub_falt, sub_rep = st.tabs(["❌ Faltantes", "🔄 Para trocar"])

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
                with st.expander(f"{pais} — {len(grupo)} faltando"):
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
                linhas.append(f"{fig['Codigo']} — {fig['Descricao']} ({fig['Pais']}){sufixo}")

            st.code("\n".join(linhas), language=None)
            st.caption("Copie a lista acima e compartilhe com quem quiser trocar!")
