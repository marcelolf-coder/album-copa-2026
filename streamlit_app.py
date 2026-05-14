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
import json
import os

import gspread
import pandas as pd
import streamlit as st

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
STATUS_ICON = {"tenho": "🟢", "repetida": "🟡", "faltante": "🔴"}
STATUS_LABEL = {s: f"{STATUS_ICON[s]} {s}" for s in STATUS_OPTIONS}

COLS_GRID = 4  # colunas no grid de figurinhas


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


# ---------------------------------------------------------------------------
# Abas
# ---------------------------------------------------------------------------

tab_resumo, tab_time, tab_busca, tab_listas = st.tabs(
    ["📊 Resumo", "🏳️ Por Time", "🔍 Busca", "📋 Listas"]
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

    st.dataframe(
        stats[["Pais", "Progresso", "✅"]],
        use_container_width=True,
        hide_index=True,
        column_config={"✅": st.column_config.CheckboxColumn(disabled=True)},
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

    # Progresso do time
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


# ── Busca Rápida ─────────────────────────────────────────────────────────────
with tab_busca:
    st.subheader("Atualizar figurinha")
    st.caption("Digite o código (ex: BRA5, FWC3, ARG1) e marque o status.")

    df = load_df()

    codigo = st.text_input(
        "Código",
        placeholder="BRA5",
        max_chars=8,
        label_visibility="collapsed",
    ).strip().upper()

    if codigo:
        match = df[df["Codigo"] == codigo]
        if match.empty:
            st.error(f"Código **{codigo}** não encontrado. Verifique o código no álbum.")
        else:
            fig = match.iloc[0]
            st.info(f"**{fig['Codigo']}** — {fig['Pais']} / {fig['Descricao']}")

            novo_status = st.radio(
                "Status:",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(fig["Status"]),
                horizontal=True,
                format_func=lambda s: STATUS_LABEL[s],
            )

            novas_reps = int(fig["Repetidas"])
            if novo_status == "repetida":
                novas_reps = st.number_input(
                    "Cópias extras (para troca):",
                    min_value=1,
                    value=max(1, novas_reps),
                    step=1,
                )

            if st.button("✅ Salvar", type="primary", use_container_width=True):
                with st.spinner("Salvando..."):
                    salvar([(int(fig["_row"]), novo_status, int(novas_reps))])
                st.success(f"**{codigo}** → {STATUS_LABEL[novo_status]}")
                st.rerun()


# ── Listas ───────────────────────────────────────────────────────────────────
with tab_listas:
    df = load_df()

    sub_falt, sub_rep = st.tabs(["❌ Faltantes", "🔄 Para trocar"])

    with sub_falt:
        faltantes = df[df["Status"] == "faltante"]
        st.caption(f"{len(faltantes)} figurinhas faltando")

        if faltantes.empty:
            st.success("Album completo! 🏆")
        else:
            for pais, grupo in faltantes.groupby("Pais", sort=True):
                codigos = ", ".join(grupo["Codigo"].astype(str).tolist())
                with st.expander(f"{pais} — {len(grupo)} faltando"):
                    st.code(codigos, language=None)

    with sub_rep:
        repetidas = df[df["Status"] == "repetida"]
        st.caption(f"{len(repetidas)} tipos de figurinhas repetidas")

        if repetidas.empty:
            st.info("Nenhuma repetida ainda.")
        else:
            linhas = []
            for _, fig in repetidas.iterrows():
                extras = int(fig["Repetidas"])
                sufixo = f"  (+{extras} extra{'s' if extras != 1 else ''})" if extras > 0 else ""
                linhas.append(f"{fig['Codigo']} — {fig['Pais']}{sufixo}")

            st.code("\n".join(linhas), language=None)
            st.caption("Copie a lista acima e compartilhe com quem quiser trocar!")
