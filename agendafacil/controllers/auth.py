from flask import Blueprint, current_app, flash, g, redirect, render_template, request, session, url_for

from ..extensions import db
from ..models import Usuario
from ..utils import destino_seguro, limpar

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.usuario:
        return redirect(url_for("dashboard.inicio"))
    email = ""
    if request.method == "POST":
        email = limpar(request.form.get("email")).lower()
        senha = request.form.get("senha") or ""
        usuario = Usuario.query.filter(db.func.lower(Usuario.email) == email).first()
        if usuario and usuario.verificar_senha(senha):
            session.clear()
            session["usuario_id"] = usuario.id
            flash(f"Bem-vindo(a), {usuario.nome}!", "sucesso")
            return redirect(destino_seguro(request.args.get("proximo")) or url_for("dashboard.inicio"))
        flash("E-mail ou senha incorretos.", "erro")
    return render_template("auth/login.html", email=email)


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if g.usuario:
        return redirect(url_for("dashboard.inicio"))
    # A primeira conta sempre pode ser criada (senão ninguém conseguiria entrar)
    if not current_app.config["CADASTRO_ABERTO"] and Usuario.query.count() > 0:
        flash("O cadastro de novas contas está fechado. Fale com o administrador.", "aviso")
        return redirect(url_for("auth.login"))
    dados = {}
    if request.method == "POST":
        dados = {k: limpar(request.form.get(k)) for k in ("nome", "email")}
        dados["email"] = dados["email"].lower()
        senha = request.form.get("senha") or ""
        erros = Usuario.validar_cadastro(dados["nome"], dados["email"], senha,
                                         request.form.get("confirmacao") or "")
        if erros:
            for erro in erros:
                flash(erro, "erro")
        else:
            primeiro = Usuario.query.count() == 0
            usuario = Usuario(nome=dados["nome"], email=dados["email"],
                              perfil="admin" if primeiro else "atendente")
            usuario.definir_senha(senha)
            db.session.add(usuario)
            db.session.commit()
            session.clear()
            session["usuario_id"] = usuario.id
            msg = "Conta criada! Você é o administrador do sistema." if primeiro else "Conta criada com sucesso!"
            flash(msg, "sucesso")
            return redirect(url_for("dashboard.inicio"))
    return render_template("auth/cadastro.html", dados=dados)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))
