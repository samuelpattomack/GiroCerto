# Registro de uso de IA

Ferramenta: GitHub Copilot Chat no VS Code.

## 09/10 - Especificação inicial

**Prompt**
> Estamos fazendo um sistema web para oficina mecânica pequena, publicado na AWS. Gere um spec.md com o problema, 3 personas e pelo menos 5 histórias de usuário. Inclua uma tabela mostrando como cada requisito (RF-01 a RF-05) se aplica ao domínio. [requisitos colados do enunciado]

**O que a IA gerou**
Um spec com 7 histórias, personas genéricas ("Usuário Administrador", "Cliente") e uma história de login com recuperação de senha.

**O que fizemos**
- Rejeitamos a persona "Cliente": o cliente da oficina não usa o sistema, só o pessoal interno.
- Removemos login e recuperação de senha. Não é exigido e tomaria tempo do que é.
- Trocamos as personas por pessoas com nome e rotina (dono, atendente, mecânico), baseadas na conversa com o dono de uma oficina conhecida de um integrante.
- A IA colocou "Agendamento" como entidade do RF-01. Trocamos por Cliente e Veículo, que é a relação 1:N que realmente existe na oficina, e deixamos agendamento fora do escopo.

## 16/10 - Critérios de aceite

**Prompt**
> Para cada história do spec.md, escreva critérios de aceite verificáveis. Evite critérios vagos como "deve ser rápido" ou "fácil de usar".

**O que a IA gerou**
De 3 a 6 critérios por história. Alguns ainda vagos, como "o sistema deve validar os dados corretamente".

**O que fizemos**
- Reescrevemos os critérios vagos dizendo exatamente qual validação (formato de placa antigo e Mercosul, telefone único, preço maior que zero).
- Acrescentamos a regra de bloqueio de exclusão quando há registros dependentes, que a IA não tinha considerado.
- Acrescentamos que ordem concluída não aceita mais itens.

## 16/10 - Arquitetura

**Prompt**
> Com base no spec.md, proponha uma arquitetura AWS respeitando as restrições do Learner Lab (sem criar roles IAM, usar LabRole, sem NAT Gateway, RDS em subnet privada). Gere o diagrama em Mermaid.

**O que a IA gerou**
Diagrama com NAT Gateway para as Lambdas acessarem o S3, Cognito para autenticação e uma EC2 rodando a API.

**O que fizemos**
- Rejeitamos o NAT Gateway, que consome o orçamento. Usamos VPC Gateway Endpoint para o S3, conforme o enunciado.
- Removemos o Cognito (sem login no escopo).
- A EC2 virou ponto de discussão e levou ao ADR-001; ficamos com Lambda.
- Adicionamos o bastion para rodar os scripts SQL no RDS privado.

## 16/10 - Modelo de dados e rotas

**Prompt**
> Gere o diagrama ER em Mermaid e a tabela de rotas REST para as entidades Cliente, Veículo, Ordem de Serviço, Serviço e Anexo.

**O que a IA gerou**
Modelo com a tabela de itens com id próprio e o valor do serviço só na tabela servico.

**O que fizemos**
- Mudamos `item_ordem` para chave composta (ordem_id, servico_id).
- Colocamos `valor_unitario` no item. Sem isso, mudar o preço do catálogo alteraria o valor de ordens antigas e quebraria o relatório de faturamento.
- Acrescentamos `situacao` no anexo para o front saber se a miniatura já foi gerada.
- Rotas: aceitamos quase todas; trocamos `PATCH /ordens/{id}/status` por `PUT /ordens/{id}` para simplificar o roteamento na Lambda.

## 16/10 - ADR do RNF-04

**Prompt**
> Compare rodar o CRUD em Lambda com API Gateway versus container em EC2 no contexto do AWS Learner Lab (sessão expira, IP muda, orçamento limitado). Escreva no formato ADR.

**O que a IA gerou**
Uma comparação equilibrada que recomendava EC2 com Docker por ser "mais próximo de um ambiente real".

**O que fizemos**
Discordamos da recomendação. O argumento principal para nós foi o RNF-03: o endpoint do API Gateway não muda entre sessões, e a EC2 mudaria de IP. Reescrevemos a decisão e os motivos, mantendo das consequências o ponto sobre conexões com o RDS, que a IA levantou bem.

## 16/10 - Landing page

**Prompt**
> Crie uma landing page estática em HTML e CSS para o GiroCerto, apresentando o sistema para donos de oficina, com seções de funcionalidades e como funciona. Sem framework. (Feito por nos)

**O que a IA gerou**
Página com Bootstrap via CDN, textos genéricos de marketing e um formulário de contato que não enviava para lugar nenhum.

**O que fizemos**
- Tiramos o Bootstrap e escrevemos o CSS na mão, para a página ser leve no S3.
- Removemos o formulário falso.
- Reescrevemos os textos com os problemas que levantamos no spec.
- Adicionamos uma prévia da tela de ordem de serviço para servir de protótipo.

## 22/10 - Entrega 3 (rede, RDS e CRUD)

Ferramenta: Claude Code (agente no terminal), com o enunciado, `specs/spec.md` e `specs/design.md` como contexto.

O pedido feito à IA foi curto: *"Quero que faça tudo que a entrega do dia 23 pede, menos o vídeo."* Funcionou porque a spec e o design já estavam detalhados, mas para o registro (e para repetir o trabalho se precisar) dividimos o pedido nas partes abaixo. Cada **Prompt** é a versão detalhada do que foi pedido, escrita por nós depois; os pedidos de correção no fim são os textos reais.

### Scripts SQL

**Prompt**
> Com base no modelo ER e na seção "Regras no banco" do `specs/design.md`, gere `sql/01_schema.sql` para PostgreSQL 16 que possa ser rodado de novo sem erro (apaga e recria as tabelas). Use `ON DELETE RESTRICT` em `veiculo.cliente_id` e `ordem_servico.veiculo_id`, chave composta em `item_ordem`, os `CHECK` de status, categoria, preço e quantidade, e valide placa (ABC1234 ou ABC1D23) e e-mail no banco. Crie índices nas FKs. Gere também `sql/02_seed.sql` com 3 clientes, 4 veículos, 5 serviços e ordens concluídas em pelo menos dois meses diferentes, para o relatório da próxima entrega ter dados. (Prompt, alias, gerado com ajuda de IA para esclarecer de forma melhor para a IA oque ela deveria fazer)

**O que a IA gerou**
Os dois scripts. Além do pedido, colocou `ON DELETE RESTRICT` também em `item_ordem.servico_id` e `CASCADE` de ordem para itens e anexos.

**O que fizemos**
- Aceitamos o RESTRICT em `servico_id`: é ele que impede excluir um serviço já usado (HU-04).
- Aceitamos o CASCADE de ordem para itens: só ordens ABERTA podem ser excluídas, e os itens não fazem sentido sem a ordem.
- Rodamos os dois scripts num PostgreSQL local antes de usar no RDS.

### Lambda do CRUD

**Prompt**
> Implemente em Python a Lambda `crud` descrita no ADR-001, para o API Gateway REST com integração proxy em `/{proxy+}`. Ela deve atender todas as rotas da tabela "Rotas da API" do `design.md`, exceto anexos e relatórios, e aplicar os critérios de aceite das HU-01 a HU-04 do `spec.md`: telefone e placa únicos (409), exclusão bloqueada quando há dependentes (409 com mensagem explicando), preço maior que zero, ordem CONCLUIDA ou CANCELADA sem alterações, data de saída preenchida ao concluir e valor do item sugerido pelo preço de referência. Leia a conexão de `DB_HOST`, `DB_NAME`, `DB_USER` e `DB_PASSWORD`, crie a conexão fora do handler, use apenas consultas parametrizadas e responda `OPTIONS` com os cabeçalhos CORS. A Lambda roda na VPC sem internet, então escolha um driver que possa ir dentro do .zip, e crie um script que gere esse .zip. (Prompt, alias, gerado com ajuda de IA para esclarecer de forma melhor para a IA oque ela deveria fazer)

**O que a IA gerou**
- `backend/crud/app.py` com uma tabela de rotas e uma função por operação.
- `scripts/empacotar-crud.sh`, que baixa o driver para Linux e o certificado do RDS.

**O que fizemos**
- Ficamos com o driver `pg8000`, que a IA propôs por ser Python puro (ADR-005). O `psycopg2` precisaria de binário compilado para Linux.
- Registramos no `design.md` a decisão do recurso `/{proxy+}` (ADR-006), para não criar 21 métodos à mão no console.
- No teste local, a exclusão de um cliente com veículos voltava 400 em vez de 409. A primeira versão reconhecia o erro pelo texto da mensagem do PostgreSQL, que veio em português. A correção foi decidir pelo método HTTP: violação de FK num DELETE é sempre registro dependente.
- Testamos todas as rotas contra o PostgreSQL local, incluindo os erros: placa inválida, telefone duplicado, cliente inexistente e ordem fechada.

### Infraestrutura e README

**Prompt**
> Escreva no README o passo a passo para criar pelo console da AWS, no Learner Lab, a arquitetura do `design.md`: VPC com uma subnet pública e duas privadas, Internet Gateway, tabelas de rota, os três Security Groups, DB subnet group, RDS PostgreSQL `db.t3.micro` sem acesso público, bastion para rodar os scripts SQL, Lambda na VPC e API Gateway com stage `prod`. Restrições: sem CloudFormation/Terraform/SAM, sem NAT Gateway, usar `LabRole` e `LabInstanceProfile` em vez de criar roles, nenhum IP fixo e nenhuma senha no repositório. Inclua o que fazer ao iniciar uma nova sessão do Learner Lab. (Pedimos para a IA deixar o readme claro e formalizado)

**O que a IA gerou**
O README com as 8 seções e a seção "Ao iniciar uma nova sessão". Também apontou que o bastion precisa de saída 80/443 para instalar o `psql`, o que não estava no `design.md`.

**O que fizemos**
- Acrescentamos a regra de saída no `sg-bastion` e no `design.md`.
- Completamos no `design.md` o Internet Gateway, as tabelas de rota e a explicação de como a Lambda chega ao RDS por referência de Security Group.
- Criamos o `specs/tasks.md` com as tarefas desta e das próximas entregas.

### Tela de cadastros

**Prompt**
> Crie `web/app.html` com HTML, CSS e JavaScript puro, reaproveitando o `style.css` da landing page, para listar, buscar, criar, editar e excluir clientes e veículos pela API. A URL da API deve vir de um `config.js` gerado no deploy (RNF-03). Mostre as mensagens de erro da API, para o usuário ver por que uma exclusão foi bloqueada, e escape os textos antes de montar a tabela.

**O que a IA gerou**
A tela, o `web/config.example.js` e um `scripts/servidor_local.py` que imita o API Gateway e o S3, para testar sem AWS.

### Correções pedidas depois do teste

Rodamos a tela localmente e pedimos correções.

**Prompt real**
> Quando tento editar algo, nada acontece. Me de solucoes e me ajude a resolver o retorno da API.

**O que aconteceu**
O clique funcionava, mas a tela não mostrava que estava editando. A IA destacou o formulário e trocou os botões para "Salvar alterações (#id)" e "Cancelar edição". Ao testar, ela mesma encontrou um bug mais grave: o "Limpar" não apagava o id escondido, então o próximo cadastro "novo" sobrescreveria o registro editado. Foi corrigido. O servidor local também passou a mandar o navegador não usar cache.

**Prompt real**
> Estou usando macOS. Adapte, tambem, para windows para todos os sistemas operacionais rodarem o programa.

**O que aconteceu**
Os comandos do README eram só de macOS/Linux. A IA acrescentou as versões para Windows (PowerShell, `icacls` para a chave do bastion e o CloudShell para gerar o .zip da Lambda).

## 29/10 - Entrega 4 (anexos, Lambda de evento, relatório e front)

Ferramenta: Claude Code, com `specs/spec.md`, `specs/design.md`, `specs/tasks.md` e o enunciado como contexto. A infraestrutura da entrega 3 já estava rodando na AWS.

**Prompt real**
> Pode fazer a entrega do dia 30 também.

**O que a IA gerou**
- Na Lambda `crud`, as rotas `POST /ordens/{id}/anexos/upload-url` (registra o anexo como `PENDENTE` e devolve a URL pré-assinada de PUT) e `GET /ordens/{id}/anexos` (devolve URLs pré-assinadas de leitura) (RF-02).
- A Lambda `processa-anexo`, disparada pelo evento do S3 em `uploads/`: confere tipo e tamanho, gera a miniatura em `thumbs/` com a biblioteca Pillow e grava o resultado na tabela `anexo` (RF-03).
- A Lambda `relatorios`, com faturamento mensal e top 10 serviços usando JOIN e GROUP BY (RF-04).
- No front, as abas Serviços, Ordens (itens, status e envio de fotos com acompanhamento da miniatura) e Relatórios (RF-05).
- O `scripts/empacotar.sh` para as três Lambdas, o módulo comum `backend/comum/banco.py`, os passos 9 a 11 do README e os ADR-007 e ADR-008.

**Decisões que a IA propôs**
- Prefixos separados `uploads/` e `thumbs/`, com o evento só em `uploads/`, para a miniatura não disparar a própria Lambda em loop (ADR-007).
- Bucket de anexos privado, com leitura também por URL pré-assinada, em vez de deixar as fotos públicas.
- Como a URL de PUT não limita o tamanho, a Lambda confere o tamanho real e marca `ERRO` acima de 10 MB.
- Relatórios numa Lambda separada, com recurso próprio no API Gateway (ADR-008).

**Problemas encontrados no teste**
- A IA testou as três Lambdas contra um PostgreSQL local, com o S3 simulado na `processa-anexo`: foto de 1600x900 virou miniatura de 320x180, um arquivo que não era imagem ficou `ERRO` e um arquivo fora da tabela foi ignorado.
- Ao testar a tela, a lista de ordens deu erro 500 com a mensagem `bind message supplies 2 parameters`. A causa era o servidor local: ele atende várias requisições ao mesmo tempo e todas usavam a mesma conexão com o banco, e a tela nova faz chamadas em paralelo. Na AWS isso não acontece, porque cada instância de Lambda atende uma requisição por vez. A correção foi o servidor local executar uma chamada de Lambda por vez.
- A mensagem "Ordem de serviço não encontrado" foi corrigida para o feminino, e os status passaram a aparecer com acento na tela ("Concluída").
