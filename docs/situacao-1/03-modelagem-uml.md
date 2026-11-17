# 3. Modelagem UML (revisada)

Os diagramas estão em [Mermaid](https://mermaid.js.org/), que o GitHub desenha automaticamente. Assim os diagramas ficam versionados junto com o código.

**Revisões em relação ao planejamento inicial:**
- O diagrama de classes ganhou os **métodos** que guardam as regras de negócio (`definir`, `alterar_status`, `conflitos`), e não só os atributos.
- Entrou a classe **Profissional**. Sem ela não dá para verificar conflito de horário quando há mais de uma pessoa atendendo.
- O **preço** passou a ser gravado também no `Agendamento`, para preservar o histórico (RN07).
- Foram incluídos o **diagrama de estados** do agendamento, que deixa explícitas as transições permitidas (RN08), e o **diagrama de sequência** do caso de uso principal.

## 3.1 Diagrama de casos de uso

```mermaid
flowchart LR
    adm(["👤 Administrador"])
    atd(["👤 Atendente"])
    tst(["👤 Testador"])

    subgraph Sistema["AgendaFácil"]
        UC01([UC01 Entrar / criar conta])
        UC02([UC02 Manter clientes])
        UC03([UC03 Manter serviços])
        UC04([UC04 Manter profissionais])
        UC05([UC05 Agendar atendimento])
        UC06([UC06 Consultar agenda])
        UC07([UC07 Remarcar / concluir / cancelar / reabrir])
        UC08([UC08 Ver painel do dia])
        UC09([UC09 Enviar laudo de teste])
        UC10([UC10 Consultar e exportar laudos])
        UC11([Verificar disponibilidade])
    end

    atd --- UC01 & UC02 & UC03 & UC04 & UC05 & UC06 & UC07 & UC08
    adm -. herda de .-> atd
    adm --- UC10
    tst --- UC09
    UC05 -. include .-> UC11
    UC07 -. include .-> UC11
```

### Especificação do caso de uso principal: UC05 Agendar atendimento

| Item | Descrição |
|---|---|
| Ator | Atendente (ou Administrador) |
| Pré-condições | Usuário autenticado; existe ao menos um serviço e um profissional ativos |
| Fluxo principal | 1. O ator abre "Novo agendamento". 2. Escolhe cliente, serviço e profissional. 3. Informa data e horário. 4. O sistema mostra o horário previsto de término e os horários já ocupados do profissional. 5. O ator salva. 6. O sistema valida as regras RN01–RN06, grava e mostra a agenda do dia com a mensagem de sucesso. |
| Fluxo alternativo A1 | Cliente não cadastrado: o ator usa "Cadastrar novo cliente" e depois "Salvar e agendar", que volta ao formulário com o cliente já escolhido. |
| Fluxo de exceção E1 | Conflito de horário (RN03/RN04): o sistema não grava, informa com quem e em que horário é o conflito e mantém os dados digitados. |
| Fluxo de exceção E2 | Horário inválido (RN01/RN02): o sistema explica a regra (ex.: "terminaria às 20:30") e mantém os dados. |
| Pós-condição | Agendamento gravado com status **agendado**, preço do serviço copiado e usuário criador registrado. |

## 3.2 Diagrama de classes (modelo de domínio / persistência)

```mermaid
classDiagram
    direction LR
    class Usuario {
        +int id
        +str nome
        +str email
        -str senha_hash
        +str perfil
        +datetime criado_em
        +definir_senha(senha)
        +verificar_senha(senha) bool
        +validar_cadastro(nome, email, senha)$
    }
    class Cliente {
        +int id
        +str nome
        +str telefone
        +str email
        +str observacoes
        +datetime criado_em
        +preencher(dados) list
    }
    class Servico {
        +int id
        +str nome
        +str descricao
        +int duracao_min
        +Decimal preco
        +bool ativo
        +preencher(dados) list
    }
    class Profissional {
        +int id
        +str nome
        +str especialidade
        +bool ativo
        +preencher(dados) list
    }
    class Agendamento {
        +int id
        +datetime inicio
        +datetime fim
        +str status
        +Decimal preco
        +str observacoes
        +datetime criado_em
        +definir(dados, referencia) list
        +alterar_status(novo, referencia) str
        +conflitos(inicio, fim)$
        -_validar_horario(referencia) list
        -_validar_conflitos() list
    }
    class Feedback {
        +int id
        +str nome_testador
        +str email_testador
        +date data_teste
        +str funcionou
        +str nao_funcionou
        +str nao_testado
        +str sugestoes
        +int avaliacao
        +bytes screenshot
        +preencher(dados, arquivo) list
    }

    Cliente "1" -- "0..*" Agendamento : recebe
    Servico "1" -- "0..*" Agendamento : é prestado em
    Profissional "1" -- "0..*" Agendamento : executa
    Usuario "0..1" -- "0..*" Agendamento : cria
```

`Feedback` é independente das demais: guarda os laudos dos testadores (Situação 3).

## 3.3 Diagrama de estados: Agendamento

```mermaid
stateDiagram-v2
    [*] --> Agendado : criar (RN01–RN06)
    Agendado --> Agendado : remarcar
    Agendado --> Concluido : concluir [agora ≥ início]
    Agendado --> Cancelado : cancelar
    Cancelado --> Agendado : reabrir [horário futuro e livre]
    Concluido --> [*]
```

## 3.4 Diagrama de sequência: UC05 Agendar atendimento (padrão MVC)

```mermaid
sequenceDiagram
    autonumber
    actor A as Atendente
    participant V as View<br/>(form.html + agendamento.js)
    participant C as Controller<br/>(agendamentos.novo)
    participant M as Model<br/>(Agendamento)
    participant DB as PostgreSQL

    A->>V: escolhe profissional e data
    V->>C: GET /agendamentos/disponibilidade
    C->>M: Agendamento.conflitos(dia)
    M->>DB: SELECT agendamentos que se sobrepõem ao dia
    DB-->>M: horários ocupados
    C-->>V: JSON
    V-->>A: "Horários já ocupados de Ana: 10:00–11:00"
    A->>V: informa 14:00 e clica em Salvar
    V->>V: validação no navegador (campos obrigatórios)
    V->>C: POST /agendamentos/novo (+ token CSRF)
    C->>M: definir(dados)
    M->>DB: busca cliente, serviço, profissional e conflitos
    alt regras atendidas
        C->>DB: INSERT agendamento + COMMIT
        C-->>A: redireciona para a agenda do dia + "Agendamento criado"
    else alguma regra violada
        M-->>C: lista de erros
        C-->>A: mesmo formulário, dados mantidos + mensagens de erro
    end
```

## 3.5 Diagrama de atividades: atender um cliente no dia

```mermaid
flowchart TD
    I((Início)) --> B{Cliente já<br/>cadastrado?}
    B -- Não --> C[Cadastrar cliente<br/>'Salvar e agendar']
    B -- Sim --> D[Abrir Novo agendamento]
    C --> D
    D --> E[Escolher serviço, profissional,<br/>data e hora]
    E --> F{Horário livre e<br/>dentro das regras?}
    F -- Não --> G[Ler mensagem e<br/>ajustar horário/profissional] --> E
    F -- Sim --> H[Agendamento criado]
    H --> J{Cliente<br/>compareceu?}
    J -- Sim --> K[Concluir atendimento]
    J -- Desmarcou --> L[Cancelar]
    J -- Pediu outro horário --> M[Remarcar] --> F
    L --> N{Cancelou<br/>por engano?}
    N -- Sim --> O[Reabrir] --> J
    N -- Não --> Z((Fim))
    K --> Z
```
