# 3. Instalação local e publicação no Vercel

## 3.1 Rodar no computador (desenvolvimento)

Pré-requisitos: Python 3.12 ou superior e Git.

```bash
git clone https://github.com/Lex-Stki/projeto_faculdade.git
cd projeto_faculdade
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements-dev.txt
flask --app agendafacil run --debug
```

Abra http://127.0.0.1:5000. Sem `DATABASE_URL`, o sistema usa SQLite em `instance/agendafacil.db`. Para testar com PostgreSQL localmente, crie um arquivo `.env` a partir de `.env.example` ou exporte as variáveis.

Comandos úteis:

| Comando | O que faz |
|---|---|
| `flask --app agendafacil seed` | Cria dados de demonstração |
| `pytest` | Roda todos os testes (unidade, integração e E2E) |
| `pytest --cov=agendafacil --cov-report=term-missing` | Testes com relatório de cobertura |
| `pytest tests/e2e` | Só os testes no navegador (precisa de Edge/Chrome e `pip install playwright`) |
| `E2E_EVIDENCIAS=1 pytest tests/e2e` | Gera as capturas em `docs/situacao-3/evidencias/` |
| `python scripts/gerar_schema.py` | Regenera `docs/situacao-1/schema.sql` |

## 3.2 Publicar no Vercel com PostgreSQL (Neon)

### Passo 1: Importar o repositório
1. Entre em https://vercel.com com sua conta do GitHub.
2. **Add New… → Project** e escolha o repositório `projeto_faculdade` (**Import**).
3. Em **Framework Preset**, deixe **Other** (o `vercel.json` já define isso).
4. Abra **Environment Variables** e adicione:
   - `SECRET_KEY`: um valor aleatório longo. Para gerar: `python -c "import secrets; print(secrets.token_hex(32))"`
5. Clique em **Deploy**. O primeiro deploy pode mostrar erro ao abrir o site porque o banco ainda não existe. Isso é esperado.

### Passo 2: Criar o banco PostgreSQL (Neon)
1. No projeto do Vercel, abra a aba **Storage → Create Database → Neon (Serverless Postgres)**.
2. Escolha a **mesma região das funções do Vercel** (padrão: `Washington, D.C. (iad1)`; um banco em São Paulo deixaria cada consulta mais lenta, porque a função roda nos EUA), aceite o plano gratuito e **conecte ao projeto** (marque Production e Preview).
3. O Vercel cria sozinho a variável `DATABASE_URL`. A aplicação também aceita `POSTGRES_URL`.

### Passo 3: Publicar de novo
1. Aba **Deployments → (último deploy) → ⋯ → Redeploy**.
2. Acesse `https://SEU-PROJETO.vercel.app/saude`. Deve aparecer `{"banco":"ok","status":"ok"}`.
3. Acesse a página inicial, **crie a conta de administrador** (a primeira conta) e, se quiser, carregue os dados de exemplo.

As tabelas são criadas automaticamente na primeira requisição. Se preferir criá-las à mão, rode o conteúdo de [`docs/situacao-1/schema.sql`](../situacao-1/schema.sql) no **SQL Editor** do Neon.

### Passo 4: Depois do período de testes
Quando os 5 colegas terminarem de testar, adicione a variável `CADASTRO_ABERTO=0` e faça *redeploy*. A partir daí ninguém mais consegue criar conta pelo site.

A cada `git push` na branch `main`, o Vercel publica a nova versão automaticamente.

## 3.3 Variáveis de ambiente

| Variável | Obrigatória no Vercel | Descrição |
|---|---|---|
| `SECRET_KEY` | Sim | Assina o cookie de sessão. Sem ela, a aplicação não inicia em produção. |
| `DATABASE_URL` (ou `POSTGRES_URL`) | Sim | URL do PostgreSQL. Criada pela integração com o Neon. |
| `CADASTRO_ABERTO` | Não | `1` (padrão) permite criar contas; `0` fecha o cadastro. |

## 3.4 Problemas comuns

| Sintoma | Causa / solução |
|---|---|
| "Erro interno" em todas as páginas logo após o deploy | Faltou `SECRET_KEY` ou `DATABASE_URL`. Confira em **Settings → Environment Variables** e faça *redeploy*. Os detalhes aparecem em **Logs**. |
| `/saude` responde `503` | A aplicação está no ar, mas não conecta ao banco. Verifique a `DATABASE_URL` e se o banco do Neon está ativo. |
| Usuários "deslogados" a cada acesso | `SECRET_KEY` mudando entre deploys. Use um valor fixo. |
| Captura de tela recusada no laudo | O arquivo passa de 2 MB ou não é PNG/JPG/GIF/WEBP. |
