# 3. Laudo de qualidade

| Item | Valor |
|---|---|
| Sistema | AgendaFácil: agendamento para negócios de serviços |
| Versão avaliada | 2.3 (branch `main`), após as correções dos testes de aceitação |
| Ambiente de verificação | Windows 11, Python 3.13, SQLite em memória (testes), Microsoft Edge (E2E) |
| Ambiente de produção | Render (Python 3.12, gunicorn) + PostgreSQL (Neon) |
| Data da verificação interna | 17/11/2026 |
| Testes de aceitação (colegas) | 17/11/2026, 5 testadores |

## 3.1 Resumo

| Indicador | Resultado |
|---|---|
| Testes automatizados | **149 aprovados / 0 falhas** (98 unidade, 48 integração, 3 cenários E2E) |
| Cobertura de código | **94 %** |
| Defeitos encontrados (verificação interna, deploy e colegas) | 8 (2 altas, 3 médias, 3 baixas) |
| Defeitos corrigidos | 8 de 8, cada um com teste de regressão |
| Erros de JavaScript no navegador durante o E2E | 0 |
| Validação em produção | **OK**: `https://agendafacil-scyw.onrender.com/saude` responde `banco: ok`; agendamento criado e listado no PostgreSQL (Neon), evidência `11-producao-agendamento-criado.png` |
| Resultado dos testes de aceitação | **Concluídos**: 5 testadores, nota média de facilidade **4,6 / 5**; 1 defeito e 4 sugestões, das quais 3 implementadas (seção 3.4) |

## 3.2 Defeitos encontrados na verificação interna e correções

### D1: Clique em link ou botão "não funciona" logo depois de sair de um campo (média)

| | |
|---|---|
| **Como foi encontrado** | Teste E2E `test_fluxo_completo`, passo 1: o clique em "Crie uma agora" na tela de login não abria o cadastro (Timeout esperando o campo `#nome`). |
| **Evidência** | Captura do momento da falha (abaixo, à esquerda): a mensagem "Campo obrigatório." apareceu sob o e-mail sem que o usuário tivesse enviado nada, e a página continuou no login. |
| **Causa** | O campo e-mail tem foco automático. O JavaScript validava cada campo ao **perder o foco** (*blur*). Ao clicar no link, o *blur* inseria a mensagem de erro, a página descia cerca de 20 px e o fim do clique caía fora do link. O mesmo acontecia ao contrário: corrigir um campo e clicar em "Salvar" removia a mensagem, a página subia e o clique errava o botão. |
| **Correção** | Nova estratégia de validação (`static/js/app.js`): os erros aparecem **no envio** e somem **enquanto a pessoa digita** no campo com erro. Nada muda de lugar no momento do clique. |
| **Teste de regressão** | `test_fluxo_completo` (passos 1 e 3) |
| **Status** | Corrigido |

| Antes da correção | Depois da correção |
|---|---|
| ![Antes: erro inserido ao clicar no link](evidencias/D1-antes-da-correcao.png) | ![Depois: erros aparecem só ao enviar](evidencias/03-validacao-formulario.png) |

### D2: Mensagens de sucesso sumiam sozinhas e deslocavam a página (baixa)

| | |
|---|---|
| **Como foi encontrado** | Análise da causa do D1: o alerta de sucesso era removido após 6 s, o que também desloca todo o conteúdo para cima, possivelmente durante um clique. |
| **Correção** | As mensagens só são fechadas pelo usuário (botão ×), seguindo o princípio "controlada pelo usuário". |
| **Status** | Corrigido |

### D3: E-mail longo no laudo de teste causaria erro 500 só em produção (média)

| | |
|---|---|
| **Como foi encontrado** | Revisão das diferenças entre SQLite (testes) e PostgreSQL (produção). O PostgreSQL rejeita textos maiores que o `VARCHAR`; o SQLite aceita. Todos os campos tinham verificação de tamanho, exceto `feedback.email_testador` (120). |
| **Impacto** | Um testador com e-mail de mais de 120 caracteres veria "Erro interno" em produção, e o problema não apareceria nos testes locais. |
| **Correção** | Validação de tamanho em `Feedback.preencher()`. |
| **Teste de regressão** | `TestFeedback::test_email_longo_demais` |
| **Status** | Corrigido |

### D4: Renomear um serviço para um nome já existente gerava erro 500 (alta)

| | |
|---|---|
| **Como foi encontrado** | Revisão de código (verificação) do fluxo de edição, antes da primeira execução. |
| **Causa** | O SQLAlchemy grava automaticamente as alterações pendentes antes de cada consulta (*autoflush*). Ao validar "nome já existe?", a alteração inválida era enviada ao banco, a restrição `UNIQUE` disparava e o resultado era um erro 500 em vez da mensagem amigável. No caso da remarcação, uma alteração ainda não validada podia ser enviada ao banco durante a checagem de conflitos. |
| **Correção** | Consultas de validação dentro de `db.session.no_autoflush`; `rollback()` explícito quando há erro; formulários renderizados a partir dos dados digitados, não do objeto do banco. |
| **Testes de regressão** | `test_renomear_para_nome_existente_nao_quebra`, `test_edicao_invalida_nao_altera_o_banco`, `test_remarcacao_invalida_nao_altera_o_banco` |
| **Status** | Corrigido |

### D5: Endereço de retorno após o login terminava com "?" (baixa)

| | |
|---|---|
| **Como foi encontrado** | Teste exploratório (*smoke test*): acessar `/` sem login redirecionava para `/login?proximo=/?`. |
| **Correção** | Remoção do `?` final em `login_obrigatorio`. |
| **Status** | Corrigido |

### D6: Deploy no Render falhava com `ModuleNotFoundError: No module named 'psycopg'` (alta)

| | |
|---|---|
| **Como foi encontrado** | Primeiro deploy no Render (validação em ambiente real). A aplicação não iniciava. |
| **Causa** | A partir do **SQLAlchemy 2.1** (versão usada no projeto), um endereço `postgresql://` sem driver explícito passa a usar o *psycopg 3*, mas o projeto instala o *psycopg2*. Os testes não pegaram o problema porque rodam em SQLite e só comparavam o texto da URL, sem verificar qual driver seria carregado. |
| **Primeira tentativa (incorreta)** | A primeira hipótese foi que o painel do Neon gerava a URL no formato `postgresql+psycopg://`. A normalização feita para isso não resolveu: o segundo deploy falhou com o mesmo erro, o que mostrou que a causa era outra. Fica registrado como aprendizado: a correção precisa ser validada no ambiente onde o erro aconteceu. |
| **Correção** | `config.normalizar_url_postgres()` converte qualquer variação (`postgres://`, `postgresql://`, `postgresql+psycopg://`, `postgresql+asyncpg://`, com aspas ou espaços colados) para **`postgresql+psycopg2://`**, deixando o driver explícito. |
| **Testes de regressão** | `test_url_postgres_e_normalizada` (6 variações), `test_driver_postgres_carregado_esta_instalado` (verifica que o driver escolhido pelo SQLAlchemy é o psycopg2 e que ele importa), `test_url_de_outro_banco_nao_e_alterada` |
| **Status** | Corrigido |

Na primeira execução da suíte houve também uma falha em `test_desativar_e_reativar_servico` que **era erro do próprio teste**: ele procurava a palavra "Corte" na página, mas ela aparecia na mensagem "Serviço “Corte” desativado". O teste foi ajustado para procurar o texto da opção do formulário. Não houve mudança no sistema.

### D7: Seletor de hora aceitava minutos que depois eram recusados (média), relatado pelo testador Robson

| | |
|---|---|
| **Como foi encontrado** | Teste de aceitação. Laudo do Robson: *"Não é possível agendar em horários que não sejam hora + 10, 20, 30, 40 e 50 min, exemplo, não pode agendar às 15:34, apenas 15:30"*; *"Interface de escolha de hora confusa e difícil de usar"*. |
| **Causa** | O campo era um `<input type="time" step="300">` (intervalos de 5 min). O seletor do navegador oferece todos os minutos de 00 a 59; ao escolher 15:34, a validação do navegador recusava com a mensagem genérica "Valor inválido.". A interface permitia o erro e depois punia o usuário sem explicar o motivo. |
| **Correção** | O horário virou uma **lista de horários de 10 em 10 minutos** (sugestão do próprio testador), calculada pelo novo `Agendamento.horarios_do_dia()` com as mesmas regras do salvamento. Horários passados ou em conflito aparecem **bloqueados, com o motivo** (ex.: "indisponível: Ana Souza ocupado(a) 10:00–11:00"). A lista é atualizada ao mudar data, serviço, profissional ou cliente. A mensagem genérica também foi trocada por textos específicos ("Valor fora dos intervalos aceitos…"). |
| **Testes de regressão** | `TestHorariosDoDia` (8 testes, entre eles `test_mesma_regra_que_o_salvamento`, que garante que todo horário oferecido como livre é aceito ao salvar e vice-versa), `test_disponibilidade_devolve_horarios_com_motivo`, `test_formulario_ja_vem_com_horarios_bloqueados_sem_javascript`, `test_remarcar_mantem_horario_fora_da_grade`, E2E passos 4 e 5 |
| **Status** | Corrigido |

![Lista de horários com indisponibilidade antes de salvar](evidencias/06-indisponibilidade-antes-de-salvar.png)

### D8: Depois do expediente, "Novo agendamento" abria no dia de hoje sem nenhum horário (baixa)

| | |
|---|---|
| **Como foi encontrado** | Reteste após a correção do D7 (verificação). A captura do formulário no celular, feita às 20h50, mostrou "Nenhum horário livre neste dia" e a orientação errada "Escolha o profissional…". |
| **Correção** | A data padrão passa a ser o próximo dia que ainda tem horário livre (pulando o domingo). Quando não há horários na data escolhida, o painel diz "Não há mais horários disponíveis nesta data. Escolha outra data.". |
| **Teste de regressão** | `test_novo_agendamento_abre_no_proximo_dia_com_horario` (manhã de segunda, segunda à noite, sábado à noite) |
| **Status** | Corrigido |

## 3.3 Limitações conhecidas (riscos aceitos nesta versão)

| # | Limitação | Risco | Tratamento |
|---|---|---|---|
| L1 | Duas pessoas salvando agendamentos conflitantes **no mesmo segundo** poderiam passar ambas pela verificação | Baixo para um pequeno negócio (1–2 atendentes) | Evolução: restrição de exclusão no PostgreSQL (`EXCLUDE USING gist`) |
| L2 | O formato dos campos de data e hora (ex.: 01/07/2030 × 07/01/2030, AM/PM) segue o idioma do **navegador**, não do site | Confusão em navegadores configurados em inglês | Documentado; os textos do sistema usam sempre dd/mm/aaaa. Em navegador em português aparece dd/mm/aaaa (confirmado na evidência 11) |
| L3 | Não há recuperação de senha por e-mail | Usuário bloqueado se esquecer a senha | Fora do escopo (próxima versão) |
| L4 | Cadastro aberto: qualquer pessoa com o link pode criar conta e ver os dados | Exposição de dados de clientes | Necessário durante os testes; depois, `CADASTRO_ABERTO=0` |
| L5 | A suíte automatizada roda em SQLite; em PostgreSQL a aplicação foi validada em produção (deploy no Neon, `/saude` e fluxo de agendamento), mas a suíte completa ainda não rodou contra PostgreSQL | Diferença de comportamento entre bancos em casos não exercitados manualmente | Rodar `TEST_DATABASE_URL=<branch de teste do Neon> pytest` |

## 3.4 Resultados dos testes de aceitação (colegas)

Os 5 laudos foram enviados pelo formulário do sistema (`/feedback`) em 17/11/2026 e exportados em CSV. Nenhum testador anexou captura de tela. Os nomes estão abreviados neste repositório público; o documento de entrega traz os nomes completos.

| # | Testador | Data | O que testou e funcionou | Problemas relatados | Não testado | Nota |
|---|---|---|---|---|---|---|
| 1 | Rafael F. | 17/11/2026 | Criação de agendamentos; conflito de horário entre profissionais e clientes bloqueado corretamente | Nenhum | Cadastro de profissionais, clientes e serviços | 5 |
| 2 | Fernando C. | 17/11/2026 | Agenda, clientes e serviços | Nenhum | — | 5 |
| 3 | Robson I. | 17/11/2026 | Escolha de profissional e de serviço | Só aceita minutos "redondos" (não aceita 15:34); escolha de hora confusa; interface ruim no celular | Envio de pré-agendamento por WhatsApp (não existe no sistema) | 3 |
| 4 | Bruno V. | 17/11/2026 | Cadastro de cliente, agendamento, serviços e profissionais | Nenhum | — | 5 |
| 5 | Vitória S. | 17/11/2026 | Todas as funcionalidades disponíveis | Nenhum | Indicadores de vendas com gráficos (não existiam) | 5 |

**Nota média de facilidade de uso: 4,6 / 5** (critério de aceitação: ≥ 4, atendido). A única nota abaixo de 4 veio do relato que originou o D7.

### Itens relatados, classificação e ação tomada

| Item | Quem | Classificação | Ação | Status |
|---|---|---|---|---|
| Minutos fora de 10/20/30… recusados; escolha de hora confusa | Robson | Defeito, média (D7) | Lista de horários de 10 em 10 min com indisponibilidade e motivo | Corrigido |
| Interface ruim no celular | Robson | Usabilidade | Lista de horários nativa (fácil de usar no toque); botões principais com largura total e altura mínima de 44 px; filtros um por linha; margens menores | Melhorado (evidências 14 e 15) |
| Mostrar a validação ao escolher a data, sem precisar salvar | Bruno | Sugestão | Aceita: horários indisponíveis bloqueados com o motivo e aviso imediato quando o horário escolhido deixa de valer | Implementada |
| Mostrar "indisponível e o motivo" antes de clicar em agendar | Vitória | Sugestão | Aceita: mesma implementação acima | Implementada |
| Indicadores de vendas no dia, com gráficos | Vitória | Sugestão (nova funcionalidade) | Aceita: seção **Vendas** no painel com faturamento, atendimentos e ticket médio do mês, gráfico de faturamento dos últimos 7 dias e ranking dos serviços mais vendidos, com dicas no mouse ou teclado, tabela com os dados e modo escuro | Implementada (RF13) |
| Lembrete por WhatsApp 1 h antes do atendimento | Robson | Sugestão | **Não implementada nesta versão.** Exige a API oficial do WhatsApp Business (conta empresarial verificada, aprovação de modelos de mensagem e custo por conversa) e um agendador de tarefas fora do plano gratuito de hospedagem. Já estava listada como "fora do escopo" e fica registrada para a próxima versão. | Fora do escopo |
| Não testou cadastros de profissionais, clientes e serviços | Rafael | Cobertura do teste | Essas funções foram cobertas pelos laudos do Fernando e do Bruno e pelos testes automatizados (`TestClientes`, `TestServicosEProfissionais`) | Sem ação |

## 3.5 Evidências

Todas as capturas em [`evidencias/`](evidencias/) foram geradas automaticamente pelo teste E2E (`E2E_EVIDENCIAS=1 pytest tests/e2e`), sempre a partir da versão atual do código.

| Arquivo | O que comprova |
|---|---|
| `01-login.png` | Tela de entrada |
| `02-primeiros-passos.png` | Primeira conta = admin; orientação inicial |
| `03-validacao-formulario.png` | Validação no navegador após a correção do D1 |
| `04-formulario-agendamento.png` | Término previsto e disponibilidade em tempo real (RN06, RF08) |
| `05-agenda-do-dia.png` | Agendamento criado e mensagem de sucesso |
| `06-indisponibilidade-antes-de-salvar.png` | Horários em conflito bloqueados com o motivo e aviso imediato, antes de salvar (D7; sugestões de Bruno e Vitória) |
| `07-dialogo-confirmacao.png` | Confirmação antes de cancelar (RNF02) |
| `08-agenda-no-celular.png` | Layout responsivo (RNF03) |
| `09-laudos-recebidos.png` | Laudo de teste recebido (RF10/RF11) |
| `10-erro-404.png` | Página de erro amigável (RNF10) |
| `D1-antes-da-correcao.png` | Defeito D1 no momento em que foi detectado |
| `11-producao-agendamento-criado.png` | Sistema em produção (Render + Neon): agendamento criado e listado, data em formato brasileiro, modo escuro |
| `12-painel-vendas.png` | Indicadores e gráficos de vendas (sugestão da Vitória) |
| `13-painel-vendas-escuro.png` | O mesmo painel no modo escuro (cores validadas para a superfície escura) |
| `14-painel-vendas-celular.png` | Painel de vendas no celular |
| `15-agendamento-no-celular.png` | Formulário de agendamento no celular após as melhorias (relato do Robson) e a correção do D8 |
