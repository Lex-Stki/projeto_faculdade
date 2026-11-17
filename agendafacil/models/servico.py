from decimal import Decimal, InvalidOperation

from ..extensions import db
from ..utils import parse_int


class Servico(db.Model):
    """Serviço oferecido (ex.: corte, escova, barba), com duração e preço."""

    __tablename__ = "servico"
    __table_args__ = (
        db.CheckConstraint("duracao_min BETWEEN 5 AND 480", name="ck_servico_duracao"),
        db.CheckConstraint("preco >= 0", name="ck_servico_preco"),
    )

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False, unique=True)
    descricao = db.Column(db.String(255), nullable=True)
    duracao_min = db.Column(db.Integer, nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())

    agendamentos = db.relationship("Agendamento", back_populates="servico", lazy="dynamic")

    def preencher(self, dados: dict) -> list[str]:
        self.nome = (dados.get("nome") or "").strip()
        self.descricao = (dados.get("descricao") or "").strip() or None
        self.duracao_min = parse_int(dados.get("duracao_min"))
        preco_txt = (dados.get("preco") or "").strip().replace("R$", "").replace(" ", "")
        if "," in preco_txt:  # aceita 1.234,56 e 35,00
            preco_txt = preco_txt.replace(".", "").replace(",", ".")
        try:
            self.preco = Decimal(preco_txt).quantize(Decimal("0.01"))
        except InvalidOperation:
            self.preco = None

        erros = []
        if not 2 <= len(self.nome) <= 80:
            erros.append("Nome do serviço é obrigatório (entre 2 e 80 caracteres).")
        else:
            with db.session.no_autoflush:
                existente = Servico.query.filter(db.func.lower(Servico.nome) == self.nome.lower()).first()
            if existente and existente.id != self.id:
                erros.append("Já existe um serviço com este nome.")
        if self.descricao and len(self.descricao) > 255:
            erros.append("Descrição pode ter no máximo 255 caracteres.")
        if self.duracao_min is None or not 5 <= self.duracao_min <= 480:
            erros.append("Duração deve ser um número inteiro entre 5 e 480 minutos.")
        if self.preco is None or not Decimal("0") <= self.preco <= Decimal("99999.99"):
            erros.append("Preço inválido. Use um valor como 35,00.")
        return erros

    def __repr__(self) -> str:
        return f"<Servico {self.nome}>"
