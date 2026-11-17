# 1. Plano de testes: verificação e validação

## 1.1 Verificação × validação

| | Verificação | Validação |
|---|---|---|
| Pergunta | "Estamos construindo o produto **corretamente**?" | "Estamos construindo o produto **certo**?" |
| Quando | Durante o desenvolvimento | Ao final de um módulo ou do sistema |
| Atividades neste projeto | Revisão de código; comparação do código com as regras RN01–RN14; testes automatizados de unidade e integração; análise de diferenças SQLite × PostgreSQL | Teste de sistema em navegador real (E2E); **teste de aceitação com 5 colegas**, que usam o sistema como um dono de salão usaria |
| Evidência | [Testes automatizados](../situacao-2/04-testes-automatizados.md), defeitos D1–D5 do [laudo](03-laudo-de-qualidade.md) | Capturas em `evidencias/`; laudos enviados pelo formulário |

## 1.2 Teste de aceitação com colegas

**Participantes:** 5 colegas de curso ou profissionais da área, os "dublês de usuário".

**Instrumento:** o formulário de laudo dentro do próprio sistema (`/feedback`). Ele tem todos os campos mínimos pedidos pela disciplina (nome, data, o que funcionou, o que não funcionou, o que não foi testado), além de sugestões, nota de facilidade de uso e envio de **captura da tela com erro**. Os laudos ficam no banco e podem ser exportados em CSV. O modelo em papel ou PDF está em [02-template-laudo-de-teste.md](02-template-laudo-de-teste.md).

**Mensagem sugerida para enviar aos colegas:**

> Oi! Estou terminando meu Projeto Integrador e preciso que você teste meu sistema por uns 15 minutos.
> É um sistema de agendamento para salão/barbearia.
> 1) Acesse **https://SEU-PROJETO.vercel.app**, crie uma conta e use como se fosse dono(a) de um salão (o roteiro abaixo ajuda).
> 2) No final, preencha o laudo em **https://SEU-PROJETO.vercel.app/feedback**. Pode mandar print dos erros!
> Pode ser bem sincero(a): os erros que você achar vão me ajudar a melhorar a nota. Obrigado!

## 1.3 Roteiro de casos de teste (para os testadores)

O roteiro também aparece recolhido no formulário de laudo ("Sugestão de roteiro de teste").

| ID | Caso de teste | Passos | Resultado esperado | Requisitos |
|---|---|---|---|---|
| CT01 | Criar conta e entrar | Criar conta; sair; entrar de novo | Painel aparece com a mensagem de boas-vindas | RF01 |
| CT02 | Senha errada | Entrar com senha errada | "E-mail ou senha incorretos." | RF01 |
| CT03 | Dados de exemplo | Painel → Carregar dados de exemplo (só a 1ª conta, admin) | Serviços, profissionais e clientes criados | RF12 |
| CT04 | Cadastrar cliente | Clientes → Novo; deixar o telefone vazio e salvar; depois preencher | Erro "Campo obrigatório." ao lado do campo; depois "Cliente … cadastrado." | RF02, RN14 |
| CT05 | Buscar cliente | Buscar por parte do nome e por parte do telefone | Lista filtrada | RF02 |
| CT06 | Agendar | Novo agendamento para amanhã (seg–sáb) às 10:00 | Término previsto exibido; agendamento criado | RF05, RN06 |
| CT07 | Conflito | Agendar outro cliente com o **mesmo profissional** às 10:30 | Mensagem de conflito com o horário ocupado | RN03 |
| CT08 | Regras de horário | Tentar domingo; tentar 19:30 com serviço de 60 min; tentar ontem | Mensagens explicando cada regra | RN01, RN02 |
| CT09 | Remarcar | Agenda → Remarcar para 14:00 | Agendamento atualizado | RF07 |
| CT10 | Cancelar e reabrir | Cancelar (confirmar no diálogo) e depois Reabrir | Status muda para Cancelado e volta para Agendado | RF07, RN08 |
| CT11 | Concluir | Concluir um agendamento futuro | Mensagem: só depois do horário de início | RN09 |
| CT12 | Serviço | Desativar um serviço; ver que ele some do formulário de agendamento; tentar excluir um serviço já usado | Some da lista; exclusão negada com sugestão de desativar | RN10, RN11 |
| CT13 | Filtros da agenda | Filtrar por dia, por profissional e por status | Apenas os registros correspondentes | RF06 |
| CT14 | Celular | Repetir CT06 no celular | Telas legíveis, menu recolhível, tabelas em cartões | RNF03 |
| CT15 | Enviar laudo | Preencher o laudo com uma captura de tela | Página "Laudo enviado!" | RF10 |

## 1.4 Critérios de aceitação

- Nenhum defeito de severidade **alta** (perda de dados, erro 500, regra de negócio violada) em aberto.
- Todos os defeitos de severidade **média** corrigidos ou justificados no laudo de qualidade.
- Média da nota de facilidade de uso ≥ 4 entre os testadores.
- Suíte automatizada 100% aprovada após as correções.

## 1.5 Ciclo de correção

1. Ler os laudos (menu **Laudos**) e exportar em CSV.
2. Classificar cada item: defeito (alta, média ou baixa), sugestão (aceita ou recusada, com motivo) ou fora do escopo.
3. Para cada defeito: reproduzir → **escrever um teste automatizado que falha** → corrigir → ver o teste passar → registrar no laudo de qualidade (seção 3.4).
4. `git push` → o Vercel publica → pedir ao testador que confira, quando possível.
5. Gravar o vídeo da solução atualizada mostrando as mudanças.
