-- GiroCerto - schema do banco (PostgreSQL 16+)
-- Rodar a partir do bastion:
--   psql "host=<endpoint-rds> port=5432 dbname=girocerto user=<usuario> sslmode=require" -f sql/01_schema.sql
-- O script pode ser rodado de novo: apaga e recria as tabelas.

DROP TABLE IF EXISTS anexo, item_ordem, ordem_servico, servico, veiculo, cliente CASCADE;

CREATE TABLE cliente (
    id         SERIAL PRIMARY KEY,
    nome       VARCHAR(120) NOT NULL,
    telefone   VARCHAR(20)  NOT NULL UNIQUE,
    email      VARCHAR(160),
    criado_em  TIMESTAMP    NOT NULL DEFAULT now(),
    CHECK (email IS NULL OR email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$')
);

CREATE TABLE veiculo (
    id          SERIAL PRIMARY KEY,
    cliente_id  INT         NOT NULL REFERENCES cliente (id) ON DELETE RESTRICT,
    placa       VARCHAR(7)  NOT NULL UNIQUE,
    marca       VARCHAR(60) NOT NULL,
    modelo      VARCHAR(60) NOT NULL,
    ano         SMALLINT    NOT NULL,
    -- formato antigo (ABC1234) ou Mercosul (ABC1D23)
    CHECK (placa ~ '^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$'),
    CHECK (ano BETWEEN 1950 AND 2100)
);

CREATE INDEX idx_veiculo_cliente ON veiculo (cliente_id);

CREATE TABLE servico (
    id                SERIAL PRIMARY KEY,
    nome              VARCHAR(120)  NOT NULL,
    categoria         VARCHAR(20)   NOT NULL,
    preco_referencia  NUMERIC(10,2) NOT NULL,
    ativo             BOOLEAN       NOT NULL DEFAULT true,
    CHECK (categoria IN ('MOTOR','FREIO','SUSPENSAO','ELETRICA','REVISAO','OUTROS')),
    CHECK (preco_referencia > 0)
);

CREATE TABLE ordem_servico (
    id             SERIAL PRIMARY KEY,
    veiculo_id     INT         NOT NULL REFERENCES veiculo (id) ON DELETE RESTRICT,
    data_entrada   DATE        NOT NULL DEFAULT current_date,
    data_saida     DATE,
    quilometragem  INT         NOT NULL,
    descricao      TEXT        NOT NULL,
    status         VARCHAR(15) NOT NULL DEFAULT 'ABERTA',
    CHECK (status IN ('ABERTA','EM_ANDAMENTO','CONCLUIDA','CANCELADA')),
    CHECK (quilometragem >= 0),
    CHECK (data_saida IS NULL OR data_saida >= data_entrada)
);

CREATE INDEX idx_ordem_veiculo ON ordem_servico (veiculo_id);
CREATE INDEX idx_ordem_status ON ordem_servico (status);

CREATE TABLE item_ordem (
    ordem_id        INT           NOT NULL REFERENCES ordem_servico (id) ON DELETE CASCADE,
    servico_id      INT           NOT NULL REFERENCES servico (id) ON DELETE RESTRICT,
    quantidade      INT           NOT NULL DEFAULT 1,
    valor_unitario  NUMERIC(10,2) NOT NULL,
    PRIMARY KEY (ordem_id, servico_id),
    CHECK (quantidade > 0),
    CHECK (valor_unitario >= 0)
);

CREATE INDEX idx_item_servico ON item_ordem (servico_id);

-- Preenchida pela Lambda processa-anexo (RF-03, entrega de 30/10)
CREATE TABLE anexo (
    id               SERIAL PRIMARY KEY,
    ordem_id         INT          NOT NULL REFERENCES ordem_servico (id) ON DELETE CASCADE,
    chave_s3         VARCHAR(300) NOT NULL UNIQUE,
    chave_miniatura  VARCHAR(300),
    nome_original    VARCHAR(200) NOT NULL,
    tipo             VARCHAR(60)  NOT NULL,
    tamanho_bytes    BIGINT,
    largura          INT,
    altura           INT,
    situacao         VARCHAR(12)  NOT NULL DEFAULT 'PENDENTE',
    enviado_em       TIMESTAMP    NOT NULL DEFAULT now(),
    CHECK (situacao IN ('PENDENTE','PROCESSADO','ERRO')),
    CHECK (tipo IN ('image/jpeg','image/png','application/pdf'))
);

CREATE INDEX idx_anexo_ordem ON anexo (ordem_id);
