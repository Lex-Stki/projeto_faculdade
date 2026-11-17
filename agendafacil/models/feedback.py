from ..config import TAMANHO_MAX_SCREENSHOT
from ..extensions import db
from ..utils import agora, email_valido, hoje, parse_data, parse_int

# Assinaturas (magic bytes) dos formatos de imagem aceitos
ASSINATURAS = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
}

CAMPOS_TEXTO = ("funcionou", "nao_funcionou", "nao_testado", "sugestoes")


def detectar_imagem(conteudo: bytes) -> str | None:
    for assinatura, mime in ASSINATURAS.items():
        if conteudo.startswith(assinatura):
            return mime
    if conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
        return "image/webp"
    return None


class Feedback(db.Model):
    """Laudo de teste preenchido por um testador (colega de curso) — Situação-Problema 3."""

    __tablename__ = "feedback"
    __table_args__ = (
        db.CheckConstraint("avaliacao IS NULL OR avaliacao BETWEEN 1 AND 5", name="ck_feedback_avaliacao"),
    )

    id = db.Column(db.Integer, primary_key=True)
    nome_testador = db.Column(db.String(100), nullable=False)
    email_testador = db.Column(db.String(120), nullable=True)
    data_teste = db.Column(db.Date, nullable=False)
    funcionou = db.Column(db.Text, nullable=True)
    nao_funcionou = db.Column(db.Text, nullable=True)
    nao_testado = db.Column(db.Text, nullable=True)
    sugestoes = db.Column(db.Text, nullable=True)
    avaliacao = db.Column(db.SmallInteger, nullable=True)
    screenshot = db.Column(db.LargeBinary, nullable=True)
    screenshot_mime = db.Column(db.String(30), nullable=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    def preencher(self, dados: dict, arquivo=None) -> list[str]:
        self.nome_testador = (dados.get("nome_testador") or "").strip()
        self.email_testador = (dados.get("email_testador") or "").strip().lower() or None
        self.data_teste = parse_data(dados.get("data_teste"))
        for campo in CAMPOS_TEXTO:
            setattr(self, campo, (dados.get(campo) or "").strip() or None)
        self.avaliacao = parse_int(dados.get("avaliacao"))

        erros = []
        if not 2 <= len(self.nome_testador) <= 100:
            erros.append("Informe seu nome (entre 2 e 100 caracteres).")
        if self.email_testador and (not email_valido(self.email_testador) or len(self.email_testador) > 120):
            erros.append("E-mail inválido.")
        if self.data_teste is None:
            erros.append("Informe a data do teste.")
        elif self.data_teste > hoje():
            erros.append("A data do teste não pode estar no futuro.")
        if not any(getattr(self, c) for c in CAMPOS_TEXTO):
            erros.append("Descreva pelo menos o que funcionou ou o que não funcionou.")
        for campo in CAMPOS_TEXTO:
            valor = getattr(self, campo)
            if valor and len(valor) > 5000:
                erros.append("Cada campo de texto pode ter no máximo 5000 caracteres.")
                break
        if self.avaliacao is not None and not 1 <= self.avaliacao <= 5:
            erros.append("A avaliação deve ser de 1 a 5.")

        if arquivo is not None and arquivo.filename:
            conteudo = arquivo.read()
            if len(conteudo) > TAMANHO_MAX_SCREENSHOT:
                erros.append("A imagem deve ter no máximo 2 MB.")
            else:
                mime = detectar_imagem(conteudo)
                if mime is None:
                    erros.append("O arquivo enviado não é uma imagem PNG, JPG, GIF ou WEBP.")
                else:
                    self.screenshot = conteudo
                    self.screenshot_mime = mime
        return erros
