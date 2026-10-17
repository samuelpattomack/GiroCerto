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
> Crie uma landing page estática em HTML e CSS para o GiroCerto, apresentando o sistema para donos de oficina, com seções de funcionalidades e como funciona. Sem framework.

**O que a IA gerou**
Página com Bootstrap via CDN, textos genéricos de marketing e um formulário de contato que não enviava para lugar nenhum.

**O que fizemos**
- Tiramos o Bootstrap e escrevemos o CSS na mão, para a página ser leve no S3.
- Removemos o formulário falso.
- Reescrevemos os textos com os problemas que levantamos no spec.
- Adicionamos uma prévia da tela de ordem de serviço para servir de protótipo.
