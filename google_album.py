"""
Integração com Google Sheets.

Uso:
  python google_album.py criar    — Cria planilha no Google Drive (só uma vez)
  python google_album.py baixar   — Baixa dados do Sheet para album.csv
  python google_album.py enviar   — Envia status do album.csv para o Sheet
  python google_album.py url      — Mostra o link da planilha
"""
import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "album.csv")
CREDS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")
CONFIG_PATH = os.path.join(BASE_DIR, "sheet_config.json")

SHEET_NAME = "Álbum Panini - Copa do Mundo 2026"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def check_credentials():
    if not os.path.exists(CREDS_PATH):
        print("ERRO: credentials.json não encontrado.")
        print()
        print("Passos para configurar (5 min):")
        print("  1. Acesse https://console.cloud.google.com/")
        print("  2. Crie ou selecione um projeto")
        print("  3. Menu lateral > APIs > Biblioteca:")
        print("     - Ative 'Google Sheets API'")
        print("     - Ative 'Google Drive API'")
        print("  4. Menu lateral > APIs > Credenciais:")
        print("     - Clique 'Criar credenciais' > 'ID do cliente OAuth 2.0'")
        print("     - Tipo: Aplicativo para computador")
        print("     - Baixe o JSON e renomeie para 'credentials.json'")
        print(f"     - Salve na pasta: {BASE_DIR}")
        print()
        print("  Na primeira execução, o navegador abrirá para autorizar o acesso.")
        sys.exit(1)


def get_client():
    import gspread
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    check_credentials()

    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            print("Abrindo navegador para autorizar o acesso ao Google...")
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return gspread.Client(auth=creds)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_csv():
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save_csv(rows):
    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Codigo", "Secao", "Descricao", "Status", "Repetidas"])
        writer.writeheader()
        writer.writerows(rows)


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


def require_sheet_id():
    cfg = load_config()
    if not cfg.get("sheet_id"):
        print("ERRO: planilha não configurada.")
        print("Execute primeiro: python google_album.py criar")
        sys.exit(1)
    return cfg["sheet_id"]


# ---------------------------------------------------------------------------
# Comando: criar
# ---------------------------------------------------------------------------

def criar():
    gc = get_client()
    rows = load_csv()

    print(f"Criando '{SHEET_NAME}' no Google Drive...")
    sh = gc.create(SHEET_NAME)
    ws = sh.sheet1
    ws.update_title("Figurinhas")

    # Build rows
    header = ["Codigo", "País", "Descrição", "Status", "Repetidas", "Observações"]
    data = [header] + [
        [r["Codigo"], r["Secao"], r["Descricao"], r.get("Status", "faltante"), r.get("Repetidas", "0"), ""]
        for r in rows
    ]

    print(f"Enviando {len(rows)} figurinhas...")
    ws.update(data, "A1")

    _apply_formatting(sh, ws, n_rows=len(data))

    cfg = load_config()
    cfg["sheet_id"] = sh.id
    cfg["sheet_url"] = sh.url
    save_config(cfg)

    print()
    print("Planilha criada!")
    print(f"Link: {sh.url}")
    print()
    print("Compartilhe esse link:")
    print("  No Google Sheets, clique 'Compartilhar' (canto superior direito)")
    print("  > 'Qualquer pessoa com o link' > 'Editor' > Copiar link")


def _apply_formatting(sh, ws, n_rows):
    sid = ws.id
    reqs = []

    # Freeze header
    reqs.append({"updateSheetProperties": {
        "properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": 1}},
        "fields": "gridProperties.frozenRowCount"
    }})

    # Column widths: Codigo, País, Descrição, Status, Repetidas, Observações
    for i, px in enumerate([75, 150, 120, 95, 85, 160]):
        reqs.append({"updateDimensionProperties": {
            "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
            "properties": {"pixelSize": px},
            "fields": "pixelSize"
        }})

    # Row height (compact)
    reqs.append({"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 1, "endIndex": n_rows},
        "properties": {"pixelSize": 20},
        "fields": "pixelSize"
    }})

    # Header style
    reqs.append({"repeatCell": {
        "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 6},
        "cell": {"userEnteredFormat": {
            "backgroundColor": {"red": 0.082, "green": 0.302, "blue": 0.565},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 10},
            "horizontalAlignment": "CENTER"
        }},
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
    }})

    # Data validation: Status dropdown
    reqs.append({"setDataValidation": {
        "range": {"sheetId": sid, "startRowIndex": 1, "endRowIndex": n_rows, "startColumnIndex": 3, "endColumnIndex": 4},
        "rule": {
            "condition": {"type": "ONE_OF_LIST", "values": [
                {"userEnteredValue": "faltante"},
                {"userEnteredValue": "tenho"},
                {"userEnteredValue": "repetida"},
            ]},
            "showCustomUi": True,
            "strict": True,
        }
    }})

    data_range = {"sheetId": sid, "startRowIndex": 1, "endRowIndex": n_rows, "startColumnIndex": 0, "endColumnIndex": 6}

    # Conditional formatting: tenho → green
    reqs.append({"addConditionalFormatRule": {"index": 0, "rule": {
        "ranges": [data_range],
        "booleanRule": {
            "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": '=$D2="tenho"'}]},
            "format": {"backgroundColor": {"red": 0.714, "green": 0.882, "blue": 0.714}}
        }
    }}})

    # Conditional formatting: repetida → yellow
    reqs.append({"addConditionalFormatRule": {"index": 1, "rule": {
        "ranges": [data_range],
        "booleanRule": {
            "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": '=$D2="repetida"'}]},
            "format": {"backgroundColor": {"red": 1.0, "green": 0.945, "blue": 0.463}}
        }
    }}})

    # Conditional formatting: faltante → light red
    reqs.append({"addConditionalFormatRule": {"index": 2, "rule": {
        "ranges": [data_range],
        "booleanRule": {
            "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": '=$D2="faltante"'}]},
            "format": {"backgroundColor": {"red": 1.0, "green": 0.878, "blue": 0.878}}
        }
    }}})

    sh.batch_update({"requests": reqs})


# ---------------------------------------------------------------------------
# Comando: baixar
# ---------------------------------------------------------------------------

def baixar():
    gc = get_client()
    sheet_id = require_sheet_id()

    sh = gc.open_by_key(sheet_id)
    ws = sh.sheet1

    print("Baixando dados do Google Sheets...")
    all_rows = ws.get_all_records()

    rows = []
    for r in all_rows:
        status = str(r.get("Status", "faltante")).strip().lower()
        if status not in ("faltante", "tenho", "repetida"):
            status = "faltante"
        rows.append({
            "Codigo": str(r.get("Codigo", "")),
            "Secao": str(r.get("País", "")),
            "Descricao": str(r.get("Descrição", "")),
            "Status": status,
            "Repetidas": str(r.get("Repetidas", "0")),
        })

    save_csv(rows)

    total = len(rows)
    tenho = sum(1 for r in rows if r["Status"] in ("tenho", "repetida"))
    faltante = total - tenho
    print(f"Salvo em album.csv | Total: {total} | Tenho: {tenho} ({tenho/total*100:.1f}%) | Faltantes: {faltante}")


# ---------------------------------------------------------------------------
# Comando: enviar
# ---------------------------------------------------------------------------

def enviar():
    gc = get_client()
    sheet_id = require_sheet_id()
    rows = load_csv()

    sh = gc.open_by_key(sheet_id)
    ws = sh.sheet1

    print(f"Enviando status de {len(rows)} figurinhas...")
    status_data = [[r.get("Status", "faltante"), r.get("Repetidas", "0")] for r in rows]
    ws.update(status_data, f"D2:E{len(rows) + 1}")
    print("Enviado com sucesso!")


# ---------------------------------------------------------------------------
# Comando: url
# ---------------------------------------------------------------------------

def mostrar_url():
    cfg = load_config()
    url = cfg.get("sheet_url")
    if url:
        print(f"Link da planilha: {url}")
    else:
        print("Planilha não configurada. Execute: python google_album.py criar")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cmds = {"criar": criar, "baixar": baixar, "enviar": enviar, "url": mostrar_url}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print("Uso: python google_album.py [criar|baixar|enviar|url]")
        print()
        print("  criar    Cria a planilha no Google Drive (executar só uma vez)")
        print("  baixar   Baixa os dados do Sheet para album.csv")
        print("  enviar   Envia o status do album.csv para o Sheet")
        print("  url      Mostra o link da planilha")
        sys.exit(0)
    cmds[sys.argv[1]]()
