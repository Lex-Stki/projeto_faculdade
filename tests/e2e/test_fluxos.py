"""Testes ponta a ponta (E2E): sobem o servidor de verdade e usam um navegador real.

Validam o front-end (HTML + CSS + JavaScript) junto com o back-end.
Requisitos: pip install playwright  e  Microsoft Edge ou Google Chrome instalado
(ou `playwright install chromium`). Sem isso, os testes são ignorados (skip).

Para salvar as capturas de tela usadas no laudo:
  E2E_EVIDENCIAS=1 pytest tests/e2e
"""
import os
import threading
from pathlib import Path

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")

from werkzeug.serving import make_server  # noqa: E402

from agendafacil import create_app  # noqa: E402

PASTA_EVIDENCIAS = Path(__file__).resolve().parents[2] / "docs" / "situacao-3" / "evidencias"
SALVAR = bool(os.environ.get("E2E_EVIDENCIAS"))
SEGUNDA = "2030-01-07"


@pytest.fixture(scope="module")
def servidor(tmp_path_factory):
    banco = tmp_path_factory.mktemp("e2e") / "e2e.db"
    app = create_app({"TESTING": True, "SECRET_KEY": "e2e",
                      "SQLALCHEMY_DATABASE_URI": f"sqlite:///{banco.as_posix()}"})
    srv = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


@pytest.fixture(scope="module")
def navegador():
    with playwright_api.sync_playwright() as p:
        browser = None
        for canal in ("msedge", "chrome", None):
            try:
                browser = p.chromium.launch(channel=canal) if canal else p.chromium.launch()
                break
            except Exception:
                continue
        if browser is None:
            pytest.skip("Nenhum navegador Chromium disponível para os testes E2E.")
        yield browser
        browser.close()


@pytest.fixture
def pagina(navegador):
    contexto = navegador.new_context(viewport={"width": 1280, "height": 860}, locale="pt-BR")
    page = contexto.new_page()
    yield page
    contexto.close()


def evidencia(page, nome, pagina_inteira=True):
    if SALVAR:
        PASTA_EVIDENCIAS.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(PASTA_EVIDENCIAS / f"{nome}.png"), full_page=pagina_inteira)


def alerta(page) -> str:
    return page.locator(".mensagens").inner_text()


def test_fluxo_completo(servidor, pagina):
    page = pagina
    erros_js = []
    page.on("pageerror", lambda e: erros_js.append(str(e)))

    # 1. Cadastro do primeiro usuário (vira admin)
    page.goto(servidor + "/")
    assert "/login" in page.url
    evidencia(page, "01-login")
    page.click("text=Crie uma agora")
    page.fill("#nome", "Dona do Salão")
    page.fill("#email", "dona@salao.com")
    page.fill("#senha", "123456")
    page.fill("#confirmacao", "654321")
    page.click("button[type=submit]")
    assert page.locator("#confirmacao-erro").inner_text() == "As senhas não conferem."
    page.fill("#confirmacao", "123456")
    page.click("button[type=submit]")
    assert "administrador" in alerta(page)
    evidencia(page, "02-primeiros-passos")

    # 2. Dados de exemplo
    page.click("text=Carregar dados de exemplo")
    assert "demonstração criados" in alerta(page)

    # 3. Validação no navegador + máscara de telefone
    page.click("nav >> text=Clientes")
    page.click("text=+ Novo cliente")
    page.click("button:has-text('Salvar e agendar')")
    assert page.locator("#nome-erro").inner_text() == "Campo obrigatório."
    assert page.locator("#telefone-erro").inner_text() == "Campo obrigatório."
    evidencia(page, "03-validacao-formulario")
    page.fill("#nome", "Paula Teste")
    page.locator("#telefone").press_sequentially("11987654321")
    assert page.input_value("#telefone") == "(11) 98765-4321"

    # 4. Salvar e agendar: formulário de agendamento já com o cliente escolhido
    page.click("button:has-text('Salvar e agendar')")
    assert "/agendamentos/novo" in page.url
    assert page.locator("#cliente_id option:checked").inner_text().startswith("Paula Teste")
    page.select_option("#servico_id", label="Corte feminino · 60 min · R$ 80,00")
    page.select_option("#profissional_id", index=1)
    page.fill("#data", SEGUNDA)
    page.fill("#hora", "10:00")
    page.dispatch_event("#data", "change")
    assert page.locator("#previsao-termino").inner_text() == "Término previsto: 11:00 (60 min)"
    page.wait_for_selector("#painel-disponibilidade:has-text('livre o dia todo')")
    evidencia(page, "04-formulario-agendamento")
    page.click("button:has-text('Salvar agendamento')")
    assert "Agendamento criado para 07/01/2030 às 10:00." in alerta(page)
    evidencia(page, "05-agenda-do-dia")

    # 5. Conflito de horário: mensagem do servidor e painel de horários ocupados
    page.goto(servidor + "/agendamentos/novo")
    page.select_option("#cliente_id", index=1)
    page.select_option("#servico_id", index=2)
    page.select_option("#profissional_id", index=1)
    page.fill("#data", SEGUNDA)
    page.dispatch_event("#data", "change")
    page.wait_for_selector("#painel-disponibilidade li:has-text('10:00–11:00')")
    page.fill("#hora", "10:30")
    page.click("button:has-text('Salvar agendamento')")
    assert "já tem atendimento das 10:00 às 11:00" in alerta(page)
    evidencia(page, "06-conflito-de-horario")

    # 6. Cancelar com diálogo de confirmação e depois reabrir (ação reversível)
    page.goto(servidor + f"/agendamentos/?data={SEGUNDA}")
    page.click("button:has-text('Cancelar')")
    assert page.locator("#dialogo-confirmar").is_visible()
    evidencia(page, "07-dialogo-confirmacao", pagina_inteira=False)
    page.click("#dialogo-ok")
    assert "Agendamento cancelado" in alerta(page)
    assert page.locator(".selo-cancelado").count() == 1
    page.click("button:has-text('Reabrir')")
    assert "Agendamento reaberto." in alerta(page)

    # 7. Layout no celular
    page.set_viewport_size({"width": 390, "height": 844})
    page.reload()
    assert page.locator("#menu").is_hidden()
    page.click("[data-menu]")
    assert page.locator("#menu").is_visible()
    evidencia(page, "08-agenda-no-celular")
    page.set_viewport_size({"width": 1280, "height": 860})

    # 8. Laudo de teste (público) e lista de laudos (admin)
    page.goto(servidor + "/feedback/")
    page.fill("#nome_testador", "Colega Testador")
    page.fill("#funcionou", "Cadastro de cliente e agendamento.")
    page.fill("#nao_funcionou", "Exemplo de problema encontrado.")
    page.check("input[name=avaliacao][value='4']")
    page.click("button:has-text('Enviar laudo')")
    assert "Laudo enviado!" in page.inner_text("h1")
    page.goto(servidor + "/feedback/recebidos")
    assert "Colega Testador" in page.inner_text("main")
    evidencia(page, "09-laudos-recebidos")

    assert erros_js == [], f"Erros de JavaScript: {erros_js}"


def test_pagina_404_amigavel(servidor, pagina):
    resposta = pagina.goto(servidor + "/nao-existe")
    assert resposta.status == 404
    assert "Página não encontrada" in pagina.inner_text("h1")
    evidencia(pagina, "10-erro-404", pagina_inteira=False)
