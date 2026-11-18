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


def _primeira_data_com_horario():
    """Data padrão do novo agendamento: hoje, ou o próximo dia que ainda tenha horário livre
    (depois do expediente ou no domingo, abrir em "hoje" mostrava uma lista vazia; defeito D8)."""
    dia = hoje()
    for _ in range(14):
        if any(h["livre"] for h in Agendamento.horarios_do_dia(dia)):
            return dia
        dia += timedelta(days=1)
    return hoje()


def _horarios(dados, ignorar_id=None) -> list[dict]:
    """Lista de horários do <select> conforme o que já está escolhido no formulário.

    Renderizada no servidor para funcionar mesmo sem JavaScript; o agendamento.js a atualiza
    sempre que data, serviço, profissional ou cliente mudam.
    """
    servico = db.session.get(Servico, parse_int(dados.get("servico_id"), 0))
    horarios = Agendamento.horarios_do_dia(
        parse_data(dados.get("data")),
        duracao_min=servico.duracao_min if servico else None,
        profissional_id=parse_int(dados.get("profissional_id")),
        cliente_id=parse_int(dados.get("cliente_id")),
        ignorar_id=ignorar_id,
    )
    hora = (dados.get("hora") or "")[:5]
    if hora and all(h["hora"] != hora for h in horarios):
        # horário fora da grade (ex.: agendamento antigo às 08:35): mantém a opção para não perdê-lo
        horarios.append({"hora": hora, "fim": "", "livre": True, "motivo": None})
        horarios.sort(key=lambda h: h["hora"])
    return horarios


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
        "data": request.args.get("data") or _primeira_data_com_horario().isoformat(),
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
                           titulo="Novo agendamento", horarios=_horarios(dados), **_opcoes())


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
                           titulo="Editar agendamento", horarios=_horarios(dados, agendamento.id),
                           **_opcoes(agendamento))


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
    """JSON usado pelo formulário: horários do dia (livres/bloqueados com motivo) e ocupação do profissional.

    Parâmetros: data (obrigatório, AAAA-MM-DD), profissional_id, servico_id, cliente_id, ignorar.
    """
    data = parse_data(request.args.get("data"))
    if not data:
        return jsonify(erro="Informe a data (AAAA-MM-DD)."), 400
    profissional_id = parse_int(request.args.get("profissional_id"))
    ignorar_id = parse_int(request.args.get("ignorar"))
    ocupados = []
    if profissional_id:
        inicio = datetime.combine(data, time.min)
        ocupados = Agendamento.conflitos(
            inicio, inicio + timedelta(days=1), profissional_id=profissional_id, ignorar_id=ignorar_id,
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
        horarios=_horarios(request.args, ignorar_id),
    )
