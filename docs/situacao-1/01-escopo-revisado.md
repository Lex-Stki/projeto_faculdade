# 1. Escopo revisado do projeto

> Situação-Problema 1: verificar e adequar o escopo e a ideia e prepará-los para a execução.

## 1.1 Histórico de revisões

| Versão | Etapa | O que mudou |
|---|---|---|
| 1.0 | PIT I | Planejamento inicial: problema, ideia da solução, requisitos e protótipo. |
| 2.0 | PIT II, Situação 1 | Escopo fechado para execução (seção 1.5). Regras de negócio numeradas e ligadas aos testes. UML revisada, com estados e sequência. IHC revisada (mensagens de erro, mapa de navegação). Modelos conceitual, lógico normalizado e físico. Dicionário de dados. |
| 2.1 | PIT II, Situação 2 | Arquitetura MVC implementada, manual de uso e de implantação, testes automatizados. |
| 2.2 | PIT II, Situação 3 | Plano de testes, formulário de laudo, laudo de qualidade com defeitos e correções. |

## 1.2 Problema

Pequenos negócios de serviços com hora marcada (salões de beleza, barbearias, esmalterias, estúdios) costumam controlar a agenda em caderno ou por mensagens no WhatsApp. Isso causa:

- **Dois clientes marcados no mesmo horário** com o mesmo profissional (*overbooking*);
- **Horários marcados fora do expediente** ou em dias em que o estabelecimento não abre;
- **Falta de histórico**: não se sabe quando o cliente veio, qual serviço fez e quanto pagou;
- **Retrabalho para remarcar e cancelar**, e cancelamentos feitos por engano que não podem ser desfeitos;
- **Falta de visão do dia**: quantos atendimentos há e quanto deve entrar no caixa.

## 1.3 Objetivo

Construir o **AgendaFácil**, uma aplicação web responsiva que funcione no computador da recepção e no celular do dono. Ela deve centralizar clientes, serviços, profissionais e agendamentos e **impedir automaticamente** os erros de agenda listados acima.

## 1.4 Partes interessadas e usuários

| Perfil | Quem é | O que precisa |
|---|---|---|
| Administrador | Dono(a) do negócio. É a primeira conta criada no sistema. | Tudo o que o atendente faz, mais consultar os laudos de teste e carregar dados de exemplo. |
| Atendente | Recepcionista ou o próprio profissional | Cadastrar clientes e agendar, remarcar, concluir e cancelar atendimentos. |
| Testador | Colegas de curso (Situação 3) | Um formulário público para registrar o que funcionou, o que falhou e sugestões. |
| Cliente final | Quem recebe o serviço | Não acessa o sistema nesta versão (ver "fora do escopo"). |

## 1.5 Escopo

### Dentro do escopo (implementado)

1. Conta de usuário com login e senha. A primeira conta vira administradora. O cadastro aberto pode ser fechado por configuração.
2. Cadastro de **clientes** com busca por nome, telefone ou e-mail, paginação e histórico de atendimentos.
3. Cadastro de **serviços** com duração e preço. Serviço já usado pode ser desativado, mas não excluído.
4. Cadastro de **profissionais**, com a mesma regra de ativar e inativar.
5. **Agendamento** com cálculo automático do horário de término e bloqueio de: horário passado, domingo, fora do expediente e conflito de profissional ou de cliente.
6. **Agenda** com filtros por dia, profissional, status e período.
7. **Remarcar, concluir, cancelar e reabrir** um agendamento. O cancelamento é reversível.
8. **Consulta de disponibilidade** em tempo real no formulário: horários já ocupados do profissional no dia.
9. **Painel do dia** com atendimentos, pendentes, receita prevista e total de clientes.
10. **Formulário de laudo de teste** público, com envio de captura de tela, e lista e exportação em CSV para o administrador.

### Fora do escopo (próximas versões)

- Agendamento feito pelo próprio cliente final (página pública de reservas);
- Lembretes automáticos por WhatsApp ou e-mail;
- Vários estabelecimentos na mesma instalação (*multi-tenant*);
- Horário de funcionamento diferente por profissional, folgas e feriados;
- Recuperação de senha por e-mail;
- Controle financeiro (formas de pagamento, comissões).

## 1.6 Premissas e restrições

- **Linguagem**: Python 3.12, uma das linguagens sugeridas pela disciplina, com o *framework* Flask.
- **Padrão de projeto**: MVC, como indica o material da disciplina.
- **Banco de dados**: PostgreSQL, um SGBD popular e de fácil manutenção, como pede o material ("nada de usar SGBD obscuros"). Em produção usa o Neon (PostgreSQL gerenciado, com plano gratuito); nos testes, SQLite em memória.
- **Hospedagem**: Render (Web Service Python, plano gratuito). O disco do serviço é temporário e se perde a cada novo deploy, por isso tudo, inclusive as capturas de tela dos testadores, fica no banco. O projeto também roda no Vercel.
- **Modo de codificação**: tradicional (HTML, CSS e JavaScript no front-end; Python no back-end), sem ferramentas *no-code*.
- **Regras de funcionamento** (configuráveis em `agendafacil/config.py`): segunda a sábado, das 08:00 às 20:00, fuso `America/Sao_Paulo`.
