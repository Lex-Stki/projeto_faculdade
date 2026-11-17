from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..config import ITENS_POR_PAGINA
from ..extensions import db
from ..models import Agendamento, Cliente
from ..utils import formatar_telefone, limpar, login_obrigatorio, parse_int, somente_digitos

bp = Blueprint("clientes", __name__, url_prefix="/clientes")


def _obter(cliente_id: int) -> Cliente:
    cliente = db.session.get(Cliente, cliente_id)
    if cliente is None:
        abort(404)
    return cliente


@bp.route("/")
@login_obrigatorio
def lista():
    busca = limpar(request.args.get("q"))
    consulta = db.select(Cliente).order_by(Cliente.nome)
    if busca:
        termo = f"%{busca.lower()}%"
        condicoes = [db.func.lower(Cliente.nome).like(termo), db.func.lower(Cliente.email).like(termo)]
        digitos = somente_digitos(busca)
        if digitos:
            condicoes.append(Cliente.telefone.like(f"%{digitos}%"))
        consulta = consulta.where(db.or_(*condicoes))
    pagina = db.paginate(consulta, page=parse_int(request.args.get("pagina"), 1),
                         per_page=ITENS_POR_PAGINA, error_out=False)
    return render_template("clientes/lista.html", pagina=pagina, busca=busca)


@bp.route("/novo", methods=["GET", "POST"])
@login_obrigatorio
def novo():
    dados = {"nome": limpar(request.args.get("nome"))}
    if request.method == "POST":
        cliente = Cliente()
        erros = cliente.preencher(request.form)
        if not erros:
            db.session.add(cliente)
            db.session.commit()
            flash(f"Cliente “{cliente.nome}” cadastrado.", "sucesso")
            if request.form.get("agendar"):
                return redirect(url_for("agendamentos.novo", cliente_id=cliente.id))
            return redirect(url_for("clientes.detalhe", cliente_id=cliente.id))
        for erro in erros:
            flash(erro, "erro")
        dados = request.form
    return render_template("clientes/form.html", dados=dados, cliente_id=None, titulo="Novo cliente")


@bp.route("/<int:cliente_id>")
@login_obrigatorio
def detalhe(cliente_id):
    cliente = _obter(cliente_id)
    historico = cliente.agendamentos.order_by(Agendamento.inicio.desc()).limit(50).all()
    return render_template("clientes/detalhe.html", cliente=cliente, historico=historico)


@bp.route("/<int:cliente_id>/editar", methods=["GET", "POST"])
@login_obrigatorio
def editar(cliente_id):
    cliente = _obter(cliente_id)
    dados = {
        "nome": cliente.nome,
        "telefone": formatar_telefone(cliente.telefone),
        "email": cliente.email or "",
        "observacoes": cliente.observacoes or "",
    }
    if request.method == "POST":
        erros = cliente.preencher(request.form)
        if not erros:
            db.session.commit()
            flash("Dados do cliente atualizados.", "sucesso")
            return redirect(url_for("clientes.detalhe", cliente_id=cliente.id))
        db.session.rollback()  # descarta as alterações inválidas
        for erro in erros:
            flash(erro, "erro")
        dados = request.form
    return render_template("clientes/form.html", dados=dados, cliente_id=cliente_id, titulo="Editar cliente")


@bp.route("/<int:cliente_id>/excluir", methods=["POST"])
@login_obrigatorio
def excluir(cliente_id):
    cliente = _obter(cliente_id)
    total = cliente.agendamentos.count()
    if total:
        flash(f"“{cliente.nome}” tem {total} agendamento(s) no histórico e não pode ser excluído.", "erro")
        return redirect(url_for("clientes.detalhe", cliente_id=cliente.id))
    db.session.delete(cliente)
    db.session.commit()
    flash(f"Cliente “{cliente.nome}” excluído.", "sucesso")
    return redirect(url_for("clientes.lista"))
