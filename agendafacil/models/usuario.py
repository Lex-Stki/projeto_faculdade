from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..utils import agora, email_valido

PERFIS = ("admin", "atendente")


class Usuario(db.Model):
    """Pessoa que opera o sistema (dono do negócio ou atendente)."""

    __tablename__ = "usuario"
    __table_args__ = (
        db.CheckConstraint("perfil IN ('admin', 'atendente')", name="ck_usuario_perfil"),
    )

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.String(20), nullable=False, default="atendente", server_default="atendente")
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    def definir_senha(self, senha: str) -> None:
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha or "")

    @staticmethod
    def validar_cadastro(nome: str, email: str, senha: str, confirmacao: str) -> list[str]:
        erros = []
        if not 2 <= len(nome) <= 100:
            erros.append("Informe seu nome (entre 2 e 100 caracteres).")
        if not email_valido(email) or len(email) > 120:
            erros.append("Informe um e-mail válido.")
        elif Usuario.query.filter(db.func.lower(Usuario.email) == email.lower()).first():
            erros.append("Já existe uma conta com este e-mail. Use a opção Entrar.")
        if len(senha) < 6:
            erros.append("A senha precisa ter pelo menos 6 caracteres.")
        elif senha != confirmacao:
            erros.append("A confirmação de senha não confere.")
        return erros

    def __repr__(self) -> str:
        return f"<Usuario {self.email}>"
