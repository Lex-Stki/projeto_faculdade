# 2. Requisitos

Cada requisito tem um identificador, aponta para o código que o implementa e para os testes automatizados que o verificam. O material da disciplina pede "vincular facilmente a esses requisitos os códigos e testes".

Arquivos de teste: `tests/test_models.py` (unidade), `tests/test_controllers.py` (integração), `tests/e2e/test_fluxos.py` (sistema, com navegador real).

## 2.1 Requisitos funcionais (RF)

| ID | Requisito | Implementação | Testes |
|---|---|---|---|
| RF01 | Criar conta, entrar e sair do sistema | `controllers/auth.py` | `TestAutenticacao`, `test_fluxo_completo` |
| RF02 | Cadastrar, editar, buscar e excluir clientes; ver histórico | `controllers/clientes.py`, `models/cliente.py` | `TestClientes`, `TestCliente` |
| RF03 | Cadastrar, editar, desativar, reativar e excluir serviços | `controllers/servicos.py`, `models/servico.py` | `TestServicosEProfissionais`, `TestServico` |
| RF04 | Cadastrar, editar, inativar, reativar e excluir profissionais | `controllers/profissionais.py` | `test_crud_profissional` |
| RF05 | Criar agendamento (cliente + serviço + profissional + data e hora) | `controllers/agendamentos.py`, `models/agendamento.py` | `TestAgendamento`, `test_criar_e_listar_no_dia` |
| RF06 | Consultar a agenda filtrando por dia, profissional, status e período | `agendamentos.lista` | `test_filtros_da_agenda`, `test_passados_so_aparecem_com_periodo_todos` |
| RF07 | Remarcar, concluir, cancelar e reabrir agendamento | `agendamentos.editar`, `agendamentos.alterar_status` | `TestStatusAgendamento`, `test_remarcar`, `test_cancelar_reabrir_e_concluir` |
| RF08 | Oferecer os horários do dia de 10 em 10 min, bloqueando os indisponíveis com o motivo antes de salvar, e mostrar a ocupação do profissional | `Agendamento.horarios_do_dia`, `agendamentos.disponibilidade`, `static/js/agendamento.js` | `TestHorariosDoDia`, `test_disponibilidade_json`, `test_disponibilidade_devolve_horarios_com_motivo`, E2E passos 4 e 5 |
| RF09 | Painel do dia: atendimentos, pendentes, receita prevista, clientes | `controllers/dashboard.py` | `test_dashboard_mostra_agenda_de_hoje` |
| RF10 | Formulário público de laudo de teste, com captura de tela | `controllers/feedback.py`, `models/feedback.py` | `TestFeedback` (dois arquivos) |
| RF11 | Listar, ver captura, exportar CSV e excluir laudos (admin) | `feedback.lista`, `feedback.exportar` | `test_admin_lista_ve_print_e_exporta_csv` |
| RF12 | Carregar dados de exemplo para testes rápidos | `seed.py`, `dashboard.dados_exemplo` | `test_dados_de_exemplo` |
| RF13 | Indicadores de vendas: faturamento, atendimentos e ticket médio do mês; gráfico de faturamento dos últimos 7 dias; serviços mais vendidos (somente concluídos). Pedido da testadora Vitória | `models/vendas.py`, `views/dashboard.html` | `TestResumoVendas`, `test_painel_mostra_vendas_concluidas`, `test_painel_de_vendas` (E2E) |

## 2.2 Regras de negócio (RN)

| ID | Regra | Onde está | Testes |
|---|---|---|---|
| RN01 | Não é possível agendar em data ou horário que já passou | `Agendamento._validar_horario` | `test_nao_agenda_no_passado` |
| RN02 | Funcionamento de segunda a sábado, 08:00–20:00; o atendimento precisa **terminar** até 20:00 | `Agendamento._validar_horario`, `config.py` | `test_nao_agenda_no_domingo`, `test_fora_do_horario_de_funcionamento`, `test_ultimo_horario_possivel` |
| RN03 | Um profissional não pode ter dois atendimentos sobrepostos | `Agendamento._validar_conflitos` | `test_conflito_mesmo_profissional`, `test_outro_profissional_no_mesmo_horario_pode` |
| RN04 | Um cliente não pode ter dois atendimentos sobrepostos | `Agendamento._validar_conflitos` | `test_conflito_mesmo_cliente_com_outro_profissional` |
| RN05 | Horários encostados (10:00–11:00 e 11:00–12:00) não conflitam; agendamento cancelado libera o horário | `Agendamento.conflitos` | `test_horarios_encostados_nao_conflitam`, `test_cancelado_libera_o_horario` |
| RN06 | Término = início + duração do serviço | `Agendamento.definir` | `test_calcula_fim_e_copia_preco` |
| RN07 | O preço é copiado para o agendamento; reajustes no serviço não alteram o histórico | `Agendamento.definir` | `test_preco_historico_nao_muda_com_reajuste` |
| RN08 | Transições de status: agendado → concluído / cancelado; cancelado → agendado (reabrir); concluído é definitivo | `TRANSICOES` em `models/agendamento.py` | `TestStatusAgendamento` |
| RN09 | Só é possível concluir depois do horário de início; só é possível reabrir se o horário ainda não passou e continua livre | `Agendamento.alterar_status` | `test_nao_conclui_antes_do_inicio`, `test_nao_reabre_se_horario_foi_ocupado` |
| RN10 | Cliente, serviço ou profissional com histórico não pode ser excluído; serviço e profissional podem ser desativados | `excluir` nos controllers + `ON DELETE RESTRICT` | `test_nao_exclui_cliente_com_historico`, `test_nao_exclui_servico_usado` |
| RN11 | Serviço ou profissional inativo não aparece para novos agendamentos | `_opcoes`, `Agendamento.definir` | `test_servico_desativado_nao_pode_ser_escolhido`, `test_desativar_e_reativar_servico` |
| RN12 | A primeira conta é administradora; somente o administrador vê os laudos | `auth.cadastro`, `admin_obrigatorio` | `test_primeiro_cadastro_vira_admin_e_os_demais_atendentes`, `test_somente_admin_ve_laudos` |
| RN13 | O cadastro de novas contas pode ser fechado (`CADASTRO_ABERTO=0`) depois do período de testes | `auth.cadastro` | `test_cadastro_fechado_bloqueia_novas_contas` |
| RN15 | A data padrão de um novo agendamento é o primeiro dia com horário livre (D8) | `agendamentos._primeira_data_com_horario` | `test_novo_agendamento_abre_no_proximo_dia_com_horario` |
| RN14 | Telefone com DDD (10 ou 11 dígitos); nome de serviço único (sem diferenciar maiúsculas); duração de 5 a 480 min; preço ≥ 0 | `preencher()` dos models + `CHECK` no banco | `TestCliente`, `TestServico` |

## 2.3 Requisitos não funcionais (RNF)

| ID | Categoria | Requisito | Como foi atendido |
|---|---|---|---|
| RNF01 | Usabilidade | Interface em português, com mensagens claras que dizem o que fazer | Catálogo de mensagens em [04-ihc.md](04-ihc.md) |
| RNF02 | Usabilidade | Ações destrutivas pedem confirmação; cancelamento é reversível | Diálogo de confirmação + "Reabrir" |
| RNF03 | Portabilidade | Funcionar em celular (≥ 360 px) e computador | CSS responsivo; tabelas viram cartões; evidência `08-agenda-no-celular.png` |
| RNF04 | Acessibilidade | Rótulos em todos os campos, foco visível, link "pular para o conteúdo", mensagens anunciadas por leitor de tela | `label`/`aria-describedby`/`aria-live`/`aria-invalid` |
| RNF05 | Segurança | Senhas guardadas como *hash*; proteção contra CSRF; cookie `HttpOnly`/`SameSite`/`Secure`; sem *open redirect*; cabeçalhos `X-Frame-Options` e `nosniff`; upload validado pela assinatura do arquivo | `utils.py`, `__init__.py`, `models/feedback.py`; testes em `TestAutenticacao` e `test_utils.py` |
| RNF06 | Integridade | Regras validadas no servidor **e** garantidas no banco (`NOT NULL`, `UNIQUE`, `CHECK`, `FOREIGN KEY`) | [05-banco-de-dados.md](05-banco-de-dados.md) |
| RNF07 | Desempenho | Consultas de agenda usam índice (`profissional_id, inicio`); listas paginadas (10 por página) | `schema.sql` |
| RNF08 | Manutenibilidade | Arquitetura MVC; cobertura de testes automatizados ≥ 90% | 149 testes, 94% de cobertura |
| RNF09 | Disponibilidade | Hospedado no Render com banco gerenciado (Neon); rota `/saude` para checar aplicação e banco | `dashboard.saude` |
| RNF10 | Robustez | Nenhum erro técnico aparece para o usuário; páginas amigáveis para 400, 403, 404, 413 e 500 | `_registrar_erros` em `__init__.py` |
