"""
Mostra um resumo do álbum: faltantes, que tenho e repetidas.
Execute sempre que quiser ver o status atual.
"""
import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
from collections import defaultdict

CSV = os.path.join(os.path.dirname(__file__), "album.csv")


def main():
    if not os.path.exists(CSV):
        print("album.csv não encontrado. Execute gerar_album.py primeiro.")
        return

    total = faltante = tenho = repetida = repetidas_extra = 0
    faltantes_por_secao = defaultdict(list)
    repetidas_list = []
    erros = []

    with open(CSV, newline="", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            total += 1
            status = row.get("Status", "").strip().lower()

            if status == "faltante":
                faltante += 1
                faltantes_por_secao[row["Secao"]].append(row["Codigo"])
            elif status == "tenho":
                tenho += 1
            elif status == "repetida":
                repetida += 1
                tenho += 1  # também tenho essa
                try:
                    extra = int(row.get("Repetidas", 0))
                except ValueError:
                    extra = 0
                repetidas_extra += extra
                repetidas_list.append((row["Codigo"], row["Secao"], row["Descricao"], extra))
            else:
                erros.append(f"Linha {i}: status inválido '{status}' (código {row['Codigo']})")

    sep = "-" * 50
    print(sep)
    print("  ÁLBUM PANINI — FIFA WORLD CUP 2026")
    print(sep)
    print(f"  Total de figurinhas : {total}")
    print(f"  Tenho               : {tenho}  ({tenho/total*100:.1f}%)")
    print(f"  Faltantes           : {faltante}  ({faltante/total*100:.1f}%)")
    print(f"  Com repetidas       : {repetida}  (total de cópias extras: {repetidas_extra})")
    print(sep)

    if repetidas_list:
        print("\n  REPETIDAS (para trocar):")
        for cod, sec, desc, extra in sorted(repetidas_list, key=lambda x: x[1]):
            extras_str = f"  +{extra} extra(s)" if extra else ""
            print(f"    {cod:<8}  {sec:<25}  {desc}{extras_str}")

    if faltante > 0:
        print(f"\n  FALTANTES POR SEÇÃO:")
        for secao in sorted(faltantes_por_secao):
            codigos = ", ".join(faltantes_por_secao[secao])
            print(f"    {secao:<28}  {codigos}")

    if erros:
        print(f"\n  ATENÇÃO — {len(erros)} linha(s) com status inválido:")
        for e in erros:
            print(f"    {e}")

    print()


if __name__ == "__main__":
    main()
