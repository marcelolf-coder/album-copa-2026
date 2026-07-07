import numpy as np
import pandas as pd
import pytest
from PIL import Image
from unittest.mock import MagicMock

from logic import (
    TEAMS,
    LEGENDS, LEGENDS_VARIAÇÕES, LEGENDS_COR, LEGENDS_EMOJI,
    build_map,
    pais_label,
    _texto_whatsapp,
    _texto_whatsapp_trocas,
    _html_impressao,
    _extrair_codigos,
    _classificar_pacote,
    _formatar_lista_repetidas,
    _parsear_entrada_pacote,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_df(rows):
    """Cria DataFrame mínimo compatível com as funções de exportação."""
    return pd.DataFrame(rows, columns=["Codigo", "Pais", "Descricao", "Status", "Repetidas"])


FALTANTES_SIMPLES = _make_df([
    ("BRA1", "Brasil", "Alisson", "faltante", 0),
    ("BRA5", "Brasil", "Vini Jr", "faltante", 0),
    ("ARG3", "Argentina", "Messi", "faltante", 0),
    ("FWC2", "FWC", "FWC 2", "faltante", 0),
])

REPETIDAS_SIMPLES = _make_df([
    ("ARG4", "Argentina", "Di Maria", "repetida", 2),
    ("MEX1", "México", "Ochoa", "repetida", 1),
])

VAZIO = _make_df([])


# ---------------------------------------------------------------------------
# build_map
# ---------------------------------------------------------------------------

class TestBuildMap:
    def setup_method(self):
        self.m = build_map()

    def test_posicao_1_e_introducao(self):
        assert self.m[1] == "00"

    def test_posicao_2_e_fwc1(self):
        assert self.m[2] == "FWC1"

    def test_posicao_20_e_fwc19(self):
        assert self.m[20] == "FWC19"

    def test_posicao_21_e_primeiro_time(self):
        primeiro_prefix = TEAMS[0][0]
        assert self.m[21] == f"{primeiro_prefix}1"

    def test_posicao_40_e_ultimo_do_primeiro_time(self):
        primeiro_prefix = TEAMS[0][0]
        assert self.m[40] == f"{primeiro_prefix}20"

    def test_posicao_980_e_ultimo_codigo(self):
        assert 980 in self.m

    def test_total_de_posicoes(self):
        assert len(self.m) == 980

    def test_sem_posicoes_duplicadas(self):
        assert len(set(self.m.values())) == 980


# ---------------------------------------------------------------------------
# pais_label
# ---------------------------------------------------------------------------

class TestPaisLabel:
    def test_pais_com_bandeira(self):
        resultado = pais_label("Brasil")
        assert "🇧🇷" in resultado
        assert "Brasil" in resultado

    def test_pais_sem_bandeira(self):
        resultado = pais_label("Nárnia")
        assert resultado == "Nárnia"

    def test_formato_flag_espaco_nome(self):
        resultado = pais_label("Brasil")
        assert resultado == "🇧🇷 Brasil"


# ---------------------------------------------------------------------------
# _texto_whatsapp
# ---------------------------------------------------------------------------

class TestTextoWhatsapp:
    def test_cabecalho_presente(self):
        txt = _texto_whatsapp(VAZIO, VAZIO, True, True)
        assert "Figurinhas App - Lista" in txt
        assert "Eua Méx Can 26" in txt

    def test_so_faltantes_sem_secao_repetidas(self):
        txt = _texto_whatsapp(FALTANTES_SIMPLES, VAZIO, True, False)
        assert "Faltantes" in txt
        assert "Repetidas" not in txt

    def test_so_trocas_sem_secao_faltantes(self):
        txt = _texto_whatsapp(VAZIO, REPETIDAS_SIMPLES, False, True)
        assert "Faltantes" not in txt
        assert "Repetidas" in txt

    def test_fwc_usa_trofeu(self):
        txt = _texto_whatsapp(FALTANTES_SIMPLES, VAZIO, True, False)
        assert "🏆" in txt

    def test_brasil_usa_bandeira(self):
        txt = _texto_whatsapp(FALTANTES_SIMPLES, VAZIO, True, False)
        assert "🇧🇷" in txt

    def test_ordem_segue_teams_nao_alfabetica(self):
        # MEX vem antes de ARG em TEAMS; alfabeticamente seria ARG antes de MEX
        txt = _texto_whatsapp(REPETIDAS_SIMPLES, VAZIO, True, False)
        pos_mex = txt.find("MEX")
        pos_arg = txt.find("ARG")
        assert pos_mex < pos_arg

    def test_numeros_faltantes_corretos(self):
        txt = _texto_whatsapp(FALTANTES_SIMPLES, VAZIO, True, False)
        assert "BRA 🇧🇷: 1, 5" in txt

    def test_df_vazio_nao_quebra(self):
        txt = _texto_whatsapp(VAZIO, VAZIO, True, True)
        assert isinstance(txt, str)

    def test_ambos_incluidos(self):
        txt = _texto_whatsapp(FALTANTES_SIMPLES, REPETIDAS_SIMPLES, True, True)
        assert "Faltantes" in txt
        assert "Repetidas" in txt


# ---------------------------------------------------------------------------
# _texto_whatsapp_trocas
# ---------------------------------------------------------------------------

OFERTA_SIMPLES = _make_df([
    ("BRA1", "Brasil", "Alisson", "repetida", 2),
    ("MEX3", "México", "Ochoa", "repetida", 1),
    ("FWC2", "FWC", "FWC 2", "repetida", 1),
])


class TestTextoWhatsappTrocas:
    def test_cabecalho_presente(self):
        txt = _texto_whatsapp_trocas(OFERTA_SIMPLES)
        assert "Figurinhas App - Lista" in txt
        assert "Eua Méx Can 26" in txt

    def test_secao_posso_oferecer(self):
        txt = _texto_whatsapp_trocas(OFERTA_SIMPLES)
        assert "Posso oferecer" in txt

    def test_sem_secao_faltantes_ou_repetidas(self):
        txt = _texto_whatsapp_trocas(OFERTA_SIMPLES)
        assert "Faltantes" not in txt
        assert "Repetidas" not in txt

    def test_brasil_com_bandeira(self):
        txt = _texto_whatsapp_trocas(OFERTA_SIMPLES)
        assert "🇧🇷" in txt

    def test_fwc_com_trofeu(self):
        txt = _texto_whatsapp_trocas(OFERTA_SIMPLES)
        assert "🏆" in txt

    def test_ordem_fwc_antes_times(self):
        txt = _texto_whatsapp_trocas(OFERTA_SIMPLES)
        pos_fwc = txt.find("FWC")
        pos_bra = txt.find("BRA")
        assert pos_fwc < pos_bra

    def test_numeros_corretos(self):
        txt = _texto_whatsapp_trocas(OFERTA_SIMPLES)
        assert "BRA 🇧🇷: 1" in txt
        assert "MEX 🇲🇽: 3" in txt

    def test_df_vazio_sem_secao(self):
        txt = _texto_whatsapp_trocas(VAZIO)
        assert "Posso oferecer" not in txt
        assert isinstance(txt, str)


# ---------------------------------------------------------------------------
# _html_impressao
# ---------------------------------------------------------------------------

class TestHtmlImpressao:
    def test_retorna_html_valido(self):
        html = _html_impressao(FALTANTES_SIMPLES, REPETIDAS_SIMPLES)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_sem_faltantes_nao_gera_bloco_faltantes(self):
        html = _html_impressao(FALTANTES_SIMPLES, REPETIDAS_SIMPLES, incluir_faltantes=False)
        assert "Figurinhas Faltantes" not in html

    def test_sem_trocas_nao_gera_bloco_trocas(self):
        html = _html_impressao(FALTANTES_SIMPLES, REPETIDAS_SIMPLES, incluir_trocas=False)
        assert "Para Trocar" not in html

    def test_sem_trocas_sem_page_break(self):
        html = _html_impressao(FALTANTES_SIMPLES, REPETIDAS_SIMPLES, incluir_trocas=False)
        assert '<div class="page-break">' not in html

    def test_contagem_faltantes_no_meta(self):
        html = _html_impressao(FALTANTES_SIMPLES, REPETIDAS_SIMPLES)
        assert f"{len(FALTANTES_SIMPLES)} faltantes" in html

    def test_contagem_repetidas_no_meta(self):
        html = _html_impressao(FALTANTES_SIMPLES, REPETIDAS_SIMPLES)
        assert f"{len(REPETIDAS_SIMPLES)} tipos para trocar" in html

    def test_df_vazio_nao_quebra(self):
        html = _html_impressao(VAZIO, VAZIO)
        assert "Nenhuma figurinha faltando!" in html
        assert "Nenhuma figurinha para trocar." in html


# ---------------------------------------------------------------------------
# _extrair_codigos (OCR mockado)
# ---------------------------------------------------------------------------

def _imagem_branca():
    return Image.fromarray(np.ones((100, 100, 3), dtype=np.uint8) * 255)


def _mock_ocr(resultados):
    """Cria mock de RapidOCR que retorna lista de (bbox, texto, confiança)."""
    ocr = MagicMock()
    ocr.return_value = (resultados, None)
    return ocr


CODIGOS_VALIDOS = {"BRA5", "FWC1", "ARG3", "MEX10"}


class TestExtrairCodigos:
    def test_codigo_valido_retornado(self):
        ocr = _mock_ocr([(None, "BRA5", 0.9)])
        resultado = _extrair_codigos(_imagem_branca(), CODIGOS_VALIDOS, ocr)
        assert resultado == ["BRA5"]

    def test_baixa_confianca_descartada(self):
        ocr = _mock_ocr([(None, "BRA5", 0.4)])
        resultado = _extrair_codigos(_imagem_branca(), CODIGOS_VALIDOS, ocr)
        assert resultado == []

    def test_confianca_exata_05_aceita(self):
        ocr = _mock_ocr([(None, "BRA5", 0.5)])
        resultado = _extrair_codigos(_imagem_branca(), CODIGOS_VALIDOS, ocr)
        assert resultado == ["BRA5"]

    def test_codigo_fora_do_valido_descartado(self):
        ocr = _mock_ocr([(None, "ESP7", 0.95)])
        resultado = _extrair_codigos(_imagem_branca(), CODIGOS_VALIDOS, ocr)
        assert resultado == []

    def test_deduplicacao(self):
        ocr = _mock_ocr([(None, "BRA5", 0.9), (None, "BRA5", 0.8)])
        resultado = _extrair_codigos(_imagem_branca(), CODIGOS_VALIDOS, ocr)
        assert resultado == ["BRA5"]

    def test_multiplos_codigos_preserva_ordem(self):
        ocr = _mock_ocr([(None, "BRA5", 0.9), (None, "ARG3", 0.85)])
        resultado = _extrair_codigos(_imagem_branca(), CODIGOS_VALIDOS, ocr)
        assert resultado == ["BRA5", "ARG3"]

    def test_ocr_sem_resultado_retorna_vazio(self):
        ocr = _mock_ocr(None)
        resultado = _extrair_codigos(_imagem_branca(), CODIGOS_VALIDOS, ocr)
        assert resultado == []

    def test_codigo_com_espaco_normalizado(self):
        # OCR pode retornar "BRA 5" — o código remove espaços antes do regex
        ocr = _mock_ocr([(None, "BRA 5", 0.9)])
        resultado = _extrair_codigos(_imagem_branca(), CODIGOS_VALIDOS, ocr)
        assert resultado == ["BRA5"]

    def test_codigo_minusculo_normalizado(self):
        ocr = _mock_ocr([(None, "bra5", 0.9)])
        resultado = _extrair_codigos(_imagem_branca(), CODIGOS_VALIDOS, ocr)
        assert resultado == ["BRA5"]


# ---------------------------------------------------------------------------
# _parsear_entrada_pacote
# ---------------------------------------------------------------------------

class TestParsearEntradaPacote:
    def setup_method(self):
        self.num_map = build_map()
        self.codigos_validos = set(self.num_map.values())

    def _parse(self, texto):
        return _parsear_entrada_pacote(texto, self.num_map, self.codigos_validos)

    def test_numero_sequencial(self):
        nums, inv = self._parse("182")
        assert 182 in nums
        assert inv == []

    def test_codigo_sem_espaco(self):
        nums, inv = self._parse("BRA3")
        seq = next(k for k, v in self.num_map.items() if v == "BRA3")
        assert seq in nums
        assert inv == []

    def test_codigo_com_espaco(self):
        # "BRA 3" deve resolver igual a "BRA3"
        nums_sem, _ = self._parse("BRA3")
        nums_com, inv = self._parse("BRA 3")
        assert nums_sem == nums_com
        assert inv == []

    def test_multiplos_formatos_mistos(self):
        nums, inv = self._parse("BRA3 182 ARG 5")
        assert len(nums) == 3
        assert inv == []

    def test_token_invalido(self):
        nums, inv = self._parse("XPTO99")
        assert nums == []
        assert "XPTO99" in inv

    def test_virgula_como_separador(self):
        nums, inv = self._parse("BRA3,BRA5")
        assert len(nums) == 2
        assert inv == []

    def test_entrada_vazia(self):
        nums, inv = self._parse("")
        assert nums == []
        assert inv == []

    def test_minusculo_aceito(self):
        nums, inv = self._parse("bra3")
        assert len(nums) == 1
        assert inv == []

    def test_formato_whatsapp_linha_unica(self):
        # "MEX 🇲🇽: 3, 9, 11" deve resolver BRA3, BRA9, BRA11
        nums, inv = self._parse("MEX 🇲🇽: 3, 9, 11")
        codigos = {self.num_map[n] for n in nums}
        assert "MEX3" in codigos
        assert "MEX9" in codigos
        assert "MEX11" in codigos
        assert inv == []

    def test_formato_whatsapp_fwc(self):
        nums, inv = self._parse("FWC 🏆: 2, 3, 4")
        codigos = {self.num_map[n] for n in nums}
        assert "FWC2" in codigos
        assert "FWC3" in codigos
        assert "FWC4" in codigos
        assert inv == []

    def test_formato_whatsapp_multiplas_linhas(self):
        entrada = "MEX 🇲🇽: 3, 9\nBRA 🇧🇷: 1, 5"
        nums, inv = self._parse(entrada)
        codigos = {self.num_map[n] for n in nums}
        assert "MEX3" in codigos
        assert "MEX9" in codigos
        assert "BRA1" in codigos
        assert "BRA5" in codigos
        assert inv == []

    def test_formato_whatsapp_ignora_cabecalho(self):
        # Linhas de cabeçalho ("Figurinhas App", "Faltantes") devem ir para invalidos
        # mas os dados válidos devem ser extraídos
        entrada = "Faltantes\nBRA 🇧🇷: 1, 5"
        nums, inv = self._parse(entrada)
        codigos = {self.num_map[n] for n in nums}
        assert "BRA1" in codigos
        assert "BRA5" in codigos

    def test_formato_whatsapp_misturado_com_codigos_soltos(self):
        entrada = "MEX 🇲🇽: 3, 9\nBRA5"
        nums, inv = self._parse(entrada)
        codigos = {self.num_map[n] for n in nums}
        assert "MEX3" in codigos
        assert "BRA5" in codigos
        assert inv == []


# ---------------------------------------------------------------------------
# _classificar_pacote
# ---------------------------------------------------------------------------

def _status_map(*entries):
    """Helper: cria status_map {codigo: (status, reps, row_num)}."""
    return {code: (status, reps, row) for code, status, reps, row in entries}


class TestClassificarPacote:
    def setup_method(self):
        self.num_map = {1: "BRA1", 2: "BRA2", 3: "ARG1", 99: "MEX1"}

    def test_faltante_vira_tenho(self):
        sm = _status_map(("BRA1", "faltante", 0, 10))
        novas, ja, reps, desc, updates = _classificar_pacote([1], self.num_map, sm)
        assert novas == [(1, "BRA1")]
        assert updates == [(10, "tenho", 0)]
        assert ja == [] and reps == [] and desc == []

    def test_tenho_vira_repetida_1(self):
        sm = _status_map(("BRA1", "tenho", 0, 10))
        novas, ja, reps, desc, updates = _classificar_pacote([1], self.num_map, sm)
        assert ja == [(1, "BRA1")]
        assert updates == [(10, "repetida", 1)]
        assert novas == [] and reps == []

    def test_repetida_incrementa(self):
        sm = _status_map(("BRA1", "repetida", 3, 10))
        novas, ja, reps, desc, updates = _classificar_pacote([1], self.num_map, sm)
        assert reps == [(1, "BRA1", 4)]
        assert updates == [(10, "repetida", 4)]

    def test_numero_desconhecido(self):
        sm = _status_map(("BRA1", "faltante", 0, 10))
        novas, ja, reps, desc, updates = _classificar_pacote([999], self.num_map, sm)
        assert desc == [999]
        assert updates == []

    def test_duplicatas_no_input_processadas_uma_vez(self):
        sm = _status_map(("BRA1", "faltante", 0, 10))
        novas, ja, reps, desc, updates = _classificar_pacote([1, 1, 1], self.num_map, sm)
        assert len(novas) == 1
        assert len(updates) == 1

    def test_multiplos_numeros_mistos(self):
        sm = _status_map(
            ("BRA1", "faltante", 0, 10),
            ("BRA2", "tenho", 0, 11),
            ("ARG1", "repetida", 2, 12),
        )
        novas, ja, reps, desc, updates = _classificar_pacote([1, 2, 3, 50], self.num_map, sm)
        assert len(novas) == 1
        assert len(ja) == 1
        assert len(reps) == 1
        assert desc == [50]
        assert len(updates) == 3

    def test_saida_ordenada_por_numero(self):
        sm = _status_map(
            ("BRA2", "faltante", 0, 11),
            ("BRA1", "faltante", 0, 10),
        )
        novas, _, _, _, _ = _classificar_pacote([2, 1], self.num_map, sm)
        assert [n for n, _ in novas] == [1, 2]


# ---------------------------------------------------------------------------
# _formatar_lista_repetidas
# ---------------------------------------------------------------------------

class TestFormatarListaRepetidas:
    def setup_method(self):
        num_map = build_map()
        self.num_map_inv = {v: k for k, v in num_map.items()}

    def _rep_df(self, rows):
        return pd.DataFrame(rows, columns=["Codigo", "Pais", "Descricao", "Status", "Repetidas"])

    def test_formato_basico(self):
        df = self._rep_df([("BRA1", "Brasil", "Alisson", "repetida", 2)])
        resultado = _formatar_lista_repetidas(df, self.num_map_inv)
        assert "BRA1" in resultado
        assert "Alisson" in resultado
        assert "+2 extras" in resultado

    def test_numero_sequencial_presente(self):
        df = self._rep_df([("BRA1", "Brasil", "Alisson", "repetida", 1)])
        resultado = _formatar_lista_repetidas(df, self.num_map_inv)
        seq = self.num_map_inv.get("BRA1")
        assert f"#{seq:>4}" in resultado

    def test_singular_extra(self):
        df = self._rep_df([("BRA1", "Brasil", "Alisson", "repetida", 1)])
        resultado = _formatar_lista_repetidas(df, self.num_map_inv)
        assert "+1 extra)" in resultado

    def test_plural_extras(self):
        df = self._rep_df([("BRA1", "Brasil", "Alisson", "repetida", 3)])
        resultado = _formatar_lista_repetidas(df, self.num_map_inv)
        assert "+3 extras)" in resultado

    def test_codigo_sem_sequencial_mostra_interrogacao(self):
        df = self._rep_df([("XPTO1", "Brasil", "Jogador", "repetida", 1)])
        resultado = _formatar_lista_repetidas(df, self.num_map_inv)
        assert "#   ?" in resultado

    def test_multiplas_linhas(self):
        df = self._rep_df([
            ("BRA1", "Brasil", "Alisson", "repetida", 1),
            ("ARG3", "Argentina", "Messi", "repetida", 2),
        ])
        resultado = _formatar_lista_repetidas(df, self.num_map_inv)
        assert resultado.count("\n") == 1


# ---------------------------------------------------------------------------
# Legends — constantes e integridade dos dados
# ---------------------------------------------------------------------------

class TestLegendsConstantes:
    def test_total_de_jogadores(self):
        assert len(LEGENDS) == 20

    def test_total_de_variacoes(self):
        assert len(LEGENDS_VARIAÇÕES) == 4

    def test_variacoes_corretas(self):
        assert LEGENDS_VARIAÇÕES == ["normal", "bronze", "prata", "ouro"]

    def test_todos_prefixos_unicos(self):
        prefixos = [p for p, _, _ in LEGENDS]
        assert len(prefixos) == len(set(prefixos))

    def test_todos_jogadores_unicos(self):
        jogadores = [j for _, _, j in LEGENDS]
        assert len(jogadores) == len(set(jogadores))

    def test_cor_definida_para_todas_variacoes(self):
        for var in LEGENDS_VARIAÇÕES:
            assert var in LEGENDS_COR
            cor_texto, cor_bg = LEGENDS_COR[var]
            assert cor_texto.startswith("#")
            assert cor_bg.startswith("#")

    def test_emoji_definido_para_todas_variacoes(self):
        for var in LEGENDS_VARIAÇÕES:
            assert var in LEGENDS_EMOJI
            assert len(LEGENDS_EMOJI[var]) > 0

    def test_normal_usa_roxo(self):
        cor_texto, cor_bg = LEGENDS_COR["normal"]
        # roxo — componente R do hex deve ser menor que B (característica do roxo)
        assert "6D28D9" in cor_texto or "EDE9FE" in cor_bg

    def test_prefixos_pertencem_a_teams(self):
        teams_prefixos = {p for p, _ in TEAMS}
        for prefix, _, _ in LEGENDS:
            assert prefix in teams_prefixos, f"{prefix} não está em TEAMS"

    def test_paises_tem_bandeira(self):
        from logic import BANDEIRAS
        for _, pais, _ in LEGENDS:
            assert pais in BANDEIRAS, f"{pais} não tem bandeira em BANDEIRAS"

    def test_total_combinacoes(self):
        # 20 jogadores × 4 variações = 80 combinações únicas
        combinacoes = {(p, v) for p, _, _ in LEGENDS for v in LEGENDS_VARIAÇÕES}
        assert len(combinacoes) == 80
