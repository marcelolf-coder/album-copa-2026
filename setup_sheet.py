"""
Uso único: cria e popula a planilha Google Sheets usando a service account.

Uso:
  python setup_sheet.py <SHEET_ID>

O SHEET_ID está na URL da planilha:
  https://docs.google.com/spreadsheets/d/SHEET_ID/edit
"""
import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) < 2:
        print("Uso: python setup_sheet.py <SHEET_ID>")
        print()
        print("Exemplo:")
        print("  python setup_sheet.py 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms")
        sys.exit(1)

    sheet_id = sys.argv[1].strip()

    sa_path = os.path.join(BASE, "service_account.json")
    if not os.path.exists(sa_path):
        print("ERRO: service_account.json nao encontrado.")
        print(f"Salve o arquivo na pasta: {BASE}")
        sys.exit(1)

    csv_path = os.path.join(BASE, "album.csv")
    if not os.path.exists(csv_path):
        print("ERRO: album.csv nao encontrado. Execute gerar_album.py primeiro.")
        sys.exit(1)

    import gspread
    with open(sa_path) as f:
        creds_info = json.load(f)

    gc = gspread.service_account_from_dict(creds_info)

    print(f"Conectando na planilha {sheet_id}...")
    sh = gc.open_by_key(sheet_id)
    ws = sh.sheet1
    ws.clear()
    ws.update_title("Figurinhas")

    # Carrega CSV
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    header = ["Codigo", "Pais", "Descricao", "Status", "Repetidas", "Observacoes"]
    data = [header] + [
        [r["Codigo"], r["Secao"], r["Descricao"],
         r.get("Status", "faltante"), r.get("Repetidas", "0"), ""]
        for r in rows
    ]

    print(f"Enviando {len(rows)} figurinhas...")
    ws.update(data, "A1")

    # Formataçao
    sid = ws.id
    n = len(data)
    reqs = []

    # Congela cabecalho
    reqs.append({"updateSheetProperties": {
        "properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": 1}},
        "fields": "gridProperties.frozenRowCount"
    }})

    # Largura das colunas
    for i, px in enumerate([75, 150, 120, 95, 85, 160]):
        reqs.append({"updateDimensionProperties": {
            "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
            "properties": {"pixelSize": px}, "fields": "pixelSize"
        }})

    # Altura das linhas de dados
    reqs.append({"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 1, "endIndex": n},
        "properties": {"pixelSize": 20}, "fields": "pixelSize"
    }})

    # Cabecalho azul
    reqs.append({"repeatCell": {
        "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1,
                  "startColumnIndex": 0, "endColumnIndex": 6},
        "cell": {"userEnteredFormat": {
            "backgroundColor": {"red": 0.082, "green": 0.302, "blue": 0.565},
            "textFormat": {"bold": True,
                           "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                           "fontSize": 10},
            "horizontalAlignment": "CENTER"
        }},
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
    }})

    # Dropdown Status
    reqs.append({"setDataValidation": {
        "range": {"sheetId": sid, "startRowIndex": 1, "endRowIndex": n,
                  "startColumnIndex": 3, "endColumnIndex": 4},
        "rule": {
            "condition": {"type": "ONE_OF_LIST", "values": [
                {"userEnteredValue": "faltante"},
                {"userEnteredValue": "tenho"},
                {"userEnteredValue": "repetida"},
            ]},
            "showCustomUi": True, "strict": True,
        }
    }})

    dr = {"sheetId": sid, "startRowIndex": 1, "endRowIndex": n,
          "startColumnIndex": 0, "endColumnIndex": 6}

    # Formatacao condicional: tenho=verde, repetida=amarelo, faltante=rosa
    for i, (val, cor) in enumerate([
        ("tenho",    {"red": 0.714, "green": 0.882, "blue": 0.714}),
        ("repetida", {"red": 1.0,   "green": 0.945, "blue": 0.463}),
        ("faltante", {"red": 1.0,   "green": 0.878, "blue": 0.878}),
    ]):
        reqs.append({"addConditionalFormatRule": {"index": i, "rule": {
            "ranges": [dr],
            "booleanRule": {
                "condition": {"type": "CUSTOM_FORMULA",
                              "values": [{"userEnteredValue": f'=$D2="{val}"'}]},
                "format": {"backgroundColor": cor}
            }
        }}})

    sh.batch_update({"requests": reqs})

    # Salva sheet_id local
    cfg_path = os.path.join(BASE, "sheet_config.json")
    with open(cfg_path, "w") as f:
        json.dump({"sheet_id": sheet_id, "sheet_url": sh.url}, f, indent=2)

    print()
    print("Planilha configurada com sucesso!")
    print(f"URL: {sh.url}")
    print()
    print("Proximos passos:")
    print("  1. Compartilhe a URL acima com seus amigos (Editor)")
    print("  2. Siga o guia de deploy para publicar o app mobile")


if __name__ == "__main__":
    main()
