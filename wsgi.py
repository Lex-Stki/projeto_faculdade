"""Ponto de entrada WSGI para servidores como o gunicorn (usado no Render).

Comando de início: gunicorn wsgi:app
"""
from agendafacil import create_app

app = create_app()
