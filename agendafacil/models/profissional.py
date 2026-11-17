from ..extensions import db


class Profissional(db.Model):
    """Pessoa que executa os serviços. Cada profissional tem a própria agenda."""

    __tablename__ = "profissional"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    especialidade = db.Column(db.String(80), nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())

    agendamentos = db.relationship("Agendamento", back_populates="profissional", lazy="dynamic")

    def preencher(self, dados: dict) -> list[str]:
        self.nome = (dados.get("nome") or "").strip()
        self.especialidade = (dados.get("especialidade") or "").strip() or None
        erros = []
        if not 2 <= len(self.nome) <= 100:
            erros.append("Nome do profissional é obrigatório (entre 2 e 100 caracteres).")
        if self.especialidade and len(self.especialidade) > 80:
            erros.append("Especialidade pode ter no máximo 80 caracteres.")
        return erros

    def __repr__(self) -> str:
        return f"<Profissional {self.nome}>"
