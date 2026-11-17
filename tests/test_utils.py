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


@pytest.mark.parametrize("colada", [
    "postgresql://u:s@host/db?sslmode=require",           # formato padrão do Neon (falhou no 1º deploy)
    "postgres://u:s@host/db?sslmode=require",
    "postgresql+psycopg://u:s@host/db?sslmode=require",
    "postgresql+psycopg2://u:s@host/db?sslmode=require",
    "postgresql+asyncpg://u:s@host/db?sslmode=require",
    "  'postgresql://u:s@host/db?sslmode=require'\n",
])
def test_url_postgres_e_normalizada(monkeypatch, colada):
    monkeypatch.setenv("DATABASE_URL", colada)
    assert config.url_banco() == "postgresql+psycopg2://u:s@host/db?sslmode=require"


def test_driver_postgres_carregado_esta_instalado(monkeypatch):
    """Teste que teria pegado o D6: o SQLAlchemy precisa carregar um driver que está no requirements.txt."""
    from sqlalchemy.engine import make_url

    monkeypatch.setenv("DATABASE_URL", "postgresql://u:s@host/db?sslmode=require")
    dialeto = make_url(config.url_banco()).get_dialect()
    assert dialeto.driver == "psycopg2"
    dialeto.import_dbapi()  # falha com ModuleNotFoundError se o driver não estiver instalado


def test_url_de_outro_banco_nao_e_alterada():
    assert config.normalizar_url_postgres("sqlite:///x.db") == "sqlite:///x.db"


@pytest.mark.parametrize("plataforma", ["RENDER", "VERCEL"])
def test_producao_exige_banco_e_chave(monkeypatch, plataforma):
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv(plataforma, "true")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        config.url_banco()
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        config.chave_secreta()


def test_links_externos_usam_https_atras_do_proxy(monkeypatch):
    """No Render/Vercel o app recebe HTTP do proxy; os links públicos precisam sair com https://."""
    from agendafacil import create_app
    from agendafacil.extensions import db
    from agendafacil.models import Usuario

    monkeypatch.setenv("RENDER", "true")
    app = create_app({"TESTING": True, "SECRET_KEY": "x", "SQLALCHEMY_DATABASE_URI": "sqlite://",
                      "SESSION_COOKIE_SECURE": False})
    with app.app_context():
        admin = Usuario(nome="Admin", email="a@a.com", perfil="admin")
        admin.definir_senha("123456")
        db.session.add(admin)
        db.session.commit()
        cliente = app.test_client()
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = admin.id
        pagina = cliente.get("/feedback/recebidos", headers={
            "X-Forwarded-Proto": "https", "X-Forwarded-Host": "agendafacil.onrender.com"})
        assert "https://agendafacil.onrender.com/feedback/" in pagina.get_data(as_text=True)
        db.session.remove()
        db.engine.dispose()
