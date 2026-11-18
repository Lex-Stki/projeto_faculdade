"""Testes de integração: requisições HTTP passando por Controller -> Model -> banco -> View."""
from datetime import datetime, timedelta
from io import BytesIO

import pytest

from agendafacil.models import Agendamento, Cliente, Feedback, Servico, Usuario
from agendafacil.utils import agora

from .conftest import SEGUNDA, criar_agendamento, criar_usuario, form_agendamento, logar, mensagens, post

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


# ------------------------------------------------------------------ autenticação e segurança
class TestAutenticacao:
    def test_paginas_internas_exigem_login(self, client):
        for url in ["/", "/clientes/", "/servicos/", "/profissionais/", "/agendamentos/", "/agendamentos/novo"]:
            resposta = client.get(url)
            assert resposta.status_code == 302
            assert "/login" in resposta.headers["Location"]

    def test_primeiro_cadastro_vira_admin_e_os_demais_atendentes(self, client, db):
        dados = {"nome": "Dona", "email": "dona@salao.com", "senha": "123456", "confirmacao": "123456"}
        assert post(client, "/cadastro", dados).status_code == 302
        post(client, "/logout")
        dados.update(nome="Atendente", email="atendente@salao.com")
        post(client, "/cadastro", dados)
        perfis = {u.email: u.perfil for u in Usuario.query.all()}
        assert perfis == {"dona@salao.com": "admin", "atendente@salao.com": "atendente"}

    def test_cadastro_fechado_bloqueia_novas_contas(self, app, client, admin):
        app.config["CADASTRO_ABERTO"] = False
        resposta = client.get("/cadastro", follow_redirects=True)
        assert "O cadastro de novas contas está fechado" in mensagens(resposta)[0]
        post(client, "/cadastro", {"nome": "Intruso", "email": "x@x.com", "senha": "123456", "confirmacao": "123456"})
        assert Usuario.query.count() == 1

    def test_cadastro_com_erro_mantem_dados_digitados(self, client, db):
        resposta = post(client, "/cadastro", {"nome": "Dona", "email": "dona@salao.com",
                                              "senha": "123", "confirmacao": "123"})
        assert resposta.status_code == 200
        assert "A senha precisa ter pelo menos 6 caracteres." in mensagens(resposta)
        assert 'value="dona@salao.com"' in resposta.get_data(as_text=True)

    def test_login_com_senha_errada(self, client, admin):
        resposta = post(client, "/login", {"email": admin.email, "senha": "errada"})
        assert "E-mail ou senha incorretos." in mensagens(resposta)

    def test_login_redireciona_para_pagina_pedida(self, client, admin):
        resposta = post(client, "/login?proximo=/clientes/", {"email": "ADMIN@teste.com", "senha": "segredo1"})
        assert resposta.headers["Location"] == "/clientes/"

    def test_login_bloqueia_redirecionamento_externo(self, client, admin):
        resposta = post(client, "/login?proximo=//malicioso.com", {"email": admin.email, "senha": "segredo1"})
        assert resposta.headers["Location"] == "/"

    def test_logout(self, logado):
        post(logado, "/logout")
        assert logado.get("/").status_code == 302

    def test_post_sem_csrf_e_recusado(self, logado, db):
        resposta = logado.post("/clientes/novo", data={"nome": "Sem token", "telefone": "11999999999"})
        assert resposta.status_code == 400
        assert Cliente.query.count() == 0

    def test_cabecalhos_de_seguranca(self, client):
        resposta = client.get("/login")
        assert resposta.headers["X-Frame-Options"] == "DENY"
        assert resposta.headers["X-Content-Type-Options"] == "nosniff"


# ------------------------------------------------------------------ clientes
class TestClientes:
    def test_crud_completo(self, logado, db):
        resposta = post(logado, "/clientes/novo", {"nome": "Mariana", "telefone": "(11) 98765-4321"},
                        follow_redirects=True)
        assert "Cliente “Mariana” cadastrado." in mensagens(resposta)
        cliente = Cliente.query.one()
        assert cliente.telefone == "11987654321"

        resposta = post(logado, f"/clientes/{cliente.id}/editar",
                        {"nome": "Mariana Alves", "telefone": "11987654321", "email": "m@ex.com"},
                        follow_redirects=True)
        assert "Dados do cliente atualizados." in mensagens(resposta)
        assert db.session.get(Cliente, cliente.id).nome == "Mariana Alves"

        resposta = post(logado, f"/clientes/{cliente.id}/excluir", follow_redirects=True)
        assert "Cliente “Mariana Alves” excluído." in mensagens(resposta)
        assert Cliente.query.count() == 0

    def test_salvar_e_agendar_vai_para_o_formulario_de_agendamento(self, logado, db):
        resposta = post(logado, "/clientes/novo", {"nome": "Mariana", "telefone": "11987654321", "agendar": "1"})
        cliente = Cliente.query.one()
        assert resposta.headers["Location"] == f"/agendamentos/novo?cliente_id={cliente.id}"

    def test_edicao_invalida_nao_altera_o_banco(self, logado, base, db):
        cliente = base["cliente"]
        resposta = post(logado, f"/clientes/{cliente.id}/editar", {"nome": "X", "telefone": "123"})
        assert resposta.status_code == 200
        assert len(mensagens(resposta)) == 2
        db.session.expire_all()
        assert db.session.get(Cliente, cliente.id).nome == "Mariana Alves"

    def test_busca_por_nome_e_telefone(self, logado, base):
        assert "Mariana Alves" in logado.get("/clientes/?q=mari").get_data(as_text=True)
        pagina = logado.get("/clientes/?q=91234").get_data(as_text=True)
        assert "João Pereira" in pagina and "Mariana Alves" not in pagina

    def test_busca_sem_resultado_oferece_cadastro(self, logado, base):
        pagina = logado.get("/clientes/?q=Zuleica").get_data(as_text=True)
        assert "Nenhum cliente encontrado" in pagina
        assert "/clientes/novo?nome=Zuleica" in pagina

    def test_nao_exclui_cliente_com_historico(self, logado, base, db):
        criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        resposta = post(logado, f"/clientes/{base['cliente'].id}/excluir", follow_redirects=True)
        assert "não pode ser excluído" in mensagens(resposta)[0]
        assert Cliente.query.count() == 2

    def test_cliente_inexistente_404(self, logado):
        resposta = logado.get("/clientes/999")
        assert resposta.status_code == 404
        assert "Página não encontrada" in resposta.get_data(as_text=True)

    def test_paginacao(self, logado, db):
        for i in range(15):
            db.session.add(Cliente(nome=f"Cliente {i:02d}", telefone="11999999999"))
        db.session.commit()
        pagina2 = logado.get("/clientes/?pagina=2").get_data(as_text=True)
        assert "Página 2 de 2" in pagina2
        assert "Cliente 14" in pagina2


# ------------------------------------------------------------------ serviços e profissionais
class TestServicosEProfissionais:
    def test_cadastrar_servico(self, logado, db):
        resposta = post(logado, "/servicos/novo", {"nome": "Barba", "duracao_min": "30", "preco": "35,00"},
                        follow_redirects=True)
        assert "Serviço “Barba” cadastrado." in mensagens(resposta)
        assert "R$ 35,00" in resposta.get_data(as_text=True)

    def test_renomear_para_nome_existente_nao_quebra(self, logado, base, db):
        post(logado, "/servicos/novo", {"nome": "Barba", "duracao_min": "30", "preco": "35"})
        resposta = post(logado, f"/servicos/{base['servico'].id}/editar",
                        {"nome": "Barba", "duracao_min": "60", "preco": "80"})
        assert resposta.status_code == 200
        assert "Já existe um serviço com este nome." in mensagens(resposta)
        db.session.expire_all()
        assert Servico.query.filter_by(nome="Corte").count() == 1

    def test_desativar_e_reativar_servico(self, logado, base, db):
        sid = base["servico"].id
        post(logado, f"/servicos/{sid}/alternar")
        assert db.session.get(Servico, sid).ativo is False
        assert "Corte · 60 min" not in logado.get("/agendamentos/novo").get_data(as_text=True)
        post(logado, f"/servicos/{sid}/alternar")
        assert db.session.get(Servico, sid).ativo is True

    def test_nao_exclui_servico_usado(self, logado, base, db):
        criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        resposta = post(logado, f"/servicos/{base['servico'].id}/excluir", follow_redirects=True)
        assert "Use “Desativar”" in mensagens(resposta)[0]

    def test_crud_profissional(self, logado, db):
        post(logado, "/profissionais/novo", {"nome": "Carla", "especialidade": "Manicure"})
        from agendafacil.models import Profissional

        p = Profissional.query.one()
        post(logado, f"/profissionais/{p.id}/editar", {"nome": "Carla Dias", "especialidade": ""})
        assert db.session.get(Profissional, p.id).nome == "Carla Dias"
        post(logado, f"/profissionais/{p.id}/alternar")
        assert db.session.get(Profissional, p.id).ativo is False
        post(logado, f"/profissionais/{p.id}/excluir")
        assert Profissional.query.count() == 0


# ------------------------------------------------------------------ agendamentos
class TestAgendamentos:
    def test_criar_e_listar_no_dia(self, logado, base):
        resposta = post(logado, "/agendamentos/novo", form_agendamento(base), follow_redirects=True)
        assert "Agendamento criado para 07/01/2030 às 10:00." in mensagens(resposta)
        pagina = resposta.get_data(as_text=True)
        assert "Mariana Alves" in pagina and "10:00–11:00" in pagina
        assert Agendamento.query.one().criado_por_id is not None

    def test_conflito_mostra_mensagem_e_mantem_formulario(self, logado, base, db):
        criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        resposta = post(logado, "/agendamentos/novo",
                        form_agendamento(base, hora="10:30", cliente="outro_cliente", observacoes="Teste"))
        assert resposta.status_code == 200
        assert "Ana Souza já tem atendimento" in mensagens(resposta)[0]
        assert "Teste</textarea>" in resposta.get_data(as_text=True)
        assert Agendamento.query.count() == 1

    def test_remarcar(self, logado, base, db):
        a = criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        resposta = post(logado, f"/agendamentos/{a.id}/editar", form_agendamento(base, hora="14:00"),
                        follow_redirects=True)
        assert "Agendamento remarcado/atualizado." in mensagens(resposta)
        assert db.session.get(Agendamento, a.id).inicio == datetime(2030, 1, 7, 14, 0)

    def test_remarcacao_invalida_nao_altera_o_banco(self, logado, base, db):
        a = criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        post(logado, f"/agendamentos/{a.id}/editar", form_agendamento(base, hora="21:00"))
        db.session.expire_all()
        assert db.session.get(Agendamento, a.id).inicio == datetime(2030, 1, 7, 10, 0)

    def test_nao_edita_cancelado(self, logado, base, db):
        a = criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0), status="cancelado")
        resposta = logado.get(f"/agendamentos/{a.id}/editar", follow_redirects=True)
        assert "não podem ser alterados" in mensagens(resposta)[0]

    def test_cancelar_reabrir_e_concluir(self, logado, base, db):
        a = criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        post(logado, f"/agendamentos/{a.id}/status", {"status": "cancelado"})
        assert db.session.get(Agendamento, a.id).status == "cancelado"
        post(logado, f"/agendamentos/{a.id}/status", {"status": "agendado"})
        assert db.session.get(Agendamento, a.id).status == "agendado"

        passado = criar_agendamento(db, base, agora() - timedelta(hours=2), cliente="outro_cliente",
                                    profissional="bruno")
        resposta = post(logado, f"/agendamentos/{passado.id}/status",
                        {"status": "concluido", "voltar_para": "/"})
        assert resposta.headers["Location"] == "/"
        assert db.session.get(Agendamento, passado.id).status == "concluido"

    def test_filtros_da_agenda(self, logado, base, db):
        criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        criar_agendamento(db, base, datetime(2030, 1, 8, 10, 0), profissional="bruno", status="cancelado")
        pagina = logado.get(f"/agendamentos/?data={SEGUNDA}").get_data(as_text=True)
        assert "07/01/2030" in pagina and "08/01/2030" not in pagina
        pagina = logado.get(f"/agendamentos/?profissional_id={base['bruno'].id}").get_data(as_text=True)
        assert "08/01/2030" in pagina and "07/01/2030" not in pagina
        pagina = logado.get("/agendamentos/?status=agendado").get_data(as_text=True)
        assert "07/01/2030" in pagina and "08/01/2030" not in pagina

    def test_passados_so_aparecem_com_periodo_todos(self, logado, base, db):
        criar_agendamento(db, base, datetime(2020, 3, 2, 10, 0), status="concluido")
        assert "02/03/2020" not in logado.get("/agendamentos/").get_data(as_text=True)
        assert "02/03/2020" in logado.get("/agendamentos/?periodo=todos").get_data(as_text=True)

    def test_disponibilidade_json(self, logado, base, db):
        criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        dados = logado.get(f"/agendamentos/disponibilidade?profissional_id={base['ana'].id}&data={SEGUNDA}").json
        assert dados["ocupados"] == [{"inicio": "10:00", "fim": "11:00", "servico": "Corte"}]
        assert dados["fechado"] is False
        assert logado.get("/agendamentos/disponibilidade?data=x").status_code == 400

    @pytest.mark.parametrize("agora_simulado,data_esperada", [
        (datetime(2030, 1, 7, 9, 0), "2030-01-07"),    # segunda de manhã: hoje
        (datetime(2030, 1, 7, 19, 55), "2030-01-08"),  # segunda após o último horário: terça (D8)
        (datetime(2030, 1, 5, 19, 55), "2030-01-07"),  # sábado à noite: pula o domingo
    ])
    def test_novo_agendamento_abre_no_proximo_dia_com_horario(self, logado, base, monkeypatch,
                                                                 agora_simulado, data_esperada):
        import agendafacil.controllers.agendamentos as ctrl
        import agendafacil.models.agendamento as modelo

        monkeypatch.setattr(modelo, "agora", lambda: agora_simulado)
        monkeypatch.setattr(ctrl, "hoje", lambda: agora_simulado.date())
        pagina = logado.get("/agendamentos/novo").get_data(as_text=True)
        assert f'name="data" type="date" value="{data_esperada}"' in pagina

    def test_disponibilidade_devolve_horarios_com_motivo(self, logado, base, db):
        criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        url = (f"/agendamentos/disponibilidade?data={SEGUNDA}&profissional_id={base['ana'].id}"
               f"&servico_id={base['servico'].id}")
        horarios = {h["hora"]: h for h in logado.get(url).json["horarios"]}
        assert horarios["10:30"]["livre"] is False
        assert horarios["10:30"]["motivo"] == "Ana Souza ocupado(a) 10:00–11:00"
        assert horarios["11:00"]["livre"] is True
        assert logado.get("/agendamentos/disponibilidade").status_code == 400

    def test_formulario_ja_vem_com_horarios_bloqueados_sem_javascript(self, logado, base, db):
        criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        outro = criar_agendamento(db, base, datetime(2030, 1, 7, 14, 0), cliente="outro_cliente")
        pagina = logado.get(f"/agendamentos/{outro.id}/editar").get_data(as_text=True)
        assert '<select id="hora"' in pagina
        assert "indisponível: Ana Souza ocupado(a) 10:00–11:00" in pagina
        assert 'value="14:00"' in pagina and "selected" in pagina.split('value="14:00"')[1][:120]

    def test_remarcar_mantem_horario_fora_da_grade(self, logado, base, db):
        a = criar_agendamento(db, base, datetime(2030, 1, 7, 8, 35))
        pagina = logado.get(f"/agendamentos/{a.id}/editar").get_data(as_text=True)
        assert 'value="08:35"' in pagina

    def test_dashboard_mostra_agenda_de_hoje(self, logado, base, db):
        criar_agendamento(db, base, agora() + timedelta(minutes=30))
        pagina = logado.get("/").get_data(as_text=True)
        assert "Mariana Alves" in pagina
        assert "R$ 80,00" in pagina


    def test_painel_mostra_vendas_concluidas(self, logado, base, db):
        criar_agendamento(db, base, agora() - timedelta(hours=3), status="concluido")
        pagina = logado.get("/").get_data(as_text=True)
        assert "Faturamento por dia" in pagina
        assert pagina.count('class="grafico-faixa"') == 7
        assert 'data-dica-valor="R$ 80,00"' in pagina
        assert "Ver os dados em tabela" in pagina

    def test_painel_sem_vendas_explica_o_que_fazer(self, logado, base):
        pagina = logado.get("/").get_data(as_text=True)
        assert "Nenhum atendimento concluído nos últimos 7 dias." in pagina


# ------------------------------------------------------------------ laudos de teste (feedback)
class TestFeedback:
    def test_formulario_publico_com_print(self, client, db):
        dados = {"nome_testador": "Carlos", "data_teste": "2020-05-10", "nao_funcionou": "Botão X",
                 "avaliacao": "4", "screenshot": (BytesIO(PNG), "erro.png")}
        resposta = post(client, "/feedback/", dados, content_type="multipart/form-data")
        assert resposta.headers["Location"] == "/feedback/obrigado"
        f = Feedback.query.one()
        assert f.screenshot == PNG and f.avaliacao == 4

    def test_formulario_com_erro(self, client, db):
        resposta = post(client, "/feedback/", {"nome_testador": "", "data_teste": ""})
        assert len(mensagens(resposta)) == 3
        assert Feedback.query.count() == 0

    def test_somente_admin_ve_laudos(self, client, db):
        atendente = criar_usuario(nome="At", email="at@teste.com", perfil="atendente")
        logar(client, atendente)
        assert client.get("/feedback/recebidos").status_code == 403

    def test_admin_lista_ve_print_e_exporta_csv(self, logado, db):
        f = Feedback(nome_testador="Carlos", data_teste=datetime(2020, 5, 10).date(), funcionou="Tudo",
                     screenshot=PNG, screenshot_mime="image/png")
        db.session.add(f)
        db.session.commit()
        assert "Carlos" in logado.get("/feedback/recebidos").get_data(as_text=True)
        imagem = logado.get(f"/feedback/{f.id}/screenshot")
        assert imagem.mimetype == "image/png" and imagem.data == PNG
        csv = logado.get("/feedback/exportar.csv")
        assert csv.mimetype == "text/csv"
        assert "Carlos;" in csv.get_data(as_text=True)
        post(logado, f"/feedback/{f.id}/excluir")
        assert Feedback.query.count() == 0


# ------------------------------------------------------------------ diversos
def test_saude(client):
    assert client.get("/saude").json == {"status": "ok", "banco": "ok"}


def test_dados_de_exemplo(logado, db):
    resposta = post(logado, "/dados-exemplo", follow_redirects=True)
    assert "registro(s) de demonstração criados" in mensagens(resposta)[0]
    assert Servico.query.count() == 6
    post(logado, "/dados-exemplo")  # idempotente
    assert Servico.query.count() == 6


def test_arquivo_muito_grande_retorna_413(client):
    grande = BytesIO(b"0" * (3 * 1024 * 1024))
    resposta = post(client, "/feedback/", {"screenshot": (grande, "x.png")}, content_type="multipart/form-data")
    assert resposta.status_code == 413
    assert "2 MB" in resposta.get_data(as_text=True)
