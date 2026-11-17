from ..extensions import db
from ..utils import agora, email_valido, somente_digitos


class Cliente(db.Model):
    """Pessoa atendida pelo negócio."""

    __tablename__ = "cliente"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, index=True)
    telefone = db.Column(db.String(11), nullable=False)  # somente dígitos: DDD + número
    email = db.Column(db.String(120), nullable=True)
    observacoes = db.Column(db.String(500), nullable=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    agendamentos = db.relationship("Agendamento", back_populates="cliente", lazy="dynamic")

    def preencher(self, dados: dict) -> list[str]:
        """Copia os dados do formulário para o objeto e devolve a lista de erros."""
        self.nome = (dados.get("nome") or "").strip()
        self.telefone = somente_digitos(dados.get("telefone"))
        self.email = (dados.get("email") or "").strip().lower() or None
        self.observacoes = (dados.get("observacoes") or "").strip() or None

        erros = []
        if not 2 <= len(self.nome) <= 100:
            erros.append("Nome do cliente é obrigatório (entre 2 e 100 caracteres).")
        if len(self.telefone) not in (10, 11):
            erros.append("Telefone deve ter DDD + número (10 ou 11 dígitos).")
        if self.email and (not email_valido(self.email) or len(self.email) > 120):
            erros.append("E-mail do cliente é inválido.")
        if self.observacoes and len(self.observacoes) > 500:
            erros.append("Observações podem ter no máximo 500 caracteres.")
        return erros

    def __repr__(self) -> str:
        return f"<Cliente {self.nome}>"
