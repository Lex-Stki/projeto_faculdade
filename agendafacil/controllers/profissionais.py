from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..extensions import db
from ..models import Profissional
from ..utils import login_obrigatorio

bp = Blueprint("profissionais", __name__, url_prefix="/profissionais")


def _obter(profissional_id: int) -> Profissional:
    profissional = db.session.get(Profissional, profissional_id)
    if profissional is None:
        abort(404)
    return profissional


@bp.route("/")
@login_obrigatorio
def lista():
    profissionais = Profissional.query.order_by(Profissional.ativo.desc(), Profissional.nome).all()
    return render_template("profissionais/lista.html", profissionais=profissionais)


@bp.route("/novo", methods=["GET", "POST"])
@login_obrigatorio
def novo():
    dados = {}
    if request.method == "POST":
        profissional = Profissional(ativo=True)
        erros = profissional.preencher(request.form)
        if not erros:
            db.session.add(profissional)
            db.session.commit()
            flash(f"Profissional “{profissional.nome}” cadastrado.", "sucesso")
            return redirect(url_for("profissionais.lista"))
        for erro in erros:
            flash(erro, "erro")
        dados = request.form
    return render_template("profissionais/form.html", dados=dados, profissional_id=None,
                           titulo="Novo profissional")


@bp.route("/<int:profissional_id>/editar", methods=["GET", "POST"])
@login_obrigatorio
def editar(profissional_id):
    profissional = _obter(profissional_id)
    dados = {"nome": profissional.nome, "especialidade": profissional.especialidade or ""}
    if request.method == "POST":
        erros = profissional.preencher(request.form)
        if not erros:
            db.session.commit()
            flash("Profissional atualizado.", "sucesso")
            return redirect(url_for("profissionais.lista"))
        db.session.rollback()
        for erro in erros:
            flash(erro, "erro")
        dados = request.form
    return render_template("profissionais/form.html", dados=dados, profissional_id=profissional_id,
                           titulo="Editar profissional")


@bp.route("/<int:profissional_id>/alternar", methods=["POST"])
@login_obrigatorio
def alternar(profissional_id):
    profissional = _obter(profissional_id)
    profissional.ativo = not profissional.ativo
    db.session.commit()
    estado = "reativado" if profissional.ativo else "inativado (não aparece em novos agendamentos)"
    flash(f"Profissional “{profissional.nome}” {estado}.", "sucesso")
    return redirect(url_for("profissionais.lista"))


@bp.route("/<int:profissional_id>/excluir", methods=["POST"])
@login_obrigatorio
def excluir(profissional_id):
    profissional = _obter(profissional_id)
    if profissional.agendamentos.count():
        flash(f"“{profissional.nome}” tem agendamentos no histórico. Use “Inativar” em vez de excluir.", "erro")
        return redirect(url_for("profissionais.lista"))
    db.session.delete(profissional)
    db.session.commit()
    flash(f"Profissional “{profissional.nome}” excluído.", "sucesso")
    return redirect(url_for("profissionais.lista"))
