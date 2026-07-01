"""
Lógica de negócio pura — sem dependências de Streamlit ou I/O externo.
Importado por streamlit_app.py e pelos testes unitários.
Versão: 2
"""
import datetime
import re

import pandas as pd

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

STATUS_OPTIONS = ["faltante", "tenho", "repetida"]
STATUS_ICON = {"tenho": "🟢", "repetida": "🟡", "faltante": "🔴"}
STATUS_LABEL = {s: f"{STATUS_ICON[s]} {s}" for s in STATUS_OPTIONS}

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

_FLAG_BY_PREFIX = {prefix: BANDEIRAS.get(nome, "") for prefix, nome in TEAMS}

_CODIGO_RE = re.compile(
    r'\b(FWC|CC|ALG|ARG|AUS|AUT|BEL|BIH|BRA|CAN|CIV|COD|COL|CPV|CRO|CUW|CZE|'
    r'ECU|EGY|ENG|ESP|FRA|GER|GHA|HAI|IRN|IRQ|JOR|JPN|KOR|KSA|MAR|MEX|NED|'
    r'NOR|NZL|PAN|PAR|POR|QAT|RSA|SCO|SEN|SUI|SWE|TUN|TUR|URU|USA|UZB)\s*(\d{1,2})\b',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Mapeamento posição sequencial → código
# ---------------------------------------------------------------------------

def build_map() -> dict:
    """Retorna dict {posição_sequencial: codigo} para as 980 figurinhas."""
    m = {1: "00"}
    for i, code in enumerate(FWC_CODES):
        m[i + 2] = code
    for t_idx, (prefix, _) in enumerate(TEAMS):
        start = 21 + t_idx * 20
        for j in range(1, 21):
            m[start + j - 1] = f"{prefix}{j}"
    return m


# ---------------------------------------------------------------------------
# Formatação
# ---------------------------------------------------------------------------

def pais_label(pais: str) -> str:
    flag = BANDEIRAS.get(pais, "")
    return f"{flag} {pais}" if flag else pais


# ---------------------------------------------------------------------------
# Exportação WhatsApp
# ---------------------------------------------------------------------------

def _texto_whatsapp(faltantes: pd.DataFrame, repetidas: pd.DataFrame,
                    incluir_faltantes: bool, incluir_trocas: bool) -> str:
    linhas = ["Figurinhas App - Lista", "Eua Méx Can 26", ""]

    def _numeros_por_prefix(df_part: pd.DataFrame) -> dict:
        result = {}
        fwc_nums = []
        for _, row in df_part.iterrows():
            codigo = str(row["Codigo"])
            if codigo.startswith("FWC"):
                try:
                    fwc_nums.append(int(codigo[3:]))
                except ValueError:
                    pass
            else:
                m = re.match(r'^([A-Z]+)(\d+)$', codigo)
                if m:
                    pref, num = m.group(1), int(m.group(2))
                    result.setdefault(pref, []).append(num)
        ordered = {}
        if fwc_nums:
            ordered["FWC"] = sorted(fwc_nums)
        for prefix, _ in TEAMS:
            if prefix in result:
                ordered[prefix] = sorted(result[prefix])
        return ordered

    def _linha(pref, nums):
        flag = "🏆" if pref == "FWC" else _FLAG_BY_PREFIX.get(pref, "")
        sep = " " if flag else ""
        return f"{pref}{sep}{flag}: {', '.join(str(n) for n in nums)}"

    if incluir_faltantes and not faltantes.empty:
        linhas.append("Faltantes")
        for pref, nums in _numeros_por_prefix(faltantes).items():
            linhas.append(_linha(pref, nums))
        linhas.append("")

    if incluir_trocas and not repetidas.empty:
        linhas.append("Repetidas")
        for pref, nums in _numeros_por_prefix(repetidas).items():
            linhas.append(_linha(pref, nums))

    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Impressão A4
# ---------------------------------------------------------------------------

def _html_impressao(faltantes: pd.DataFrame, repetidas: pd.DataFrame,
                    incluir_trocas: bool = True, incluir_faltantes: bool = True) -> str:
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

    secao_faltantes = f"""
<h2>&#10060; Figurinhas Faltantes &mdash; {total_f} figurinhas</h2>
<div class="grid">
{grid_falt}
</div>
""" if incluir_faltantes else ""

    page_break = '<div class="page-break"></div>' if incluir_faltantes else ""

    secao_trocas = f"""
{page_break}
<h1>&#9917; Album Copa do Mundo 2026</h1>
<p class="meta">Gerado em {hoje}</p>
<h2>&#128260; Para Trocar &mdash; {total_r} tipos</h2>
<div class="rep-box">{grid_rep}</div>
""" if incluir_trocas else ""

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
{secao_faltantes}
{secao_trocas}
<p class="footer">Abra no navegador e pressione Ctrl+P para imprimir em A4</p>
</body>
</html>"""


# ---------------------------------------------------------------------------
# OCR — pré-processamento e extração de códigos
# ---------------------------------------------------------------------------

def _pre_processar(img):
    import numpy as np
    from PIL import ImageEnhance, ImageFilter
    img = img.convert("L")
    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.resize((img.width * 2, img.height * 2))
    return np.array(img.convert("RGB"))


def _extrair_codigos(foto, codigos_validos: set, ocr) -> list:
    """Extrai códigos de figurinha da imagem usando o engine OCR fornecido."""
    arr = _pre_processar(foto)
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
# Lógica do Pacote
# ---------------------------------------------------------------------------

def _classificar_pacote(numeros: list, num_map: dict, status_map: dict) -> tuple:
    """
    Classifica números de figurinhas do pacote pelo status atual.

    status_map: {codigo: (status, repetidas_atual, row_num)}
    Retorna: (novas, ja_coletadas, repetidas_lst, desconhecidos, updates)
      - novas: [(num, codigo)]
      - ja_coletadas: [(num, codigo)]  — já eram 'tenho', viram 'repetida'
      - repetidas_lst: [(num, codigo, nova_qtd)]
      - desconhecidos: [num]
      - updates: [(row_num, novo_status, novas_reps)]
    """
    novas, ja_coletadas, repetidas_lst, desconhecidos, updates = [], [], [], [], []

    for n in sorted(set(numeros)):
        code = num_map.get(n)
        if not code or code not in status_map:
            desconhecidos.append(n)
            continue
        status, reps_atual, row_num = status_map[code]

        if status == "faltante":
            updates.append((row_num, "tenho", 0))
            novas.append((n, code))
        elif status == "tenho":
            updates.append((row_num, "repetida", 1))
            ja_coletadas.append((n, code))
        else:
            nova_qtd = reps_atual + 1
            updates.append((row_num, "repetida", nova_qtd))
            repetidas_lst.append((n, code, nova_qtd))

    return novas, ja_coletadas, repetidas_lst, desconhecidos, updates


# ---------------------------------------------------------------------------
# Formatação da lista de repetidas com número sequencial
# ---------------------------------------------------------------------------

def _formatar_lista_repetidas(repetidas: pd.DataFrame, num_map_inv: dict) -> str:
    """
    Formata a lista de figurinhas repetidas incluindo o número sequencial.

    num_map_inv: {codigo: posicao_sequencial} — inverso de build_map()
    Retorna string pronta para exibição.
    """
    linhas = []
    for _, fig in repetidas.iterrows():
        codigo = fig["Codigo"]
        extras = int(fig["Repetidas"])
        seq = num_map_inv.get(codigo, "?")
        sufixo = f"  (+{extras} extra{'s' if extras != 1 else ''})" if extras > 0 else ""
        linhas.append(f"#{seq:>4}  {codigo} — {fig['Descricao']} ({pais_label(fig['Pais'])}){sufixo}")
    return "\n".join(linhas)
