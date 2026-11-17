from datetime import datetime, time, timedelta

from flask import Blueprint, abort, flash, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy.orm import joinedload

from ..config import DIAS_FECHADOS, HORA_ABERTURA, HORA_FECHAMENTO, ITENS_POR_PAGINA
from ..extensions import db
from ..models import STATUS_AGENDAMENTO, Agendamento, Cliente, Profissional, Servico
from ..utils import destino_seguro, hoje, login_obrigatorio, parse_data, parse_int

bp = Blueprint("agendamentos", __name__, url_prefix="/agendamentos")

MENSAGENS_STATUS = {
    "concluido": "Atendimento marcado como concluído.",
    "cancelado": "Agendamento cancelado. Se foi engano, use “Reabrir”.",
    "agendado": "Agendamento reaberto.",
}


def _obter(agendamento_id: int) -> Agendamento:
    agendamento = db.session.get(Agendamento, agendamento_id)
    if agendamento is None:
        abort(404)
    return agendamento


def _opcoes(agendamento: Agendamento | None = None) -> dict:
    """Listas para os <select> do formulário. Itens inativos só aparecem se já estiverem no registro."""
    servicos = Servico.query.filter(
        db.or_(Servico.ativo.is_(True), Servico.id == (agendamento.servico_id if agendamento else None))
    ).order_by(Servico.nome).all()
    profissionais = Profissional.query.filter(
        db.or_(Profissional.ativo.is_(True),
               Profissional.id == (agendamento.profissional_id if agendamento else None))
    ).order_by(Profissional.nome).all()
    return {
        "clientes": Cliente.query.order_by(Cliente.nome).all(),
        "servicos": servicos,
        "profissionais": profissionais,
        "abertura": f"{HORA_ABERTURA:02d}:00",
        "fechamento": f"{HORA_FECHAMENTO:02d}:00",
    }


@bp.route("/")
@login_obrigatorio
def lista():
    data = parse_data(request.args.get("data"))
    status = request.args.get("status") if request.args.get("status") in STATUS_AGENDAMENTO else ""
    profissional_id = parse_int(request.args.get("profissional_id"))
    periodo = "todos" if request.args.get("periodo") == "todos" else "proximos"

    consulta = db.select(Agendamento).options(
        joinedload(Agendamento.cliente), joinedload(Agendamento.servico), joinedload(Agendamento.profissional)
    )
    if data:
        inicio = datetime.combine(data, time.min)
        consulta = consulta.where(Agendamento.inicio >= inicio, Agendamento.inicio < inicio + timedelta(days=1))
        consulta = consulta.order_by(Agendamento.inicio)
    elif periodo == "todos":
        consulta = consulta.order_by(Agendamento.inicio.desc())
    else:
        consulta = consulta.where(Agendamento.inicio >= datetime.combine(hoje(), time.min))
        consulta = consulta.order_by(Agendamento.inicio)
    if status:
        consulta = consulta.where(Agendamento.status == status)
    if profissional_id:
        consulta = consulta.where(Agendamento.profissional_id == profissional_id)

    pagina = db.paginate(consulta, page=parse_int(request.args.get("pagina"), 1),
                         per_page=ITENS_POR_PAGINA, error_out=False)
    filtros = {"data": data.isoformat() if data else "", "status": status,
               "profissional_id": profissional_id or "", "periodo": periodo}
    return render_template("agendamentos/lista.html", pagina=pagina, filtros=filtros,
                           profissionais=Profissional.query.order_by(Profissional.nome).all())


@bp.route("/novo", methods=["GET", "POST"])
@login_obrigatorio
def novo():
    dados = {
        "cliente_id": request.args.get("cliente_id", ""),
        "data": request.args.get("data") or hoje().isoformat(),
        "hora": "",
    }
    if request.method == "POST":
        agendamento = Agendamento(status="agendado", criado_por_id=g.usuario.id)
        erros = agendamento.definir(request.form)
        if not erros:
            db.session.add(agendamento)
            db.session.commit()
            flash(f"Agendamento criado para {agendamento.inicio:%d/%m/%Y às %H:%M}.", "sucesso")
            return redirect(url_for("agendamentos.lista", data=agendamento.inicio.date().isoformat()))
        for erro in erros:
            flash(erro, "erro")
        dados = request.form
    return render_template("agendamentos/form.html", dados=dados, agendamento=None,
                           titulo="Novo agendamento", **_opcoes())


@bp.route("/<int:agendamento_id>/editar", methods=["GET", "POST"])
@login_obrigatorio
def editar(agendamento_id):
    agendamento = _obter(agendamento_id)
    if agendamento.status != "agendado":
        flash(f"Agendamentos com status “{agendamento.status_rotulo}” não podem ser alterados.", "aviso")
        return redirect(url_for("agendamentos.lista", data=agendamento.inicio.date().isoformat()))
    dados = {
        "cliente_id": agendamento.cliente_id,
        "servico_id": agendamento.servico_id,
        "profissional_id": agendamento.profissional_id,
        "data": agendamento.inicio.date().isoformat(),
        "hora": f"{agendamento.inicio:%H:%M}",
        "observacoes": agendamento.observacoes or "",
    }
    if request.method == "POST":
        erros = agendamento.definir(request.form)
        if not erros:
            db.session.commit()
            flash("Agendamento remarcado/atualizado.", "sucesso")
            return redirect(url_for("agendamentos.lista", data=agendamento.inicio.date().isoformat()))
        db.session.rollback()
        for erro in erros:
            flash(erro, "erro")
        dados = request.form
    return render_template("agendamentos/form.html", dados=dados, agendamento=agendamento,
                           titulo="Editar agendamento", **_opcoes(agendamento))


@bp.route("/<int:agendamento_id>/status", methods=["POST"])
@login_obrigatorio
def alterar_status(agendamento_id):
    agendamento = _obter(agendamento_id)
    novo_status = request.form.get("status", "")
    erro = agendamento.alterar_status(novo_status)
    if erro:
        db.session.rollback()
        flash(erro, "erro")
    else:
        db.session.commit()
        flash(MENSAGENS_STATUS[novo_status], "sucesso")
    return redirect(destino_seguro(request.form.get("voltar_para"))
                    or url_for("agendamentos.lista", data=agendamento.inicio.date().isoformat()))


@bp.route("/disponibilidade")
@login_obrigatorio
def disponibilidade():
    """JSON com os horários ocupados de um profissional em um dia (usado pelo formulário)."""
    profissional_id = parse_int(request.args.get("profissional_id"))
    data = parse_data(request.args.get("data"))
    if not profissional_id or not data:
        return jsonify(erro="Informe profissional_id e data (AAAA-MM-DD)."), 400
    inicio = datetime.combine(data, time.min)
    ocupados = Agendamento.conflitos(
        inicio, inicio + timedelta(days=1), profissional_id=profissional_id,
        ignorar_id=parse_int(request.args.get("ignorar")),
    ).options(joinedload(Agendamento.servico)).all()
    return jsonify(
        data=data.isoformat(),
        fechado=data.weekday() in DIAS_FECHADOS,
        abertura=f"{HORA_ABERTURA:02d}:00",
        fechamento=f"{HORA_FECHAMENTO:02d}:00",
        ocupados=[
            {"inicio": f"{a.inicio:%H:%M}", "fim": f"{a.fim:%H:%M}", "servico": a.servico.nome}
            for a in ocupados
        ],
    )
