"""Formulário de teste para os colegas (Situação-Problema 3) e consulta dos laudos recebidos."""
import csv
import io

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for

from ..config import ITENS_POR_PAGINA
from ..extensions import db
from ..models import Feedback
from ..utils import admin_obrigatorio, hoje, parse_int

bp = Blueprint("feedback", __name__, url_prefix="/feedback")


@bp.route("/", methods=["GET", "POST"])
def formulario():
    dados = {"data_teste": hoje().isoformat()}
    if request.method == "POST":
        feedback = Feedback()
        erros = feedback.preencher(request.form, request.files.get("screenshot"))
        if not erros:
            db.session.add(feedback)
            db.session.commit()
            return redirect(url_for("feedback.obrigado"))
        for erro in erros:
            flash(erro, "erro")
        dados = request.form
    return render_template("feedback/form.html", dados=dados)


@bp.route("/obrigado")
def obrigado():
    return render_template("feedback/obrigado.html")


@bp.route("/recebidos")
@admin_obrigatorio
def lista():
    consulta = db.select(Feedback).order_by(Feedback.criado_em.desc())
    pagina = db.paginate(consulta, page=parse_int(request.args.get("pagina"), 1),
                         per_page=ITENS_POR_PAGINA, error_out=False)
    return render_template("feedback/lista.html", pagina=pagina)


@bp.route("/<int:feedback_id>/screenshot")
@admin_obrigatorio
def screenshot(feedback_id):
    feedback = db.session.get(Feedback, feedback_id)
    if feedback is None or not feedback.screenshot:
        abort(404)
    return Response(feedback.screenshot, mimetype=feedback.screenshot_mime,
                    headers={"Cache-Control": "private, max-age=3600"})


@bp.route("/exportar.csv")
@admin_obrigatorio
def exportar():
    """Exporta todos os laudos em CSV (abre no Excel) para montar o documento de entrega."""
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(["id", "nome", "email", "data_teste", "funcionou", "nao_funcionou",
                       "nao_testado", "sugestoes", "avaliacao", "tem_screenshot", "enviado_em"])
    for f in Feedback.query.order_by(Feedback.criado_em).all():
        escritor.writerow([f.id, f.nome_testador, f.email_testador or "", f.data_teste.isoformat(),
                           f.funcionou or "", f.nao_funcionou or "", f.nao_testado or "",
                           f.sugestoes or "", f.avaliacao or "", "sim" if f.screenshot else "não",
                           f.criado_em.isoformat(sep=" ")])
    conteudo = "﻿" + saida.getvalue()  # BOM para o Excel reconhecer UTF-8
    return Response(conteudo, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=laudos_teste.csv"})


@bp.route("/<int:feedback_id>/excluir", methods=["POST"])
@admin_obrigatorio
def excluir(feedback_id):
    feedback = db.session.get(Feedback, feedback_id)
    if feedback is None:
        abort(404)
    db.session.delete(feedback)
    db.session.commit()
    flash("Laudo excluído.", "sucesso")
    return redirect(url_for("feedback.lista"))
