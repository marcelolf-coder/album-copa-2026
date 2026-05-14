"""
Gerador do álbum Panini Copa do Mundo 2026.
Cria album.csv com todas as 980 figurinhas.
Se o arquivo já existir, não sobrescreve (para não perder anotações).
"""
import csv
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "album.csv")

TEAMS = [
    ("MEX", "México"),
    ("RSA", "África do Sul"),
    ("KOR", "Coreia do Sul"),
    ("CZE", "Tchéquia"),
    ("CAN", "Canadá"),
    ("BIH", "Bósnia e Herzegovina"),
    ("QAT", "Catar"),
    ("SUI", "Suíça"),
    ("BRA", "Brasil"),
    ("MAR", "Marrocos"),
    ("HAI", "Haiti"),
    ("SCO", "Escócia"),
    ("USA", "EUA"),
    ("PAR", "Paraguai"),
    ("AUS", "Austrália"),
    ("TUR", "Turquia"),
    ("GER", "Alemanha"),
    ("CUW", "Curaçao"),
    ("CIV", "Costa do Marfim"),
    ("ECU", "Equador"),
    ("NED", "Países Baixos"),
    ("JPN", "Japão"),
    ("SWE", "Suécia"),
    ("TUN", "Tunísia"),
    ("BEL", "Bélgica"),
    ("EGY", "Egito"),
    ("IRN", "Irã"),
    ("NZL", "Nova Zelândia"),
    ("ESP", "Espanha"),
    ("CPV", "Cabo Verde"),
    ("KSA", "Arábia Saudita"),
    ("URU", "Uruguai"),
    ("FRA", "França"),
    ("SEN", "Senegal"),
    ("IRQ", "Iraque"),
    ("NOR", "Noruega"),
    ("ARG", "Argentina"),
    ("ALG", "Argélia"),
    ("AUT", "Áustria"),
    ("JOR", "Jordânia"),
    ("POR", "Portugal"),
    ("COD", "Congo RD"),
    ("UZB", "Uzbequistão"),
    ("COL", "Colômbia"),
    ("ENG", "Inglaterra"),
    ("CRO", "Croácia"),
    ("GHA", "Gana"),
    ("PAN", "Panamá"),
]

FWC_STICKERS = [
    ("FWC1",  "FIFA World Cup 2026", "Apresentação"),
    ("FWC2",  "FIFA World Cup 2026", "Sede — Estados Unidos"),
    ("FWC3",  "FIFA World Cup 2026", "Sede — Canadá"),
    ("FWC4",  "FIFA World Cup 2026", "Sede — México"),
    ("FWC5",  "FIFA World Cup 2026", "Logo oficial"),
    ("FWC6",  "FIFA World Cup 2026", "Mascote"),
    ("FWC7",  "FIFA World Cup 2026", "Bola oficial"),
    ("FWC8",  "FIFA World Cup 2026", "Troféu"),
    ("FWC9",  "FIFA Museum", "Campeão 1930 — Uruguai"),
    ("FWC10", "FIFA Museum", "Campeão 1934 — Itália"),
    ("FWC11", "FIFA Museum", "Campeão 1938 — Itália"),
    ("FWC12", "FIFA Museum", "Campeão 1950 — Uruguai"),
    ("FWC13", "FIFA Museum", "Campeão 1954 — Alemanha Ocidental"),
    ("FWC14", "FIFA Museum", "Campeão 1958 — Brasil"),
    ("FWC15", "FIFA Museum", "Campeão 1962 — Brasil"),
    ("FWC16", "FIFA Museum", "Campeão 1966 — Inglaterra"),
    ("FWC17", "FIFA Museum", "Campeão 1970 — Brasil"),
    ("FWC18", "FIFA Museum", "Campeão 1974 — Alemanha Ocidental"),
    ("FWC19", "FIFA Museum", "Campeão 1978 — Argentina"),
]


def build_rows():
    rows = []

    # Figurinha 00 — logo Panini
    rows.append(("00", "Introdução", "Logo Panini", "faltante", 0))

    # Seção FWC
    for code, secao, descricao in FWC_STICKERS:
        rows.append((code, secao, descricao, "faltante", 0))

    # Times (20 figurinhas cada)
    for prefix, nome in TEAMS:
        rows.append((f"{prefix}1",  nome, "Escudo do time",  "faltante", 0))
        rows.append((f"{prefix}2",  nome, "Foto da equipe",  "faltante", 0))
        for n in range(3, 21):
            rows.append((f"{prefix}{n}", nome, f"Jogador {n - 2}", "faltante", 0))

    return rows


def main():
    if os.path.exists(OUTPUT):
        print(f"Arquivo já existe: {OUTPUT}")
        print("Para não perder suas anotações, o arquivo NÃO foi sobrescrito.")
        print("Delete-o manualmente se quiser reiniciar do zero.")
        return

    rows = build_rows()
    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Codigo", "Secao", "Descricao", "Status", "Repetidas"])
        writer.writerows(rows)

    print(f"Arquivo criado: {OUTPUT}")
    print(f"Total de figurinhas: {len(rows)}")
    print()
    print("Abra album.csv no Excel ou Google Sheets.")
    print()
    print("Coluna 'Status' — valores aceitos:")
    print("  faltante  = ainda nao tem")
    print("  tenho     = tem 1 copia")
    print("  repetida  = tem mais de 1 copia (preencha 'Repetidas' com a quantidade extra)")


if __name__ == "__main__":
    main()
