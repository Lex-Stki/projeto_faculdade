-- AgendaFácil: projeto físico do banco de dados (PostgreSQL)
-- Gerado automaticamente por scripts/gerar_schema.py a partir dos Models. Não edite à mão.

CREATE TABLE cliente (
	id SERIAL NOT NULL, 
	nome VARCHAR(100) NOT NULL, 
	telefone VARCHAR(11) NOT NULL, 
	email VARCHAR(120), 
	observacoes VARCHAR(500), 
	criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_cliente_nome ON cliente (nome);

CREATE TABLE feedback (
	id SERIAL NOT NULL, 
	nome_testador VARCHAR(100) NOT NULL, 
	email_testador VARCHAR(120), 
	data_teste DATE NOT NULL, 
	funcionou TEXT, 
	nao_funcionou TEXT, 
	nao_testado TEXT, 
	sugestoes TEXT, 
	avaliacao SMALLINT, 
	screenshot BYTEA, 
	screenshot_mime VARCHAR(30), 
	criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_feedback_avaliacao CHECK (avaliacao IS NULL OR avaliacao BETWEEN 1 AND 5)
);

CREATE TABLE profissional (
	id SERIAL NOT NULL, 
	nome VARCHAR(100) NOT NULL, 
	especialidade VARCHAR(80), 
	ativo BOOLEAN DEFAULT true NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE servico (
	id SERIAL NOT NULL, 
	nome VARCHAR(80) NOT NULL, 
	descricao VARCHAR(255), 
	duracao_min INTEGER NOT NULL, 
	preco NUMERIC(10, 2) NOT NULL, 
	ativo BOOLEAN DEFAULT true NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_servico_duracao CHECK (duracao_min BETWEEN 5 AND 480), 
	CONSTRAINT ck_servico_preco CHECK (preco >= 0), 
	UNIQUE (nome)
);

CREATE TABLE usuario (
	id SERIAL NOT NULL, 
	nome VARCHAR(100) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	senha_hash VARCHAR(255) NOT NULL, 
	perfil VARCHAR(20) DEFAULT 'atendente' NOT NULL, 
	criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_usuario_perfil CHECK (perfil IN ('admin', 'atendente'))
);
CREATE UNIQUE INDEX ix_usuario_email ON usuario (email);

CREATE TABLE agendamento (
	id SERIAL NOT NULL, 
	cliente_id INTEGER NOT NULL, 
	servico_id INTEGER NOT NULL, 
	profissional_id INTEGER NOT NULL, 
	criado_por_id INTEGER, 
	inicio TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	fim TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	status VARCHAR(20) DEFAULT 'agendado' NOT NULL, 
	preco NUMERIC(10, 2) NOT NULL, 
	observacoes VARCHAR(500), 
	criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_agendamento_intervalo CHECK (fim > inicio), 
	CONSTRAINT ck_agendamento_status CHECK (status IN ('agendado', 'concluido', 'cancelado')), 
	CONSTRAINT ck_agendamento_preco CHECK (preco >= 0), 
	FOREIGN KEY(cliente_id) REFERENCES cliente (id) ON DELETE RESTRICT, 
	FOREIGN KEY(servico_id) REFERENCES servico (id) ON DELETE RESTRICT, 
	FOREIGN KEY(profissional_id) REFERENCES profissional (id) ON DELETE RESTRICT, 
	FOREIGN KEY(criado_por_id) REFERENCES usuario (id) ON DELETE SET NULL
);
CREATE INDEX ix_agendamento_cliente_inicio ON agendamento (cliente_id, inicio);
CREATE INDEX ix_agendamento_profissional_inicio ON agendamento (profissional_id, inicio);
