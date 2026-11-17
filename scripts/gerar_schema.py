"""Gera docs/situacao-1/schema.sql (DDL PostgreSQL) a partir dos Models.

Assim o projeto físico documentado é sempre igual ao que a aplicação cria.
Uso: python scripts/gerar_schema.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from sqlalchemy.dialects import postgresql  # noqa: E402
from sqlalchemy.schema import CreateIndex, CreateTable  # noqa: E402

from agendafacil.extensions import db  # noqa: E402
import agendafacil.models  # noqa: E402,F401  (registra as tabelas)

dialeto = postgresql.dialect()
partes = [
    "-- AgendaFácil: projeto físico do banco de dados (PostgreSQL)",
    "-- Gerado automaticamente por scripts/gerar_schema.py a partir dos Models. Não edite à mão.",
    "",
]
for tabela in db.metadata.sorted_tables:
    partes.append(str(CreateTable(tabela).compile(dialect=dialeto)).strip() + ";")
    for indice in sorted(tabela.indexes, key=lambda i: i.name):
        partes.append(str(CreateIndex(indice).compile(dialect=dialeto)).strip() + ";")
    partes.append("")

destino = RAIZ / "docs" / "situacao-1" / "schema.sql"
destino.write_text("\n".join(partes), encoding="utf-8")
print(f"Gerado {destino.relative_to(RAIZ)}")
