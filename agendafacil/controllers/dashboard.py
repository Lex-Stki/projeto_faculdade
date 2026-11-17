from datetime import datetime, time, timedelta

from flask import Blueprint, flash, jsonify, redirect, render_template, url_for
from sqlalchemy import text

from ..extensions import db
from ..models import Agendamento, Cliente, Profissional, Servico
from ..utils import admin_obrigatorio, agora, login_obrigatorio

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_obrigatorio
def inicio():
    momento = agora()
    inicio_dia = datetime.combine(momento.date(), time.min)
    fim_dia = inicio_dia + timedelta(days=1)

    de_hoje = (
        Agendamento.query.filter(Agendamento.inicio >= inicio_dia, Agendamento.inicio < fim_dia)
        .order_by(Agendamento.inicio)
        .all()
    )
    ativos_hoje = [a for a in de_hoje if a.status != "cancelado"]
    proximos = (
        Agendamento.query.filter(Agendamento.inicio >= fim_dia, Agendamento.status == "agendado")
        .order_by(Agendamento.inicio)
        .limit(5)
        .all()
    )
    indicadores = {
        "hoje": len(ativos_hoje),
        "pendentes_hoje": sum(1 for a in ativos_hoje if a.status == "agendado"),
        "receita_hoje": sum((a.preco for a in ativos_hoje), 0),
        "clientes": Cliente.query.count(),
    }
    sem_cadastros = Servico.query.count() == 0 or Profissional.query.count() == 0
    return render_template("dashboard.html", de_hoje=de_hoje, proximos=proximos,
                           indicadores=indicadores, agora=momento, sem_cadastros=sem_cadastros)


@bp.route("/dados-exemplo", methods=["POST"])
@admin_obrigatorio
def dados_exemplo():
    from ..seed import popular

    flash(popular(), "sucesso")
    return redirect(url_for("dashboard.inicio"))


@bp.route("/saude")
def saude():
    """Verificação simples de funcionamento (usada no laudo/monitoramento)."""
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify(status="ok", banco="ok")
    except Exception:  # pragma: no cover - depende de falha de infraestrutura
        return jsonify(status="erro", banco="indisponível"), 503
