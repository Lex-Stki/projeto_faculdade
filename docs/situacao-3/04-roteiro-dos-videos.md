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
| 1:30–2:30 | VS Code: pastas `models/`, `controllers/`, `views/` | Arquitetura MVC: o Model guarda as regras (abrir `Agendamento.definir`), o Controller recebe a requisição, a View mostra o HTML. Python + Flask, PostgreSQL no Neon, hospedado no Vercel. |
| 2:30–3:00 | Site no ar: criar conta | Primeira conta vira administradora; carregar dados de exemplo. |
| 3:00–3:30 | Clientes | Cadastro com máscara de telefone, validação de campo obrigatório, busca, "Salvar e agendar". |
| 3:30–4:30 | Novo agendamento | Término previsto, horários ocupados. Tentar um **conflito**, **domingo** e **19:30** e ler as mensagens. Salvar um válido. |
| 4:30–5:15 | Agenda | Filtros; Remarcar; Cancelar (diálogo) e Reabrir; tentar concluir um atendimento futuro. |
| 5:15–5:45 | Serviços | Desativar um serviço e mostrar que ele some do agendamento; tentar excluir um serviço já usado. |
| 5:45–6:15 | Celular (F12 → modo dispositivo) | Layout responsivo. |
| 6:15–7:00 | Terminal: `pytest --cov=agendafacil` | 116 testes passando e 93% de cobertura; mostrar um teste de regra de negócio e o teste E2E. |
| 7:00–7:30 | Formulário `/feedback` | Como os colegas vão testar e enviar o laudo com captura de tela. Encerramento. |

## Vídeo 2: Solução atualizada (≤ 5 min)

| Tempo | Mostrar | O que falar |
|---|---|---|
| 0:00–0:30 | Menu **Laudos** | Quantos colegas testaram, nota média e principais pontos. |
| 0:30–3:30 | Para cada defeito ou sugestão aceita: o laudo (com a captura) → o *commit* no GitHub → o sistema corrigido | "O Fulano relatou X. A causa era Y. Corrigi assim, e este teste garante que não volta." |
| 3:30–4:15 | Laudo de qualidade (`docs/situacao-3/03-laudo-de-qualidade.md`) | Defeitos da verificação interna (D1–D5), limitações conhecidas e o que ficou para a próxima versão (com justificativa). |
| 4:15–5:00 | Terminal: `pytest` | Todos os testes passando depois das correções. Encerramento. |
