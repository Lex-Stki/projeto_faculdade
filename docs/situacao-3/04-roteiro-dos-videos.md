# 4. Roteiro dos vídeos

São dois vídeos:

| Vídeo | Situação | Duração | Conteúdo |
|---|---|---|---|
| **Vídeo 1: Solução em funcionamento** | 2 | **no mínimo 5 min**, narrado | Apresentação completa do sistema e do código |
| **Vídeo 2: Solução atualizada** | 3 | **até 5 min** | O que os colegas encontraram e o que foi corrigido |

Dica: grave a tela com o **Xbox Game Bar** (Win + G) ou o **OBS Studio**, publique no YouTube como **"Não listado"** e cole o link no documento de entrega e no README.

## Vídeo 1: Solução em funcionamento (≥ 5 min)

| Tempo | Mostrar na tela | O que falar |
|---|---|---|
| 0:00–0:40 | README no GitHub | Apresentação: nome, RGM, o problema (agenda em caderno ou WhatsApp, horários duplicados) e a solução AgendaFácil. |
| 0:40–1:30 | `docs/` no GitHub (requisitos, diagrama de classes, banco) | Revisão da Situação 1: regras de negócio numeradas, UML, modelo do banco e dicionário de dados. |
| 1:30–2:30 | VS Code: pastas `models/`, `controllers/`, `views/` | Arquitetura MVC: o Model guarda as regras (abrir `Agendamento.definir`), o Controller recebe a requisição, a View mostra o HTML. Python + Flask, PostgreSQL no Neon, hospedado no Render. |
| 2:30–3:00 | Site no ar: criar conta | Primeira conta vira administradora; carregar dados de exemplo. |
| 3:00–3:30 | Clientes | Cadastro com máscara de telefone, validação de campo obrigatório, busca, "Salvar e agendar". |
| 3:30–4:30 | Novo agendamento | Lista de horários de 10 em 10 min; horários **ocupados bloqueados com o motivo**; término previsto; escolher **domingo** (fechado) e notar que um serviço de 60 min não oferece 19:30. Salvar um válido. |
| 4:30–5:15 | Agenda | Filtros; Remarcar; Cancelar (diálogo) e Reabrir; tentar concluir um atendimento futuro. |
| 5:15–5:45 | Serviços | Desativar um serviço e mostrar que ele some do agendamento; tentar excluir um serviço já usado. |
| 5:45–6:15 | Celular (F12 → modo dispositivo) | Layout responsivo. |
| 6:15–6:50 | Terminal: `pytest --cov=agendafacil` | 149 testes passando e 94% de cobertura; mostrar um teste de regra de negócio e o teste E2E. |
| 6:50–7:10 | Painel **Vendas** | Faturamento, ticket médio, gráfico dos últimos 7 dias e serviços mais vendidos. |
| 7:10–7:30 | Formulário `/feedback` | Como os colegas vão testar e enviar o laudo com captura de tela. Encerramento. |

## Vídeo 2: Solução atualizada (≤ 5 min)

| Tempo | Mostrar | O que falar |
|---|---|---|
| 0:00–0:30 | Menu **Laudos** no site | 5 colegas testaram em 17/11; nota média 4,6/5; 1 defeito e 4 sugestões. |
| 0:30–1:45 | Laudo do Robson → formulário de agendamento | "O Robson não conseguia agendar às 15:34 e achou a escolha de hora confusa. O campo aceitava qualquer minuto e depois recusava com 'Valor inválido'. Troquei por uma lista de 10 em 10 minutos, como ele sugeriu." Abrir a lista e mostrar. |
| 1:45–2:45 | Mesmo formulário: trocar o profissional para um que está ocupado | "Bruno e Vitória pediram ver a indisponibilidade antes de salvar. Agora os horários ocupados ficam bloqueados com o motivo e aparece um aviso se o horário escolhido deixa de valer." |
| 2:45–3:45 | Painel **Início → Vendas** (passar o mouse no gráfico; abrir "Ver os dados em tabela") | "A Vitória sentiu falta de indicadores de vendas com gráficos. Criei faturamento, ticket médio, gráfico dos últimos 7 dias e serviços mais vendidos." |
| 3:45–4:15 | Celular (F12 → modo dispositivo) | Melhorias para o celular pedidas pelo Robson: botões maiores, lista de horários nativa. |
| 4:15–4:40 | Laudo de qualidade (seção 3.4) | Sugestão de WhatsApp registrada como fora do escopo, com a justificativa. Defeito D8 encontrado no reteste. |
| 4:40–5:00 | Terminal: `pytest` | 149 testes passando depois das correções. Encerramento. |
