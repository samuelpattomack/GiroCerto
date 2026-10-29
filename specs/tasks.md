# GiroCerto - Tarefas

Status: `A fazer`, `Em andamento`, `Concluída`. Cada tarefa é pequena o bastante para um prompt de implementação no Copilot, com `spec.md` e `design.md` como contexto.

Responsáveis: **LB** = Lucas Zeferino Baracat, **SP** = Samuel Patto Marcondes Manfredini Ferreira.

## Entrega 1 e 2 (09/10 e 16/10)

| ID | Tarefa | Requisito | Resp. | Status |
|----|--------|-----------|-------|--------|
| T-01 | Criar repositório e dar acesso ao professor | - | LB | Concluída |
| T-02 | Escrever `spec.md` inicial (problema, personas, histórias) | RF-01..05 | LB, SP | Concluída |
| T-03 | Critérios de aceite das histórias | HU-01..06 | SP | Concluída |
| T-04 | Diagrama de arquitetura, rede e Security Groups no `design.md` | RNF-01 | LB | Concluída |
| T-05 | Modelo ER e tabela de rotas da API | RF-01 | SP | Concluída |
| T-06 | ADR-001: CRUD em Lambda ou container | RNF-04 | LB, SP | Concluída |
| T-07 | Landing page em `web/` publicada no S3 | RF-05 | SP | Concluída |

## Entrega 3 (23/10): rede, RDS e CRUD

| ID | Tarefa | Requisito | Resp. | Status |
|----|--------|-----------|-------|--------|
| T-08 | Criar VPC, subnet pública, 2 subnets privadas, IGW e tabelas de rota | RNF-01 | LB | Concluída |
| T-09 | Criar `sg-lambda`, `sg-rds` e `sg-bastion` e documentar no `design.md` | RNF-01 | LB | Concluída |
| T-10 | Criar DB subnet group e RDS PostgreSQL privado `db.t3.micro` | RNF-01 | SP | Concluída |
| T-11 | Escrever `sql/01_schema.sql` com tabelas, FKs e CHECKs | RF-01 | SP | Concluída |
| T-12 | Escrever `sql/02_seed.sql` com dados de exemplo | RF-01 | SP | Concluída |
| T-13 | Criar bastion e rodar os scripts SQL no RDS | RNF-01 | SP | Concluída |
| T-14 | Lambda `crud`: conexão com o RDS por variáveis de ambiente e roteamento | RF-01, RNF-02 | LB | Concluída |
| T-15 | CRUD de clientes, com busca e bloqueio de exclusão | HU-01 | LB | Concluída |
| T-16 | CRUD de veículos, com validação de placa e bloqueio de exclusão | HU-02 | LB | Concluída |
| T-17 | CRUD de serviços, com desativação | HU-04 | SP | Concluída |
| T-18 | Ordens de serviço e itens, com total e regras de status | HU-03 | SP | Concluída |
| T-19 | Script de empacotamento da Lambda (`scripts/empacotar-crud.sh`) | RNF-05 | LB | Concluída |
| T-20 | Publicar Lambda `girocerto-crud` na VPC com a `LabRole` | RF-01, RNF-04 | LB | Concluída |
| T-21 | API Gateway REST com `/{proxy+}`, CORS e stage `prod` | RF-01 | LB | Concluída |
| T-22 | Tela `web/app.html` de clientes e veículos consumindo a API | RF-01, RF-05 | SP | Concluída |
| T-23 | Script `scripts/testar-api.sh` para demonstrar o CRUD | RF-01 | SP | Concluída |
| T-24 | README com passo a passo da infraestrutura e da nova sessão | RNF-03, RNF-05 | LB, SP | Concluída |
| T-25 | Gravar vídeo de até 5 min e enviar com o link do repositório | - | LB, SP | Concluída |

## Entrega 4 (30/10): anexos, Lambda de evento, relatório e front

| ID | Tarefa | Requisito | Resp. | Status |
|----|--------|-----------|-------|--------|
| T-26 | Bucket `girocerto-anexos` com CORS para PUT do site | RF-02 | SP | Concluída |
| T-27 | Rota `POST /ordens/{id}/anexos/upload-url` gerando URL pré-assinada | RF-02, HU-05 | LB | Concluída |
| T-28 | Rota `GET /ordens/{id}/anexos` com URL de leitura | HU-05 | LB | Concluída |
| T-29 | Gateway Endpoint do S3 na `rt-privada` | RF-03 | LB | Concluída |
| T-30 | Lambda `processa-anexo`: metadados, miniatura e gravação no RDS | RF-03 | SP | Concluída |
| T-31 | Evento `ObjectCreated` em `uploads/` disparando a Lambda, com log no CloudWatch | RF-03 | SP | Concluída |
| T-32 | Lambda `relatorios` com faturamento mensal e top 10 serviços (JOIN/GROUP BY) | RF-04, HU-06 | LB | Concluída |
| T-33 | Recurso `/relatorios/{proxy+}` no API Gateway | RF-04 | LB | Concluída |
| T-34 | Telas de serviços, ordens, anexos e relatórios no front | RF-05 | SP | Concluída |
| T-35 | Revisar `design.md` para refletir o que está rodando | - | LB, SP | Concluída |

## Entrega final (06/11)

| ID | Tarefa | Requisito | Resp. | Status |
|----|--------|-----------|-------|--------|
| T-36 | Prints da aplicação e dos recursos AWS em `docs/evidencias/` | - | LB, SP | A fazer |
| T-37 | Reflexão final no `ia-log.md` | - | LB, SP | A fazer |
| T-38 | Gerar ZIP com código, SQL, README e `specs/` | - | LB | A fazer |
