from datetime import datetime, time, timedelta

from ..config import DIAS_FECHADOS, HORA_ABERTURA, HORA_FECHAMENTO
from ..extensions import db
from ..utils import agora, parse_data, parse_hora, parse_int
from .cliente import Cliente
from .profissional import Profissional
from .servico import Servico

STATUS_AGENDAMENTO = {
    "agendado": "Agendado",
    "concluido": "Concluído",
    "cancelado": "Cancelado",
}

# Transições permitidas: status atual -> novos status possíveis
TRANSICOES = {
    "agendado": {"concluido", "cancelado"},
    "cancelado": {"agendado"},  # "reabrir" um cancelamento feito por engano
    "concluido": set(),
}

NOMES_DIA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


class Agendamento(db.Model):
    """Reserva de um horário: um cliente, um serviço, um profissional, um intervalo de tempo."""

    __tablename__ = "agendamento"
    __table_args__ = (
        db.CheckConstraint("fim > inicio", name="ck_agendamento_intervalo"),
        db.CheckConstraint(
            "status IN ('agendado', 'concluido', 'cancelado')", name="ck_agendamento_status"
        ),
        db.CheckConstraint("preco >= 0", name="ck_agendamento_preco"),
        db.Index("ix_agendamento_profissional_inicio", "profissional_id", "inicio"),
        db.Index("ix_agendamento_cliente_inicio", "cliente_id", "inicio"),
    )

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id", ondelete="RESTRICT"), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey("servico.id", ondelete="RESTRICT"), nullable=False)
    profissional_id = db.Column(
        db.Integer, db.ForeignKey("profissional.id", ondelete="RESTRICT"), nullable=False
    )
    criado_por_id = db.Column(db.Integer, db.ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True)
    inicio = db.Column(db.DateTime, nullable=False)
    fim = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="agendado", server_default="agendado")
    # Preço cobrado, copiado do serviço no momento do agendamento (histórico não muda
    # quando o preço do serviço for reajustado).
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    observacoes = db.Column(db.String(500), nullable=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    cliente = db.relationship("Cliente", back_populates="agendamentos")
    servico = db.relationship("Servico", back_populates="agendamentos")
    profissional = db.relationship("Profissional", back_populates="agendamentos")
    criado_por = db.relationship("Usuario")

    @property
    def status_rotulo(self) -> str:
        return STATUS_AGENDAMENTO.get(self.status, self.status)

    # ------------------------------------------------------------------ regras
    def definir(self, dados: dict, referencia: datetime | None = None) -> list[str]:
        """Preenche o agendamento a partir do formulário e aplica as regras de negócio.

        `referencia` é o "agora" usado na validação (parâmetro para facilitar testes).
        """
        referencia = referencia or agora()
        erros: list[str] = []

        cliente = db.session.get(Cliente, parse_int(dados.get("cliente_id"), 0))
        servico = db.session.get(Servico, parse_int(dados.get("servico_id"), 0))
        profissional = db.session.get(Profissional, parse_int(dados.get("profissional_id"), 0))
        data = parse_data(dados.get("data"))
        hora = parse_hora(dados.get("hora"))
        self.observacoes = (dados.get("observacoes") or "").strip() or None

        if cliente is None:
            erros.append("Selecione um cliente.")
        if servico is None:
            erros.append("Selecione um serviço.")
        elif not servico.ativo and servico.id != self.servico_id:
            erros.append(f"O serviço “{servico.nome}” está desativado.")
        if profissional is None:
            erros.append("Selecione um profissional.")
        elif not profissional.ativo and profissional.id != self.profissional_id:
            erros.append(f"O profissional “{profissional.nome}” está inativo.")
        if data is None:
            erros.append("Informe uma data válida.")
        if hora is None:
            erros.append("Informe um horário válido.")
        if self.observacoes and len(self.observacoes) > 500:
            erros.append("Observações podem ter no máximo 500 caracteres.")
        if erros:
            return erros

        servico_mudou = self.servico_id != servico.id
        self.cliente_id = cliente.id
        self.servico_id = servico.id
        self.profissional_id = profissional.id
        self.inicio = datetime.combine(data, hora)
        self.fim = self.inicio + timedelta(minutes=servico.duracao_min)
        if self.preco is None or servico_mudou:
            self.preco = servico.preco

        erros.extend(self._validar_horario(referencia))
        if not erros:
            erros.extend(self._validar_conflitos())
        return erros

    def _validar_horario(self, referencia: datetime) -> list[str]:
        erros = []
        if self.inicio < referencia:
            erros.append("Não é possível agendar em uma data/horário que já passou.")
        if self.inicio.weekday() in DIAS_FECHADOS:
            erros.append(f"O estabelecimento não abre aos {NOMES_DIA[self.inicio.weekday()]}s.")
        abertura = datetime.combine(self.inicio.date(), time(HORA_ABERTURA))
        fechamento = datetime.combine(self.inicio.date(), time(HORA_FECHAMENTO))
        if self.inicio < abertura or self.fim > fechamento:
            erros.append(
                f"Fora do horário de funcionamento ({HORA_ABERTURA:02d}:00 às {HORA_FECHAMENTO:02d}:00). "
                f"Este serviço terminaria às {self.fim:%H:%M}."
            )
        return erros

    def _validar_conflitos(self) -> list[str]:
        erros = []
        # no_autoflush: não grava no banco as alterações ainda não validadas deste objeto
        with db.session.no_autoflush:
            conflito_prof = Agendamento.conflitos(self.inicio, self.fim, profissional_id=self.profissional_id,
                                                  ignorar_id=self.id).first()
            conflito = Agendamento.conflitos(self.inicio, self.fim, cliente_id=self.cliente_id,
                                             ignorar_id=self.id).first()
        if conflito_prof:
            erros.append(
                f"{conflito_prof.profissional.nome} já tem atendimento das {conflito_prof.inicio:%H:%M} às "
                f"{conflito_prof.fim:%H:%M} neste dia. Escolha outro horário ou profissional."
            )
        if conflito:
            erros.append(
                f"O cliente já tem outro agendamento das {conflito.inicio:%H:%M} às {conflito.fim:%H:%M}."
            )
        return erros

    @staticmethod
    def conflitos(inicio, fim, profissional_id=None, cliente_id=None, ignorar_id=None):
        """Agendamentos não cancelados que se sobrepõem ao intervalo [inicio, fim)."""
        consulta = Agendamento.query.filter(
            Agendamento.status != "cancelado",
            Agendamento.inicio < fim,
            Agendamento.fim > inicio,
        )
        if profissional_id is not None:
            consulta = consulta.filter(Agendamento.profissional_id == profissional_id)
        if cliente_id is not None:
            consulta = consulta.filter(Agendamento.cliente_id == cliente_id)
        if ignorar_id is not None:
            consulta = consulta.filter(Agendamento.id != ignorar_id)
        return consulta.order_by(Agendamento.inicio)

    def alterar_status(self, novo: str, referencia: datetime | None = None) -> str | None:
        """Muda o status. Retorna mensagem de erro ou None se deu certo."""
        referencia = referencia or agora()
        if novo not in STATUS_AGENDAMENTO:
            return "Status inválido."
        if novo not in TRANSICOES[self.status]:
            return f"Um agendamento {self.status_rotulo.lower()} não pode passar para {STATUS_AGENDAMENTO[novo].lower()}."
        if novo == "concluido" and self.inicio > referencia:
            return "Só é possível concluir um atendimento depois do horário de início."
        if novo == "agendado":  # reabrir
            if self.inicio < referencia:
                return "Não é possível reabrir: o horário deste agendamento já passou."
            erros = self._validar_conflitos()
            if erros:
                return "Não é possível reabrir: " + erros[0]
        self.status = novo
        return None

    def __repr__(self) -> str:
        return f"<Agendamento {self.id} {self.inicio} {self.status}>"
