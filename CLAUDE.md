# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Album Copa 2026

Gerenciador pessoal de figurinhas do álbum Panini FIFA World Cup 2026.

## O que é
980 figurinhas (48 seleções × 20 + seção FWC introdutória). Cada figurinha tem status: `faltante`, `tenho` ou `repetida`.

## Dependências

```bash
pip install -r requirements.txt
```

Bibliotecas principais: `streamlit`, `gspread`, `google-auth-oauthlib`, `pandas`, `rapidocr-onnxruntime`, `Pillow`, `numpy`, `streamlit-js-eval`.

Python em uso no Windows: `C:\Users\marcelolf\AppData\Local\Programs\Python\Python314\python.exe`

## Como executar

```bash
# Testes unitários (não requerem Google Sheets nem Streamlit)
pytest tests/test_logic.py -v

# App web principal
streamlit run streamlit_app.py

# Entrada de novas figurinhas (por número sequencial do álbum)
python _atualizar_batch.py

# Ver progresso no terminal
python resumo.py

# Gerar lista para impressão
python imprimir.py
```

## Arquitetura

Duas fontes de dados sincronizadas:
- `album.csv` — arquivo local (`Codigo, Secao, Descricao, Status, Repetidas`)
- Google Sheets — ID: `1PvsPLQ_c9jnk8tiSBtG2Hw1FXtQUi8iM376BmZQumjU`

Autenticação via `service_account.json` (local, não versionado) ou secrets do Streamlit Cloud (`GOOGLE_CREDENTIALS` como JSON string). Se `service_account.json` não existir e os secrets não estiverem configurados, a conexão com o Sheets falha silenciosamente — o app funciona apenas com `album.csv`.

## Arquitetura de código

A lógica de negócio pura vive em `logic.py` (sem dependências de Streamlit ou I/O externo). O `streamlit_app.py` importa de lá e contém apenas UI, cache do Streamlit (`@st.cache_resource`, `@st.cache_data`) e acesso ao Google Sheets.

Regra: qualquer função que não precise de `st.*` ou `gspread` deve estar em `logic.py` — isso garante que pode ser testada unitariamente.

## Scripts principais

| Script | Uso |
|---|---|
| `streamlit_app.py` | App web mobile-friendly (6 abas) |
| `_atualizar_batch.py` | Entrada de novas figurinhas por número sequencial |
| `resumo.py` | Relatório CLI de progresso |
| `imprimir.py` | Gera `album_impressao.html` para impressão |
| `gerar_album.py` | Cria `album.csv` (one-time, não sobrescreve) |
| `atualizar_descricoes.py` | Preenche nomes reais dos jogadores |
| `setup_sheet.py` | Setup inicial do Google Sheet |

## App Streamlit (6 abas)
1. **Resumo** — barra de progresso + métricas globais + tabela por seleção
2. **Por Time** — grade de figurinhas por seleção com edição inline; times ordenados alfabeticamente sem considerar acentos
3. **Busca** — busca por código (ex: `BRA5`) ou nome do jogador
4. **Scanner** — OCR via câmera (`st.camera_input` + `rapidocr-onnxruntime`); pré-processa a imagem (grayscale → sharpen → contrast 2× → resize 2×), extrai códigos via regex contra lista de prefixos válidos com confiança ≥ 0.5; se detectar mais de um código, exibe `selectbox` para o usuário confirmar
5. **Pacote** — entrada de figurinhas por número sequencial do álbum
6. **Listas** — botão imprimir HTML A4 + botão Exportar WhatsApp + subabas faltantes/repetidas/trocas

## Aba Por Time — detalhes
- Grid inicial mostra todas as seleções em **ordem alfabética sem considerar acentos** (ex: África do Sul, Alemanha, Arábia Saudita...)
- Seções especiais (Introdução, FWC Host Countries, FWC History, Coca-Cola) ficam fora do grid alfabético — Introdução e FWC Host no topo, FWC History e Coca-Cola no rodapé
- Ao entrar em uma seleção, as setas ← → navegam na **ordem do álbum** (TEAMS order), não na ordem alfabética do grid

### Grid mobile — lição aprendida
Um único `st.columns(3)` para todos os N itens faz o Streamlit empilhar as colunas inteiras no mobile: todos os itens da coluna 0 primeiro, depois coluna 1, depois coluna 2 — quebrando a ordem visual. A solução correta é criar um novo `st.columns(3)` **por linha de 3 itens**:
```python
for i in range(0, len(paises), 3):
    chunk = paises[i:i + 3]
    cols = st.columns(3)
    for col, pais in zip(cols, chunk):
        with col:
            ...
```
Essa regra vale para qualquer grade de itens no app.

## Aba Resumo — detalhes
- Tabela de seleções é clicável: click pré-seleciona o time em `st.session_state.time_sel` via chave `_resumo_selecionado` e exibe aviso pedindo ao usuário para ir para aba Por Time

## Aba Pacote — detalhes
- Fluxo em dois passos: **Verificar** → preview com 4 categorias (novas, já coletadas, repetidas, desconhecidos) → **Confirmar e salvar**
- "Já coletadas" = figurinhas que já eram `tenho` e passarão para `repetida` — o preview avisa antes de sobrescrever
- Lógica de classificação está em `logic.py` → `_classificar_pacote(numeros, num_map, status_map)`

## Aba Scanner — detalhes
- Três botões: 🟢 Tenho / 🟡 Repetida / 🔴 Faltante — permite desfazer um scan errado marcando como faltante

## Aba Listas — detalhes
- Radio de seleção: "Somente faltantes" / "Somente para trocar" / "Faltantes + Para trocar"
- **Baixar para impressão (A4)**: gera HTML para Ctrl+P
- **Exportar WhatsApp**: botão verde que abre o WhatsApp com a lista pronta para enviar
- O `download_button` e o componente HTML do WhatsApp recebem `key` derivado da opção do radio — garante que o widget é recriado ao mudar a seleção, evitando o bug de precisar clicar duas vezes
- Subtab **Para trocar**: lista inclui número sequencial (`#NNN`) de cada figurinha para facilitar comunicação em trocas

### Formato da mensagem WhatsApp
```
Figurinhas App - Lista
Eua Méx Can 26

Faltantes
MEX 🇲🇽: 1, 2, 3
BRA 🇧🇷: 8, 9, 11
FWC 🏆: 1, 2

Repetidas
ARG 🇦🇷: 4, 13, 17
```
Times ordenados conforme a ordem do álbum. FWC usa 🏆, times usam bandeira do país.

### Implementação do botão WhatsApp — lições aprendidas
- `st.link_button` com `wa.me/?text=` não abre seletor de contatos no mobile
- `navigator.share()` dentro de `st.components.v1.html` falha: o iframe é sandboxado
- `postMessage` + `navigator.share()` falha: o gesto do usuário não sobrevive ao round-trip async
- **Solução correta**: `window.parent.open()` chamado **diretamente no `onclick`** do botão HTML — contorna o sandbox do iframe, preserva o gesto do usuário, e funciona em mobile e desktop
- URL: `api.whatsapp.com/send?text=` abre o seletor de contatos (melhor que `wa.me/?text=`)
- Texto passado por `json.dumps()` no Python — preserva emojis de bandeira sem encoding quebrado
- Emojis de bandeira de países **funcionam** no Android/iOS; no Windows aparecem como `?` (limitação do Segoe UI Emoji)

## Deploy
- Streamlit Cloud conectado ao repositório GitHub: `marcelolf-coder/album-copa-2026`
- Branch `main` → deploy automático a cada push

## Testes unitários

Os testes cobrem toda a lógica de negócio em `logic.py` e rodam sem Google Sheets ou Streamlit:

```bash
pytest tests/test_logic.py -v
```

**Regras de desenvolvimento:**
- Toda alteração de código deve ser acompanhada de testes unitários quando a lógica alterada for testável (funções puras em `logic.py`)
- Antes de qualquer push para produção, rodar os testes e garantir que todos passam
- Novas funções puras devem ser adicionadas em `logic.py`, não em `streamlit_app.py`

## Regras importantes
- Nunca sobrescrever `album.csv` se já existir com dados reais
- Dados reais ficam no `album.csv` e no Google Sheets
- Nunca fazer commit ou push sem autorização explícita do usuário
