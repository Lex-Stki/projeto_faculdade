"""Ponto de entrada da função serverless no Vercel.

O vercel.json redireciona todas as requisições para esta função, que expõe
a aplicação Flask na variável `app` (padrão WSGI esperado pelo Vercel).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agendafacil import create_app  # noqa: E402

app = create_app()
