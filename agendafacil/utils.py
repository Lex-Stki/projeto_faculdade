"""Funções auxiliares compartilhadas: data/hora, validação, segurança."""
import re
import secrets
from datetime import date, datetime, time
from functools import wraps
from zoneinfo import ZoneInfo

from flask import abort, flash, g, redirect, request, session, url_for

from . import config

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


# ---------------------------------------------------------------- data/hora
def agora() -> datetime:
    """Data/hora atual no fuso do negócio, sem tzinfo (é assim que gravamos no banco)."""
    return datetime.now(ZoneInfo(config.FUSO_HORARIO)).replace(tzinfo=None, microsecond=0)


def hoje() -> date:
    return agora().date()


def parse_data(texto: str | None) -> date | None:
    try:
        return date.fromisoformat((texto or "").strip())
    except ValueError:
        return None


def parse_hora(texto: str | None) -> time | None:
    try:
        return time.fromisoformat((texto or "").strip()[:5])
    except ValueError:
        return None


def parse_int(texto, padrao=None):
    try:
        return int(str(texto).strip())
    except (TypeError, ValueError):
        return padrao


def somente_digitos(texto: str | None) -> str:
    return re.sub(r"\D", "", texto or "")


def limpar(texto: str | None) -> str:
    return (texto or "").strip()


def email_valido(email: str) -> bool:
    return bool(EMAIL_RE.match(email or ""))


# ---------------------------------------------------------------- formatação (filtros Jinja)
def formatar_telefone(digitos: str | None) -> str:
    d = somente_digitos(digitos)
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return digitos or ""


def formatar_moeda(valor) -> str:
    if valor is None:
        return ""
    texto = f"{float(valor):,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_data(valor) -> str:
    return valor.strftime("%d/%m/%Y") if valor else ""


def formatar_data_hora(valor) -> str:
    return valor.strftime("%d/%m/%Y %H:%M") if valor else ""


def formatar_hora(valor) -> str:
    return valor.strftime("%H:%M") if valor else ""


# ---------------------------------------------------------------- CSRF
def gerar_csrf_token() -> str:
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def verificar_csrf():
    if request.method != "POST":
        return
    enviado = request.form.get("_csrf") or request.headers.get("X-CSRF-Token")
    esperado = session.get("_csrf")
    if not esperado or not enviado or not secrets.compare_digest(enviado, esperado):
        abort(400, description="Sua sessão expirou ou o formulário é inválido. Recarregue a página e tente novamente.")


# ---------------------------------------------------------------- autenticação
def login_obrigatorio(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if g.get("usuario") is None:
            flash("Faça login para continuar.", "aviso")
            return redirect(url_for("auth.login", proximo=request.full_path.rstrip("?")))
        return view(*args, **kwargs)

    return wrapper


def admin_obrigatorio(view):
    @wraps(view)
    @login_obrigatorio
    def wrapper(*args, **kwargs):
        if g.usuario.perfil != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapper


def destino_seguro(url: str | None) -> str | None:
    """Evita open redirect: só aceita caminhos relativos do próprio site."""
    if url and url.startswith("/") and not url.startswith("//") and "\\" not in url:
        return url
    return None
