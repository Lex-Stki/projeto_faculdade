from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..extensions import db
from ..models import Servico
from ..utils import login_obrigatorio

bp = Blueprint("servicos", __name__, url_prefix="/servicos")


def _obter(servico_id: int) -> Servico:
    servico = db.session.get(Servico, servico_id)
    if servico is None:
        abort(404)
    return servico


def _como_formulario(servico: Servico) -> dict:
    return {
        "nome": servico.nome,
        "descricao": servico.descricao or "",
        "duracao_min": servico.duracao_min,
        "preco": f"{servico.preco:.2f}".replace(".", ","),
    }


@bp.route("/")
@login_obrigatorio
def lista():
    servicos = Servico.query.order_by(Servico.ativo.desc(), Servico.nome).all()
    return render_template("servicos/lista.html", servicos=servicos)


@bp.route("/novo", methods=["GET", "POST"])
@login_obrigatorio
def novo():
    dados = {"duracao_min": 30}
    if request.method == "POST":
        servico = Servico(ativo=True)
        erros = servico.preencher(request.form)
        if not erros:
            db.session.add(servico)
            db.session.commit()
            flash(f"Serviço “{servico.nome}” cadastrado.", "sucesso")
            return redirect(url_for("servicos.lista"))
        for erro in erros:
            flash(erro, "erro")
        dados = request.form
    return render_template("servicos/form.html", dados=dados, servico_id=None, titulo="Novo serviço")


@bp.route("/<int:servico_id>/editar", methods=["GET", "POST"])
@login_obrigatorio
def editar(servico_id):
    servico = _obter(servico_id)
    dados = _como_formulario(servico)
    if request.method == "POST":
        erros = servico.preencher(request.form)
        if not erros:
            db.session.commit()
            flash("Serviço atualizado. Agendamentos já marcados mantêm o preço e a duração originais.", "sucesso")
            return redirect(url_for("servicos.lista"))
        db.session.rollback()
        for erro in erros:
            flash(erro, "erro")
        dados = request.form
    return render_template("servicos/form.html", dados=dados, servico_id=servico_id, titulo="Editar serviço")


@bp.route("/<int:servico_id>/alternar", methods=["POST"])
@login_obrigatorio
def alternar(servico_id):
    servico = _obter(servico_id)
    servico.ativo = not servico.ativo
    db.session.commit()
    estado = "reativado" if servico.ativo else "desativado (não aparece em novos agendamentos)"
    flash(f"Serviço “{servico.nome}” {estado}.", "sucesso")
    return redirect(url_for("servicos.lista"))


@bp.route("/<int:servico_id>/excluir", methods=["POST"])
@login_obrigatorio
def excluir(servico_id):
    servico = _obter(servico_id)
    if servico.agendamentos.count():
        flash(f"“{servico.nome}” já foi usado em agendamentos. Use “Desativar” em vez de excluir.", "erro")
        return redirect(url_for("servicos.lista"))
    db.session.delete(servico)
    db.session.commit()
    flash(f"Serviço “{servico.nome}” excluído.", "sucesso")
    return redirect(url_for("servicos.lista"))
