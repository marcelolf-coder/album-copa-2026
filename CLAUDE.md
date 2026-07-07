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

## App Streamlit (7 abas)
1. **Resumo** — barra de progresso + métricas globais + tabela clicável por seleção + seções especiais clicáveis
2. **Por Time** — grade de figurinhas por seleção com edição inline; times ordenados alfabeticamente sem considerar acentos
3. **Busca** — busca por código (ex: `BRA5`) ou nome do jogador
4. **Scanner** — OCR via câmera (`st.camera_input` + `rapidocr-onnxruntime`); pré-processa a imagem (grayscale → sharpen → contrast 2× → resize 2×), extrai códigos via regex contra lista de prefixos válidos com confiança ≥ 0.5; se detectar mais de um código, exibe `selectbox` para o usuário confirmar
5. **Pacote** — entrada de figurinhas por código (`BRA3`, `BRA 3`) ou número sequencial (`182`), com preview antes de salvar
6. **Listas** — botão imprimir HTML A4 + botão Exportar WhatsApp + subabas faltantes/repetidas/trocas
7. **Legends** — Extra Stickers especiais em 4 variações (🟣 Normal / 🥉 Bronze / 🥈 Prata / 🥇 Ouro), persistidos no Google Sheets

## Aba Resumo — detalhes
- Tabela de times é clicável: click pré-seleciona em `st.session_state.time_sel` e exibe aviso para ir à aba Por Time
- Seções especiais (Introdução, FWC Host, FWC History, Coca-Cola) aparecem em bloco separado abaixo dos times, também clicáveis, navegando para as respectivas seções em Por Time

## Aba Por Time — detalhes
- Grid inicial mostra todas as seleções em **ordem alfabética sem considerar acentos** (ex: África do Sul, Alemanha, Arábia Saudita...)
- Seções especiais (Introdução, FWC Host Countries, FWC History, Coca-Cola) ficam fora do grid alfabético — Introdução e FWC Host no topo, FWC History e Coca-Cola no rodapé
- Ao entrar em uma seleção, as setas ← → navegam na **ordem do álbum** (TEAMS order), não na ordem alfabética do grid
- Todo o conteúdo da aba está envolvido em `@st.fragment` (função `_render_tab_time`) — isso garante que interações com widgets (selectbox de status, botões +/−, salvar, navegar) disparam apenas um **rerun parcial** do fragment, sem resetar a aba ativa. Todos os `st.rerun()` internos usam `scope="fragment"`.

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

## Aba Pacote — detalhes
- Aceita **códigos** (`BRA3`, `BRA 3`) e **números sequenciais** (`182`) no mesmo input, inclusive misturados
- Fluxo em dois passos: **Verificar** → preview categorizado (novas / já coletadas / repetidas / não reconhecidos) → **Confirmar e salvar**
- "Já coletadas" = figurinhas que já eram `tenho` e passarão para `repetida` — o preview avisa antes de sobrescrever
- Parser: `_parsear_entrada_pacote(texto, num_map, codigos_validos)` em `logic.py`
- Aceita também o **formato WhatsApp**: `MEX 🇲🇽: 3, 9, 11` ou `FWC 🏆: 2, 3` — permite colar diretamente a lista exportada pelo app na sub-aba Trocas
- Classificação: `_classificar_pacote(numeros, num_map, status_map)` em `logic.py`

## Aba Scanner — detalhes
- Três botões: 🟢 Tenho / 🟡 Repetida / 🔴 Faltante — permite desfazer um scan errado marcando como faltante

## Aba Legends — detalhes
- 20 jogadores × 4 variações = **80 combinações** rastreadas individualmente
- Variações com cores distintas (definidas em `LEGENDS_COR` e `LEGENDS_EMOJI` em `logic.py`):
  - 🟣 Normal — fundo roxo claro `#EDE9FE`, texto `#6D28D9`
  - 🥉 Bronze — fundo laranja-acastanhado `#FDDCB5`, texto `#7C3A10`
  - 🥈 Prata — fundo cinza claro `#E5E7EB`, texto `#374151`
  - 🥇 Ouro — fundo amarelo claro `#FEF9C3`, texto `#854D0E`
- Card exibe apenas emoji + nome da variação; o botão destacado (primary) indica o status atual
- Botões por variação: 🟢 Tenho / 🟡 Repetida / 🔴 Faltante
- Status persistido em **dois lugares**: aba "Legends" do Google Sheets (criada automaticamente via `get_worksheet_legends()`) + `legends.csv` local (criado automaticamente, no `.gitignore`)
- `load_legends()` tenta Sheets primeiro; se falhar (sem internet/credenciais), usa `legends.csv` como fallback
- `salvar_legend()` grava nos dois sempre que possível
- Barra de progresso global + expander por jogador com bandeira e contador de variações
- Fonte: [paninigroup.com/ExtraStickers](https://www.paninigroup.com/ExtraStickers)

## Aba Listas — detalhes
- Radio de seleção: "Somente faltantes" / "Somente para trocar" / "Faltantes + Para trocar"
- **Baixar para impressão (A4)**: gera HTML para Ctrl+P
- **Exportar WhatsApp**: botão verde que abre o WhatsApp com a lista pronta para enviar
- O `download_button` e o componente HTML do WhatsApp recebem `key` derivado da opção do radio — garante que o widget é recriado ao mudar a seleção, evitando o bug de precisar clicar duas vezes
- Subtab **Trocas**: aceita códigos (`BRA3`, `BRA 3`) ou números sequenciais — mesmo parser do Pacote; mostra apenas figurinhas repetidas que pode oferecer

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

### Formato da mensagem WhatsApp — Trocas (sub-aba Trocas)
Após verificar o que pode oferecer, um botão "Enviar oferta pelo WhatsApp" gera:
```
Figurinhas App - Lista
Eua Méx Can 26

Posso oferecer
FWC 🏆: 2, 3
BRA 🇧🇷: 1, 5
ARG 🇦🇷: 4
```
Usa `_texto_whatsapp_trocas(posso_oferecer)` em `logic.py`. A seção se chama "Posso oferecer" (não "Repetidas") para contextualizar a troca. Resultado persistido em `st.session_state["troca_wpp_df"]` para o botão renderizar após o clique em "Ver trocas possíveis".

### Implementação do botão WhatsApp — lições aprendidas
- `st.link_button` com `wa.me/?text=` não abre seletor de contatos no mobile
- `navigator.share()` dentro de iframe falha: sandboxado
- `postMessage` + `navigator.share()` falha: o gesto do usuário não sobrevive ao round-trip async
- **Solução correta**: `window.parent.open()` chamado **diretamente no `onclick`** do botão HTML — contorna o sandbox do iframe, preserva o gesto do usuário, e funciona em mobile e desktop
- Implementado via `st.iframe()` (substituto de `st.components.v1.html`, depreciado em Streamlit ≥ 1.58)
- URL: `api.whatsapp.com/send?text=` abre o seletor de contatos (melhor que `wa.me/?text=`)
- Texto passado por `json.dumps()` no Python — preserva emojis de bandeira sem encoding quebrado
- Emojis de bandeira de países **funcionam** no Android/iOS; no Windows aparecem como `?` (limitação do Segoe UI Emoji)

## Deploy
- Streamlit Cloud conectado ao repositório GitHub: `marcelolf-coder/album-copa-2026`
- Branch `main` → deploy automático a cada push

### Troubleshooting de deploy — ImportError após push

**Sintoma:** `ImportError: cannot import name 'X' from 'logic'` mesmo com o código correto no GitHub.

**Causa:** o Streamlit Cloud faz hot-reload do `streamlit_app.py` mas mantém o processo Python em memória com o `logic.py` antigo. Funções novas adicionadas ao `logic.py` não ficam visíveis até o processo reiniciar completamente.

**Solução:** Reboot manual no painel do Streamlit Cloud:
1. Acesse `share.streamlit.io`
2. Localize o app `album-copa-2026`
3. Clique em `···` → **Reboot**

**Por que os testes não pegam isso:** os testes unitários verificam lógica de código, não estado de infraestrutura. O problema não estava no código — estava no processo em execução no servidor. São categorias diferentes de validação.

## Testes unitários

Os testes cobrem toda a lógica de negócio em `logic.py` e rodam sem Google Sheets ou Streamlit:

```bash
pytest tests/test_logic.py -v
```

Funções e constantes cobertas: `build_map`, `pais_label`, `_texto_whatsapp`, `_texto_whatsapp_trocas`, `_html_impressao`, `_extrair_codigos`, `_classificar_pacote`, `_formatar_lista_repetidas`, `_parsear_entrada_pacote`, `LEGENDS`/`LEGENDS_VARIAÇÕES`/`LEGENDS_COR`/`LEGENDS_EMOJI` — **81 testes** no total.

**Regras de desenvolvimento — obrigatórias em toda alteração:**
- Avaliar se a mudança introduz lógica testável em `logic.py` — se sim, criar testes unitários antes do commit
- Rodar `pytest tests/test_logic.py -q` e garantir 100% verde antes de qualquer push
- Atualizar este CLAUDE.md refletindo qualquer mudança de comportamento, nova feature, decisão de design ou lição aprendida — sem esperar o usuário pedir
- Novas funções puras devem ir para `logic.py`, nunca para `streamlit_app.py`
- Mudanças puramente visuais (CSS, cores, layout) não exigem testes unitários, mas exigem atualização do CLAUDE.md se afetarem comportamento documentado

## Regras importantes
- Nunca sobrescrever `album.csv` se já existir com dados reais
- Dados reais ficam no `album.csv` e no Google Sheets
- Nunca fazer commit ou push sem autorização explícita do usuário
