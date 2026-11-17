"""Configuração da aplicação, lida de variáveis de ambiente.

Em produção (Vercel) são obrigatórias:
  - SECRET_KEY    -> chave para assinar o cookie de sessão
  - DATABASE_URL  -> URL do PostgreSQL (Neon). POSTGRES_URL também é aceita.

Localmente, sem DATABASE_URL, usa SQLite em instance/agendafacil.db.
"""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Regras de negócio configuráveis
HORA_ABERTURA = 8         # 08:00
HORA_FECHAMENTO = 20      # 20:00 (o atendimento precisa terminar até este horário)
DIAS_FECHADOS = {6}       # 6 = domingo (datetime.weekday())
FUSO_HORARIO = "America/Sao_Paulo"
ITENS_POR_PAGINA = 10
TAMANHO_MAX_SCREENSHOT = 2 * 1024 * 1024  # 2 MB


def cadastro_aberto() -> bool:
    """Permite criar contas pela tela /cadastro. Deixe aberto durante os testes com os colegas
    e defina CADASTRO_ABERTO=0 depois, para que só o administrador existente use o sistema."""
    return os.environ.get("CADASTRO_ABERTO", "1") != "0"


def em_producao() -> bool:
    return bool(os.environ.get("VERCEL"))


def url_banco() -> str:
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if url:
        # SQLAlchemy exige o prefixo "postgresql://"
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        return url
    if em_producao():
        raise RuntimeError(
            "DATABASE_URL não configurada. No Vercel, conecte um banco Neon em "
            "Storage ou crie a variável DATABASE_URL em Settings > Environment Variables."
        )
    pasta = BASE_DIR / "instance"
    pasta.mkdir(exist_ok=True)
    return f"sqlite:///{(pasta / 'agendafacil.db').as_posix()}"


def chave_secreta() -> str:
    chave = os.environ.get("SECRET_KEY")
    if chave:
        return chave
    if em_producao():
        raise RuntimeError(
            "SECRET_KEY não configurada. Crie a variável em Settings > Environment Variables no Vercel."
        )
    return secrets.token_hex(32)


def montar_config(sobrescrever: dict | None = None) -> dict:
    sobrescrever = sobrescrever or {}
    cfg = {
        "SECRET_KEY": sobrescrever.get("SECRET_KEY") or chave_secreta(),
        "SQLALCHEMY_DATABASE_URI": sobrescrever.get("SQLALCHEMY_DATABASE_URI") or url_banco(),
        "SQLALCHEMY_ENGINE_OPTIONS": {"pool_pre_ping": True, "pool_recycle": 280},
        "MAX_CONTENT_LENGTH": TAMANHO_MAX_SCREENSHOT + 512 * 1024,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": em_producao(),
        "CADASTRO_ABERTO": cadastro_aberto(),
    }
    cfg.update(sobrescrever)
    return cfg
