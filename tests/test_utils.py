from datetime import date, datetime, time
from decimal import Decimal

import pytest

from agendafacil import config, utils


@pytest.mark.parametrize("entrada,saida", [
    ("11987654321", "(11) 98765-4321"),
    ("1133334444", "(11) 3333-4444"),
    ("123", "123"),
    (None, ""),
])
def test_formatar_telefone(entrada, saida):
    assert utils.formatar_telefone(entrada) == saida


@pytest.mark.parametrize("valor,saida", [
    (Decimal("1234.5"), "R$ 1.234,50"),
    (0, "R$ 0,00"),
    (None, ""),
])
def test_formatar_moeda(valor, saida):
    assert utils.formatar_moeda(valor) == saida


def test_formatar_datas():
    momento = datetime(2030, 1, 7, 9, 5)
    assert utils.formatar_data(momento) == "07/01/2030"
    assert utils.formatar_data_hora(momento) == "07/01/2030 09:05"
    assert utils.formatar_hora(momento) == "09:05"


def test_parse():
    assert utils.parse_data("2030-01-07") == date(2030, 1, 7)
    assert utils.parse_data("07/01/2030") is None
    assert utils.parse_hora("09:30") == time(9, 30)
    assert utils.parse_hora("25:00") is None
    assert utils.parse_int("12") == 12
    assert utils.parse_int("x", 3) == 3


@pytest.mark.parametrize("url,esperado", [
    ("/clientes", "/clientes"),
    ("//site-malicioso.com", None),
    ("https://site-malicioso.com", None),
    ("/\\site-malicioso.com", None),
    (None, None),
])
def test_destino_seguro(url, esperado):
    assert utils.destino_seguro(url) == esperado


def test_url_postgres_e_convertida(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:s@host/db?sslmode=require")
    assert config.url_banco() == "postgresql://u:s@host/db?sslmode=require"


def test_producao_exige_banco_e_chave(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        config.url_banco()
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        config.chave_secreta()
