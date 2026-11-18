# 2. Manual de uso

Este manual é para quem usa o sistema no dia a dia: o dono do negócio e os atendentes.

## 2.1 Primeiro acesso

1. Abra o endereço do sistema e clique em **Crie uma agora**.
2. Informe nome, e-mail e senha (mínimo de 6 caracteres) e clique em **Criar conta**.
   A **primeira conta** criada é a do **administrador**.
3. O painel mostra o quadro **Primeiros passos**. Para testar rapidamente, clique em **Carregar dados de exemplo**: o sistema cria 6 serviços, 3 profissionais e 3 clientes.

## 2.2 Menu

| Item | Para que serve |
|---|---|
| **Início** | Painel do dia: atendimentos de hoje, quantos faltam, receita prevista, total de clientes, **vendas** (faturamento e ticket médio do mês, gráfico dos últimos 7 dias, serviços mais vendidos) e os próximos agendamentos. |
| **Agenda** | Lista de agendamentos com filtros. |
| **Clientes** | Cadastro e busca de clientes. |
| **Serviços** | Serviços oferecidos, com duração e preço. |
| **Profissionais** | Quem executa os serviços. |
| **Laudos** | (somente administrador) laudos enviados pelos testadores. |
| **Sair** | Encerra a sessão. |

No celular, o menu fica no botão **Menu**, no canto superior direito.

## 2.3 Serviços e profissionais

- **+ Novo serviço**: informe nome, duração em minutos (5 a 480) e preço (ex.: `45,00`).
- **Editar** muda os dados do serviço. Agendamentos já feitos mantêm o preço da época.
- **Desativar** tira o serviço da lista de novos agendamentos sem apagar o histórico. **Reativar** traz de volta.
- **Excluir** só é permitido se o serviço nunca foi usado. Caso contrário, o sistema sugere desativar.
- Os profissionais funcionam da mesma forma (**Inativar / Reativar**). Clicar no nome de um profissional abre a agenda dele.

## 2.4 Clientes

- **Buscar**: digite parte do nome, do telefone ou do e-mail e clique em **Buscar**. Se não encontrar, o sistema oferece um link para cadastrar com o nome digitado.
- **+ Novo cliente**: nome e telefone com DDD são obrigatórios. O telefone é formatado enquanto você digita.
  - **Salvar** abre a ficha do cliente.
  - **Salvar e agendar** abre direto o formulário de agendamento com o cliente já escolhido.
- **Ficha do cliente**: dados de contato, observações e **histórico** de atendimentos (data, serviço, profissional, valor, status).
- **Excluir** só é possível para clientes sem histórico.

## 2.5 Agendar

1. Clique em **+ Novo agendamento** (no painel, na agenda ou na ficha do cliente).
2. Escolha **cliente**, **serviço** e **profissional**.
3. Escolha a **data**. Ela já vem preenchida com o primeiro dia que ainda tem horário livre. O quadro azul mostra os **horários já ocupados** daquele profissional no dia.
4. Escolha o **horário de início** na lista (de 10 em 10 minutos). Horários indisponíveis aparecem **bloqueados, com o motivo** (ex.: "indisponível: Ana Souza ocupado(a) 10:00–11:00"). O sistema mostra o **término previsto** com base na duração do serviço.
   - Se você trocar o profissional, o serviço, o cliente ou a data e o horário escolhido deixar de valer, aparece o aviso "O horário … não está mais disponível".
5. Clique em **Salvar agendamento**.

O sistema **não deixa** agendar:
- em data ou horário que já passou;
- aos domingos ou fora do horário de 08:00 às 20:00 (o atendimento precisa **terminar** até 20:00);
- em horário que se sobrepõe a outro atendimento do **mesmo profissional** ou do **mesmo cliente**.

Quando isso acontece, aparece uma mensagem explicando o motivo, e o que você já preencheu continua na tela.

## 2.6 Agenda

- Sem filtros, a agenda mostra **de hoje em diante**. Para ver o histórico, escolha **Período: Todos, inclusive passados**.
- Filtre por **dia**, **profissional** e **status** e clique em **Filtrar**. **Limpar** volta ao padrão.
- Ações em cada agendamento:

| Botão | Quando aparece | O que faz |
|---|---|---|
| **Remarcar** | Agendado | Abre o formulário para trocar data, horário, serviço ou profissional (as mesmas regras valem). |
| **Concluir** | Agendado | Marca como atendido. Só funciona depois do horário de início. |
| **Cancelar** | Agendado | Pede confirmação e libera o horário. |
| **Reabrir** | Cancelado | Desfaz um cancelamento feito por engano, se o horário ainda não passou e continua livre. |

Atendimentos **concluídos** não podem mais ser alterados.

## 2.7 Vendas (painel Início)

- Só entram atendimentos **concluídos**: use **Concluir** na agenda depois de atender.
- **Faturamento**, **atendimentos concluídos** e **ticket médio** do mês atual.
- **Gráfico de faturamento por dia** dos últimos 7 dias. Passe o mouse (ou use Tab) sobre uma coluna para ver o valor e a quantidade de atendimentos. "Ver os dados em tabela" mostra os mesmos números.
- **Serviços mais vendidos** do mês (até 5), com o valor total de cada um.

## 2.8 Laudos de teste (Situação-Problema 3)

- O formulário fica em **/feedback** (link "Testou o sistema? Envie seu laudo" no rodapé de todas as páginas). Não precisa de login.
- O testador informa nome, data do teste, o que funcionou, o que não funcionou, o que não testou, sugestões, uma nota de facilidade de uso (1 a 5) e, se quiser, uma **captura da tela** com o erro (até 2 MB).
- O administrador vê tudo em **Laudos**, abre as capturas e pode **Exportar CSV** (abre no Excel) para montar o documento de entrega.

## 2.9 Dúvidas frequentes

| Pergunta | Resposta |
|---|---|
| Esqueci a senha. | Nesta versão não há recuperação por e-mail. Crie outra conta (se o cadastro estiver aberto) ou peça ao responsável técnico. |
| Apareceu "Sua sessão expirou ou o formulário é inválido". | A página ficou aberta muito tempo ou o login mudou. Recarregue a página e repita a ação. |
| Por que não consigo excluir um serviço? | Porque ele já foi usado em agendamentos. Use **Desativar**. |
| Cancelei sem querer. | Use **Reabrir** na agenda. |
| Não consigo escolher 15:34. | Os horários andam de 10 em 10 minutos (15:30, 15:40…), conforme sugerido no teste de aceitação. |
| O gráfico de vendas está vazio. | Ele considera só atendimentos **concluídos** nos últimos 7 dias. |
