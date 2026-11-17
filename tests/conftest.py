import os
import re
from datetime import datetime
from decimal import Decimal

import pytest

from agendafacil import create_app
from agendafacil.extensions import db as _db
from agendafacil.models import Agendamento, Cliente, Profissional, Servico, Usuario

# 07/01/2030 é uma segunda-feira: data futura e em dia de funcionamento
SEGUNDA = "2030-01-07"
DOMINGO = "2030-01-06"
REFERENCIA = datetime(2030, 1, 1, 9, 0)  # "agora" usado nos testes de unidade


@pytest.fixture
def app():
    # Por padrão usa SQLite em memória. Para rodar contra PostgreSQL (ex.: um branch de teste no Neon):
    #   TEST_DATABASE_URL=postgresql://... pytest      (ATENÇÃO: apaga as tabelas ao final de cada teste)
    url = os.environ.get("TEST_DATABASE_URL", "sqlite://").replace("postgres://", "postgresql://", 1)
    app = create_app({"TESTING": True, "SECRET_KEY": "teste", "SQLALCHEMY_DATABASE_URI": url,
                      "CADASTRO_ABERTO": True})
    with app.app_context():
        yield app
        _db.session.remove()
        _db.drop_all()
        _db.engine.dispose()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def client(app):
    return app.test_client()


def csrf(client) -> str:
    """Garante que existe token CSRF na sessão e o devolve."""
    with client.session_transaction() as sessao:
        if "_csrf" not in sessao:
            sessao["_csrf"] = "token-de-teste"
        return sessao["_csrf"]


def post(client, url, dados=None, **kwargs):
    dados = dict(dados or {})
    dados.setdefault("_csrf", csrf(client))
    return client.post(url, data=dados, **kwargs)


def mensagens(resposta) -> list[str]:
    return re.findall(r'class="alerta alerta-\w+">\s*<span>(.*?)</span>', resposta.get_data(as_text=True), re.S)


def criar_usuario(nome="Admin", email="admin@teste.com", senha="segredo1", perfil="admin") -> Usuario:
    usuario = Usuario(nome=nome, email=email, perfil=perfil)
    usuario.definir_senha(senha)
    _db.session.add(usuario)
    _db.session.commit()
    return usuario


def logar(client, usuario: Usuario):
    with client.session_transaction() as sessao:
        sessao["usuario_id"] = usuario.id
        sessao["_csrf"] = "token-de-teste"


@pytest.fixture
def admin(db):
    return criar_usuario()


@pytest.fixture
def logado(client, admin):
    logar(client, admin)
    return client


@pytest.fixture
def base(db):
    """Um cliente, um serviço de 60 min e dois profissionais."""
    cliente = Cliente(nome="Mariana Alves", telefone="11987654321", email="mariana@exemplo.com")
    outro_cliente = Cliente(nome="João Pereira", telefone="11912345678")
    servico = Servico(nome="Corte", duracao_min=60, preco=Decimal("80.00"), ativo=True)
    ana = Profissional(nome="Ana Souza", especialidade="Cabeleireira", ativo=True)
    bruno = Profissional(nome="Bruno Lima", ativo=True)
    db.session.add_all([cliente, outro_cliente, servico, ana, bruno])
    db.session.commit()
    return {"cliente": cliente, "outro_cliente": outro_cliente, "servico": servico, "ana": ana, "bruno": bruno}


def form_agendamento(base, data=SEGUNDA, hora="10:00", cliente="cliente", profissional="ana", **extra):
    dados = {
        "cliente_id": base[cliente].id,
        "servico_id": base["servico"].id,
        "profissional_id": base[profissional].id,
        "data": data,
        "hora": hora,
    }
    dados.update(extra)
    return dados


def criar_agendamento(db, base, inicio: datetime, status="agendado", profissional="ana", cliente="cliente"):
    """Grava direto no banco, sem passar pelas validações (útil para montar cenários)."""
    from datetime import timedelta

    a = Agendamento(cliente_id=base[cliente].id, servico_id=base["servico"].id,
                    profissional_id=base[profissional].id, inicio=inicio,
                    fim=inicio + timedelta(minutes=base["servico"].duracao_min),
                    preco=base["servico"].preco, status=status)
    db.session.add(a)
    db.session.commit()
    return a
