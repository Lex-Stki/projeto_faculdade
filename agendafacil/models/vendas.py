"""Indicadores de vendas do painel (sugestão da testadora Vitória).

Considera apenas atendimentos **concluídos**: é o que de fato foi vendido. O preço usado é o
gravado no agendamento (RN07), então reajustes de serviço não alteram o passado.
"""
import math
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy.orm import joinedload

from .agendamento import Agendamento

DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
DIAS_NO_GRAFICO = 7
TOP_SERVICOS = 5


def _eixo(maximo: Decimal) -> list[int]:
    """Marcas do eixo Y em números redondos (passo 1, 2, 2,5 ou 5 × 10ⁿ), começando em zero."""
    if maximo <= 0:
        return [0]
    bruto = float(maximo) / 3
    ordem = 10 ** math.floor(math.log10(bruto))
    passo = next(m * ordem for m in (1, 2, 2.5, 5, 10) if m * ordem >= bruto)
    passos = math.ceil(float(maximo) / passo)
    return [round(passo * i) for i in range(passos + 1)]


def resumo_vendas(hoje: date) -> dict:
    inicio_grafico = hoje - timedelta(days=DIAS_NO_GRAFICO - 1)
    inicio_mes = hoje.replace(day=1)
    desde = datetime.combine(min(inicio_grafico, inicio_mes), time.min)
    ate = datetime.combine(hoje + timedelta(days=1), time.min)

    concluidos = (
        Agendamento.query.options(joinedload(Agendamento.servico))
        .filter(Agendamento.status == "concluido", Agendamento.inicio >= desde, Agendamento.inicio < ate)
        .all()
    )

    por_dia = defaultdict(lambda: [Decimal("0"), 0])
    por_servico = defaultdict(lambda: [Decimal("0"), 0])
    total_mes, qtd_mes = Decimal("0"), 0
    for a in concluidos:
        dia = a.inicio.date()
        por_dia[dia][0] += a.preco
        por_dia[dia][1] += 1
        if dia >= inicio_mes:
            total_mes += a.preco
            qtd_mes += 1
            por_servico[a.servico.nome][0] += a.preco
            por_servico[a.servico.nome][1] += 1

    dias = []
    for i in range(DIAS_NO_GRAFICO):
        dia = inicio_grafico + timedelta(days=i)
        valor, qtd = por_dia.get(dia, (Decimal("0"), 0))
        dias.append({"data": dia, "rotulo": f"{DIAS_SEMANA[dia.weekday()]} {dia.day:02d}",
                     "valor": valor, "qtd": qtd, "hoje": dia == hoje})
    maior = max((d["valor"] for d in dias), default=Decimal("0"))
    eixo = _eixo(maior)
    topo = eixo[-1] or 1
    for d in dias:
        d["altura"] = round(float(d["valor"]) / topo * 100, 1)
        d["destaque"] = maior > 0 and d["valor"] == maior

    servicos = sorted(por_servico.items(), key=lambda item: item[1][0], reverse=True)[:TOP_SERVICOS]
    maior_servico = servicos[0][1][0] if servicos else Decimal("1")
    return {
        "total_mes": total_mes,
        "qtd_mes": qtd_mes,
        "ticket_medio": (total_mes / qtd_mes) if qtd_mes else None,
        "dias": dias,
        "eixo": [{"valor": v, "posicao": round(v / topo * 100, 1)} for v in eixo],
        "total_periodo": sum((d["valor"] for d in dias), Decimal("0")),
        "servicos": [{"nome": nome, "valor": v, "qtd": q, "largura": round(float(v / maior_servico) * 100, 1)}
                     for nome, (v, q) in servicos],
        "mes_rotulo": f"{inicio_mes:%m/%Y}",
    }
