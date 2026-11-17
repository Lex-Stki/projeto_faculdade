"""Testes de unidade da camada Model (regras de negócio e validações)."""
from datetime import datetime
from decimal import Decimal
from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from agendafacil.models import Agendamento, Cliente, Feedback, Servico, Usuario
from agendafacil.models.feedback import detectar_imagem

from .conftest import DOMINGO, REFERENCIA, SEGUNDA, criar_agendamento, criar_usuario, form_agendamento

PNG_MINIMO = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


# ------------------------------------------------------------------ Usuario
class TestUsuario:
    def test_senha_e_guardada_como_hash(self, db):
        usuario = criar_usuario(senha="minhasenha")
        assert usuario.senha_hash != "minhasenha"
        assert usuario.verificar_senha("minhasenha")
        assert not usuario.verificar_senha("errada")

    def test_cadastro_valido(self, db):
        assert Usuario.validar_cadastro("Ana", "ana@teste.com", "123456", "123456") == []

    @pytest.mark.parametrize("nome,email,senha,confirmacao,trecho", [
        ("A", "ana@teste.com", "123456", "123456", "nome"),
        ("Ana", "ana@", "123456", "123456", "e-mail válido"),
        ("Ana", "ana@teste.com", "123", "123", "6 caracteres"),
        ("Ana", "ana@teste.com", "123456", "654321", "não confere"),
    ])
    def test_cadastro_invalido(self, db, nome, email, senha, confirmacao, trecho):
        erros = Usuario.validar_cadastro(nome, email, senha, confirmacao)
        assert any(trecho in e for e in erros)

    def test_email_duplicado_ignora_maiusculas(self, db):
        criar_usuario(email="ana@teste.com")
        erros = Usuario.validar_cadastro("Ana", "ANA@teste.com", "123456", "123456")
        assert any("Já existe" in e for e in erros)


# ------------------------------------------------------------------ Cliente
class TestCliente:
    def test_normaliza_telefone_e_email(self, db):
        cliente = Cliente()
        erros = cliente.preencher({"nome": " Mariana ", "telefone": "(11) 98765-4321", "email": "MARI@Ex.com "})
        assert erros == []
        assert cliente.nome == "Mariana"
        assert cliente.telefone == "11987654321"
        assert cliente.email == "mari@ex.com"

    @pytest.mark.parametrize("telefone", ["", "98765-4321", "119876543210"])
    def test_telefone_invalido(self, db, telefone):
        erros = Cliente().preencher({"nome": "Mariana", "telefone": telefone})
        assert any("Telefone" in e for e in erros)

    def test_email_opcional_mas_validado(self, db):
        assert Cliente().preencher({"nome": "Mariana", "telefone": "1133334444"}) == []
        erros = Cliente().preencher({"nome": "Mariana", "telefone": "1133334444", "email": "sem-arroba"})
        assert any("E-mail" in e for e in erros)


# ------------------------------------------------------------------ Servico
class TestServico:
    @pytest.mark.parametrize("texto,esperado", [
        ("35", Decimal("35.00")),
        ("35,5", Decimal("35.50")),
        ("R$ 1.234,56", Decimal("1234.56")),
        ("49.90", Decimal("49.90")),
    ])
    def test_aceita_formatos_de_preco(self, db, texto, esperado):
        servico = Servico()
        assert servico.preencher({"nome": "Corte", "duracao_min": "30", "preco": texto}) == []
        assert servico.preco == esperado

    @pytest.mark.parametrize("duracao", ["0", "4", "481", "abc", ""])
    def test_duracao_fora_do_intervalo(self, db, duracao):
        erros = Servico().preencher({"nome": "Corte", "duracao_min": duracao, "preco": "10"})
        assert any("Duração" in e for e in erros)

    @pytest.mark.parametrize("preco", ["abc", "-5", ""])
    def test_preco_invalido(self, db, preco):
        erros = Servico().preencher({"nome": "Corte", "duracao_min": "30", "preco": preco})
        assert any("Preço" in e for e in erros)

    def test_nome_duplicado(self, db, base):
        erros = Servico().preencher({"nome": "corte", "duracao_min": "30", "preco": "10"})
        assert "Já existe um serviço com este nome." in erros

    def test_pode_manter_o_proprio_nome_ao_editar(self, db, base):
        assert base["servico"].preencher({"nome": "Corte", "duracao_min": "45", "preco": "90"}) == []


# ------------------------------------------------------------------ Agendamento
class TestAgendamento:
    def test_calcula_fim_e_copia_preco(self, db, base):
        a = Agendamento()
        assert a.definir(form_agendamento(base), referencia=REFERENCIA) == []
        assert a.inicio == datetime(2030, 1, 7, 10, 0)
        assert a.fim == datetime(2030, 1, 7, 11, 0)
        assert a.preco == Decimal("80.00")

    def test_campos_obrigatorios(self, db, base):
        erros = Agendamento().definir({}, referencia=REFERENCIA)
        assert len(erros) == 5  # cliente, serviço, profissional, data, hora

    def test_nao_agenda_no_passado(self, db, base):
        erros = Agendamento().definir(form_agendamento(base), referencia=datetime(2030, 1, 7, 10, 1))
        assert any("já passou" in e for e in erros)

    def test_nao_agenda_no_domingo(self, db, base):
        erros = Agendamento().definir(form_agendamento(base, data=DOMINGO), referencia=REFERENCIA)
        assert any("domingo" in e for e in erros)

    @pytest.mark.parametrize("hora", ["07:59", "19:30", "20:00"])
    def test_fora_do_horario_de_funcionamento(self, db, base, hora):
        erros = Agendamento().definir(form_agendamento(base, hora=hora), referencia=REFERENCIA)
        assert any("horário de funcionamento" in e for e in erros)

    def test_ultimo_horario_possivel(self, db, base):
        # serviço de 60 min às 19:00 termina exatamente às 20:00
        assert Agendamento().definir(form_agendamento(base, hora="19:00"), referencia=REFERENCIA) == []

    def test_conflito_mesmo_profissional(self, db, base):
        criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        erros = Agendamento().definir(form_agendamento(base, hora="10:30", cliente="outro_cliente"),
                                      referencia=REFERENCIA)
        assert any("Ana Souza já tem atendimento das 10:00 às 11:00" in e for e in erros)

    def test_outro_profissional_no_mesmo_horario_pode(self, db, base):
        criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        erros = Agendamento().definir(form_agendamento(base, hora="10:30", cliente="outro_cliente",
                                                       profissional="bruno"), referencia=REFERENCIA)
        assert erros == []

    def test_conflito_mesmo_cliente_com_outro_profissional(self, db, base):
        criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        erros = Agendamento().definir(form_agendamento(base, hora="10:30", profissional="bruno"),
                                      referencia=REFERENCIA)
        assert any("cliente já tem outro agendamento" in e for e in erros)

    def test_horarios_encostados_nao_conflitam(self, db, base):
        criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        erros = Agendamento().definir(form_agendamento(base, hora="11:00", cliente="outro_cliente"),
                                      referencia=REFERENCIA)
        assert erros == []

    def test_cancelado_libera_o_horario(self, db, base):
        criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0), status="cancelado")
        erros = Agendamento().definir(form_agendamento(base, cliente="outro_cliente"), referencia=REFERENCIA)
        assert erros == []

    def test_remarcar_nao_conflita_consigo_mesmo(self, db, base):
        a = criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        assert a.definir(form_agendamento(base, hora="10:30"), referencia=REFERENCIA) == []

    def test_servico_desativado_nao_pode_ser_escolhido(self, db, base):
        base["servico"].ativo = False
        db.session.commit()
        erros = Agendamento().definir(form_agendamento(base), referencia=REFERENCIA)
        assert any("desativado" in e for e in erros)

    def test_preco_historico_nao_muda_com_reajuste(self, db, base):
        a = criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        base["servico"].preco = Decimal("120.00")
        db.session.commit()
        assert a.definir(form_agendamento(base, hora="11:00"), referencia=REFERENCIA) == []
        assert a.preco == Decimal("80.00")


class TestStatusAgendamento:
    def test_cancelar_e_reabrir(self, db, base):
        a = criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        assert a.alterar_status("cancelado", referencia=REFERENCIA) is None
        assert a.status == "cancelado"
        assert a.alterar_status("agendado", referencia=REFERENCIA) is None
        assert a.status == "agendado"

    def test_nao_conclui_antes_do_inicio(self, db, base):
        a = criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        assert "depois do horário de início" in a.alterar_status("concluido", referencia=REFERENCIA)
        assert a.alterar_status("concluido", referencia=datetime(2030, 1, 7, 10, 5)) is None

    def test_concluido_e_definitivo(self, db, base):
        a = criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0), status="concluido")
        assert a.alterar_status("cancelado", referencia=REFERENCIA) is not None
        assert a.status == "concluido"

    def test_nao_reabre_se_horario_foi_ocupado(self, db, base):
        a = criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0), status="cancelado")
        criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0), cliente="outro_cliente")
        erro = a.alterar_status("agendado", referencia=REFERENCIA)
        assert erro.startswith("Não é possível reabrir")
        assert a.status == "cancelado"

    def test_status_invalido(self, db, base):
        a = criar_agendamento(db, base, datetime(2030, 1, 7, 10, 0))
        assert a.alterar_status("xyz", referencia=REFERENCIA) == "Status inválido."


# ------------------------------------------------------------------ Feedback
class TestFeedback:
    def dados(self, **extra):
        d = {"nome_testador": "Carlos", "data_teste": "2020-05-10", "funcionou": "Cadastro de clientes"}
        d.update(extra)
        return d

    def test_valido(self, db):
        assert Feedback().preencher(self.dados()) == []

    def test_exige_alguma_descricao(self, db):
        erros = Feedback().preencher(self.dados(funcionou=""))
        assert any("pelo menos" in e for e in erros)

    def test_email_longo_demais(self, db):
        # No PostgreSQL, VARCHAR(120) estouraria com erro 500 (defeito D3 do laudo)
        erros = Feedback().preencher(self.dados(email_testador="a" * 120 + "@exemplo.com"))
        assert "E-mail inválido." in erros

    def test_data_no_futuro(self, db):
        erros = Feedback().preencher(self.dados(data_teste="2999-01-01"))
        assert any("futuro" in e for e in erros)

    def test_aceita_png(self, db):
        f = Feedback()
        arquivo = FileStorage(BytesIO(PNG_MINIMO), filename="erro.png")
        assert f.preencher(self.dados(), arquivo) == []
        assert f.screenshot_mime == "image/png"

    def test_recusa_arquivo_que_nao_e_imagem(self, db):
        arquivo = FileStorage(BytesIO(b"MZ executavel"), filename="erro.png")
        erros = Feedback().preencher(self.dados(), arquivo)
        assert any("não é uma imagem" in e for e in erros)

    def test_recusa_imagem_grande(self, db):
        arquivo = FileStorage(BytesIO(PNG_MINIMO + b"0" * (2 * 1024 * 1024)), filename="grande.png")
        erros = Feedback().preencher(self.dados(), arquivo)
        assert any("2 MB" in e for e in erros)

    @pytest.mark.parametrize("conteudo,mime", [
        (b"\xff\xd8\xff\xe0", "image/jpeg"),
        (b"GIF89a....", "image/gif"),
        (b"RIFF\x00\x00\x00\x00WEBPVP8 ", "image/webp"),
        (b"%PDF-1.7", None),
    ])
    def test_detectar_imagem(self, conteudo, mime):
        assert detectar_imagem(conteudo) == mime
