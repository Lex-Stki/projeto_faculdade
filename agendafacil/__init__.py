"""AgendaFácil — sistema de agendamento para pequenos negócios de serviços.

Arquitetura MVC:
  models/       -> Model: entidades, persistência (SQLAlchemy) e regras de negócio
  views/        -> View: templates HTML (Jinja2) + static/ (CSS e JavaScript)
  controllers/  -> Controller: rotas HTTP que recebem a entrada do usuário,
                   acionam o model e escolhem a view
"""
from flask import Flask, g, render_template, session
from werkzeug.exceptions import HTTPException

from . import utils
from .config import montar_config
from .extensions import db
from .models import STATUS_AGENDAMENTO, Usuario

TITULOS_ERRO = {
    400: "Requisição inválida",
    403: "Acesso negado",
    404: "Página não encontrada",
    405: "Ação não permitida",
    413: "Arquivo muito grande",
    500: "Erro interno",
}

MENSAGENS_ERRO = {
    403: "Você não tem permissão para acessar esta página.",
    404: "O endereço que você tentou acessar não existe ou o registro foi removido.",
    405: "Esta ação não pode ser feita por este caminho.",
    413: "O arquivo enviado passa do limite de 2 MB. Reduza a imagem e tente de novo.",
    500: "Algo deu errado do nosso lado. Tente novamente em instantes.",
}


def create_app(sobrescrever: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="views", static_folder="static")
    app.config.update(montar_config(sobrescrever))

    db.init_app(app)
    _registrar_blueprints(app)
    _registrar_hooks(app)
    _registrar_filtros(app)
    _registrar_erros(app)
    _registrar_comandos(app)

    with app.app_context():
        db.create_all()

    return app


def _registrar_blueprints(app: Flask) -> None:
    from .controllers import agendamentos, auth, clientes, dashboard, feedback, profissionais, servicos

    for modulo in (auth, dashboard, clientes, servicos, profissionais, agendamentos, feedback):
        app.register_blueprint(modulo.bp)


def _registrar_hooks(app: Flask) -> None:
    @app.before_request
    def carregar_usuario():
        usuario_id = session.get("usuario_id")
        g.usuario = db.session.get(Usuario, usuario_id) if usuario_id else None
        if usuario_id and g.usuario is None:  # conta removida
            session.pop("usuario_id", None)
        utils.verificar_csrf()

    @app.context_processor
    def variaveis_globais():
        return {
            "csrf_token": utils.gerar_csrf_token,
            "STATUS_AGENDAMENTO": STATUS_AGENDAMENTO,
            "hoje": utils.hoje,
        }

    @app.after_request
    def cabecalhos_seguranca(resposta):
        resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
        resposta.headers.setdefault("X-Frame-Options", "DENY")
        resposta.headers.setdefault("Referrer-Policy", "same-origin")
        return resposta


def _registrar_filtros(app: Flask) -> None:
    app.add_template_filter(utils.formatar_telefone, "telefone")
    app.add_template_filter(utils.formatar_moeda, "moeda")
    app.add_template_filter(utils.formatar_data, "data")
    app.add_template_filter(utils.formatar_data_hora, "data_hora")
    app.add_template_filter(utils.formatar_hora, "hora")


def _registrar_erros(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def erro_http(erro: HTTPException):
        codigo = erro.code or 500
        mensagem = MENSAGENS_ERRO.get(codigo) or erro.description
        if codigo == 400 and erro.description:
            mensagem = erro.description
        return (
            render_template("erros/erro.html", codigo=codigo,
                            titulo=TITULOS_ERRO.get(codigo, "Erro"), mensagem=mensagem),
            codigo,
        )

    @app.errorhandler(Exception)
    def erro_inesperado(erro: Exception):
        app.logger.exception("Erro não tratado: %s", erro)
        db.session.rollback()
        return (
            render_template("erros/erro.html", codigo=500, titulo=TITULOS_ERRO[500],
                            mensagem=MENSAGENS_ERRO[500]),
            500,
        )


def _registrar_comandos(app: Flask) -> None:
    @app.cli.command("seed")
    def seed():
        """Cria dados de demonstração (serviços, profissionais e clientes)."""
        from .seed import popular

        print(popular())
