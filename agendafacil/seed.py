"""Dados de demonstração. Uso: flask --app agendafacil seed"""
from decimal import Decimal

from .extensions import db
from .models import Cliente, Profissional, Servico

SERVICOS = [
    ("Corte feminino", "Lavagem, corte e finalização", 60, "80.00"),
    ("Corte masculino", "Corte na tesoura ou máquina", 30, "45.00"),
    ("Barba", "Barba com toalha quente", 30, "35.00"),
    ("Escova", "Escova modeladora", 45, "50.00"),
    ("Coloração", "Coloração completa", 120, "180.00"),
    ("Manicure", "Cutilagem e esmaltação", 45, "40.00"),
]
PROFISSIONAIS = [("Ana Souza", "Cabeleireira"), ("Bruno Lima", "Barbeiro"), ("Carla Dias", "Manicure")]
CLIENTES = [
    ("Mariana Alves", "11987654321", "mariana@exemplo.com"),
    ("João Pereira", "11912345678", None),
    ("Fernanda Costa", "1133334444", "fernanda@exemplo.com"),
]


def popular() -> str:
    criados = 0
    for nome, descricao, duracao, preco in SERVICOS:
        if not Servico.query.filter_by(nome=nome).first():
            db.session.add(Servico(nome=nome, descricao=descricao, duracao_min=duracao,
                                   preco=Decimal(preco), ativo=True))
            criados += 1
    for nome, especialidade in PROFISSIONAIS:
        if not Profissional.query.filter_by(nome=nome).first():
            db.session.add(Profissional(nome=nome, especialidade=especialidade, ativo=True))
            criados += 1
    for nome, telefone, email in CLIENTES:
        if not Cliente.query.filter_by(nome=nome).first():
            db.session.add(Cliente(nome=nome, telefone=telefone, email=email))
            criados += 1
    db.session.commit()
    return f"{criados} registro(s) de demonstração criados."
