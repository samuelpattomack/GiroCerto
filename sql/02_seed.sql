-- GiroCerto - dados de exemplo para demonstração
-- Rodar depois do 01_schema.sql.

INSERT INTO cliente (nome, telefone, email) VALUES
    ('Carlos Henrique Souza', '11987650001', 'carlos.souza@example.com'),
    ('Fernanda Lima',         '11987650002', NULL),
    ('Oficina Parceira Ltda', '1133224455',  'contato@example.com');

INSERT INTO veiculo (cliente_id, placa, marca, modelo, ano) VALUES
    (1, 'ABC1234', 'Volkswagen', 'Gol',    2015),
    (1, 'BRA2E19', 'Fiat',       'Toro',   2021),
    (2, 'FLM3C45', 'Chevrolet',  'Onix',   2019),
    (3, 'OFP9A88', 'Renault',    'Master', 2018);

INSERT INTO servico (nome, categoria, preco_referencia) VALUES
    ('Troca de óleo e filtro',         'REVISAO',   180.00),
    ('Troca de pastilhas dianteiras',  'FREIO',     260.00),
    ('Alinhamento e balanceamento',    'SUSPENSAO', 150.00),
    ('Troca de bateria',               'ELETRICA',  520.00),
    ('Limpeza de bicos injetores',     'MOTOR',     220.00);

INSERT INTO ordem_servico (veiculo_id, data_entrada, data_saida, quilometragem, descricao, status) VALUES
    (1, DATE '2026-09-02', DATE '2026-09-03', 98200, 'Revisão dos 100 mil e barulho no freio', 'CONCLUIDA'),
    (3, DATE '2026-09-20', DATE '2026-09-20', 45110, 'Carro puxando para a direita',          'CONCLUIDA'),
    (2, DATE '2026-10-15', NULL,              32050, 'Bateria descarregando de manhã',        'EM_ANDAMENTO'),
    (4, DATE '2026-10-21', NULL,              150300, 'Falha na partida a frio',              'ABERTA');

INSERT INTO item_ordem (ordem_id, servico_id, quantidade, valor_unitario) VALUES
    (1, 1, 1, 180.00),
    (1, 2, 1, 240.00),
    (2, 3, 1, 150.00),
    (3, 4, 1, 520.00),
    (4, 5, 1, 220.00);
