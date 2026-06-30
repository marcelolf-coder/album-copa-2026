import numpy as np
import pandas as pd
import pytest
from PIL import Image
from unittest.mock import MagicMock

from logic import (
    TEAMS,
    build_map,
    pais_label,
    _texto_whatsapp,
    _html_impressao,
    _extrair_codigos,
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
