# GiroCerto - Especificação

## Problema

Oficinas mecânicas de pequeno porte ainda controlam ordens de serviço em papel, planilha ou grupo de WhatsApp. Isso gera três problemas recorrentes:

- O histórico do veículo se perde. Quando o cliente volta, ninguém sabe o que já foi trocado nem quando.
- Fotos do carro na entrada (riscos, amassados, painel) ficam no celular do mecânico e não ficam ligadas à ordem de serviço, o que causa discussão na hora da entrega.
- O dono da oficina não sabe quanto faturou no mês nem quais serviços mais saem, porque os dados estão espalhados.

O GiroCerto é um sistema web para registrar clientes, veículos e ordens de serviço, anexar fotos e documentos a cada ordem e consultar relatórios simples de faturamento.

## Personas

**Marcos, 48 anos, dono da oficina.** Cuida do caixa e dos orçamentos. Usa o computador do balcão. Quer saber no fim do mês quanto entrou e quais serviços valem mais a pena.

**Juliana, 29 anos, atendente.** Recebe o cliente, cadastra o carro e abre a ordem de serviço. Precisa de um cadastro rápido, sem campos desnecessários.

**Rafael, 35 anos, mecânico.** Tira fotos do veículo na entrada e durante o serviço. Quer subir a foto pelo celular e não precisar mandar para ninguém depois.

## Histórias de usuário

### HU-01 - Cadastrar cliente
Como atendente, quero cadastrar um cliente com nome, telefone e e-mail para conseguir encontrá-lo nas próximas visitas.

Critérios de aceite:
- Nome e telefone são obrigatórios; e-mail é opcional mas, se informado, precisa ter formato válido.
- Não é possível cadastrar dois clientes com o mesmo telefone.
- O cliente pode ser editado e excluído. A exclusão é bloqueada se ele tiver veículos cadastrados, e o sistema mostra uma mensagem explicando o motivo.
- A listagem permite buscar por nome ou telefone.

### HU-02 - Cadastrar veículo de um cliente
Como atendente, quero vincular um ou mais veículos a um cliente para registrar o histórico de cada carro separadamente.

Critérios de aceite:
- Placa, marca, modelo e ano são obrigatórios.
- A placa é única no sistema e aceita os formatos antigo (ABC1234) e Mercosul (ABC1D23).
- Na tela do cliente aparecem todos os veículos dele.
- O veículo pode ser editado e excluído; a exclusão é bloqueada se houver ordens de serviço ligadas a ele.

### HU-03 - Abrir e acompanhar ordem de serviço
Como atendente, quero abrir uma ordem de serviço para um veículo, escolhendo os serviços do catálogo, para registrar o que será feito e quanto vai custar.

Critérios de aceite:
- A ordem tem veículo, data de entrada, quilometragem, descrição do problema e status (ABERTA, EM_ANDAMENTO, CONCLUIDA, CANCELADA).
- É possível adicionar e remover serviços do catálogo na ordem, com quantidade e valor cobrado.
- O valor total da ordem é calculado a partir dos itens e aparece na tela.
- Ao mudar o status para CONCLUIDA, a data de saída é preenchida automaticamente.
- Uma ordem CONCLUIDA ou CANCELADA não aceita mais alteração de itens.

### HU-04 - Manter catálogo de serviços
Como dono da oficina, quero manter uma lista de serviços com preço de referência para padronizar os orçamentos.

Critérios de aceite:
- Cada serviço tem nome, categoria (MOTOR, FREIO, SUSPENSAO, ELETRICA, REVISAO, OUTROS) e preço de referência maior que zero.
- O preço de referência é sugerido ao adicionar o serviço numa ordem, mas pode ser alterado na ordem.
- Um serviço já usado em alguma ordem não pode ser excluído, só desativado.

### HU-05 - Anexar fotos e documentos à ordem
Como mecânico, quero anexar fotos do veículo e o PDF do orçamento à ordem de serviço para ter registro do estado do carro.

Critérios de aceite:
- São aceitos JPG, PNG e PDF de até 10 MB.
- O arquivo é enviado direto do navegador para o S3 usando uma URL pré-assinada pedida ao backend.
- Depois do envio, o anexo aparece na lista da ordem com nome, tipo, tamanho e data.
- Para fotos, a lista mostra uma miniatura gerada automaticamente em até 1 minuto.

### HU-06 - Ver relatório de faturamento
Como dono da oficina, quero ver o faturamento por mês e os serviços mais realizados para entender o desempenho da oficina.

Critérios de aceite:
- O relatório de faturamento mostra, por mês, a quantidade de ordens concluídas e o valor total.
- O relatório de serviços mostra os 10 serviços mais realizados no período, com quantidade e receita.
- É possível filtrar por intervalo de datas.
- Só entram ordens com status CONCLUIDA.

## Como os requisitos se aplicam ao domínio

| ID | Aplicação no GiroCerto |
|----|------------------------|
| RF-01 | CRUD de Cliente, Veículo, Ordem de Serviço e Serviço. Relações: Cliente 1:N Veículo, Veículo 1:N Ordem de Serviço e Ordem de Serviço N:N Serviço (tabela item_ordem). Tudo persistido no RDS PostgreSQL. A entrega de 23/10 demonstra Cliente e Veículo; Serviço e Ordem (com itens) já estão na mesma Lambda. |
| RF-02 | Fotos e PDFs anexados à ordem de serviço. O backend gera a URL pré-assinada de PUT e o navegador envia direto para o bucket, no prefixo `uploads/ordens/{id}/`. |
| RF-03 | Cada arquivo novo em `uploads/` dispara uma Lambda que lê os metadados (tipo, tamanho, dimensões) e, se for imagem, gera uma miniatura em `thumbs/`. O resultado é gravado na tabela anexo no RDS. |
| RF-04 | `GET /relatorios/faturamento-mensal` e `GET /relatorios/servicos-mais-realizados` no API Gateway, implementados em Lambda com consultas usando JOIN e GROUP BY. |
| RF-05 | Front-end estático (HTML, CSS e JavaScript) publicado como site estático no S3, consumindo a API pelo endpoint do API Gateway. |
| RNF-01 | RDS em subnets privadas, sem IP público, aceitando conexão apenas do Security Group das Lambdas e do bastion. |
| RNF-02 | Credenciais do banco em variáveis de ambiente das Lambdas, configuradas pelo console. Arquivo `.env` no `.gitignore`. |
| RNF-03 | O front lê a URL da API de um `config.js` gerado no deploy. Nenhum IP no código; API Gateway e RDS usam nomes DNS. |
| RNF-04 | CRUD em Lambda + API Gateway. Justificativa no ADR-001 em `design.md`. |
| RNF-05 | Recursos criados pelo console e AWS CLI, com o passo a passo no README. |

## Fora do escopo

- Login e controle de permissões por perfil.
- Emissão de nota fiscal.
- Controle de estoque de peças.
- Agendamento de horários.
