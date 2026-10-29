# GiroCerto

Sistema de gestão para oficinas mecânicas. Projeto 2 de Computação em Nuvem, Mackenzie 2026.2, turma 5J11.

## Integrantes

| Nome | RA |
|------|----|
| Lucas Zeferino Baracat | 10396267 |
| Samuel Patto Marcondes Manfredini Ferreira | 32155549 |

## Onde está cada coisa

| Caminho | Conteúdo |
|---------|----------|
| `specs/spec.md` | Problema, personas, histórias e critérios de aceite |
| `specs/design.md` | Arquitetura, rede, Security Groups, modelo ER, rotas e ADRs |
| `specs/tasks.md` | Tarefas com requisito, responsável e status |
| `docs/ia-log.md` | Registro do uso do Copilot |
| `sql/01_schema.sql` | Criação das tabelas no RDS |
| `sql/02_seed.sql` | Dados de exemplo |
| `backend/crud/app.py` | Lambda `girocerto-crud`: CRUD e URLs pré-assinadas dos anexos (RF-01, RF-02) |
| `backend/processa_anexo/app.py` | Lambda `girocerto-processa-anexo`: miniatura e metadados de cada arquivo novo no S3 (RF-03) |
| `backend/relatorios/app.py` | Lambda `girocerto-relatorios`: faturamento mensal e serviços mais realizados (RF-04) |
| `backend/comum/banco.py` | Conexão com o RDS usada pelas Lambdas `relatorios` e `processa-anexo` |
| `scripts/empacotar.sh` | Gera o `.zip` de cada Lambda |
| `scripts/testar-api.sh` | Percorre o CRUD de clientes e veículos com `curl` |
| `scripts/servidor_local.py` | Simula API Gateway e S3 para testar na máquina |
| `web/index.html` | Landing page |
| `web/app.html` | Sistema: clientes, veículos, serviços, ordens com anexos e relatórios (RF-05) |

## Como usar este README

| Quero... | Vá para |
|----------|---------|
| Testar o sistema no meu computador, sem AWS | [Rodar localmente no macOS](#rodar-localmente-no-macos) ou [no Windows](#rodar-localmente-no-windows) |
| Publicar o sistema na AWS Learner Lab | [Publicar na AWS](#publicar-na-aws) |
| Voltar a usar a AWS numa sessão nova do Lab | [Ao iniciar uma nova sessão do Learner Lab](#ao-iniciar-uma-nova-sessão-do-learner-lab) |

## Rodar localmente

Roda o sistema inteiro na sua máquina: um PostgreSQL local faz o papel do RDS, e o `scripts/servidor_local.py` faz o papel do API Gateway, da Lambda e do S3. Serve para testar antes de publicar; a entrega precisa do sistema rodando na AWS.

Você vai precisar de **Git**, **Python 3** e **PostgreSQL 16 ou 17**. Os passos abaixo instalam tudo.

### Rodar localmente no macOS

Use o app **Terminal**. Rode um bloco por vez.

**1. Instalar as dependências (só na primeira vez).** Se você ainda não tem o Homebrew, instale antes pelo comando em [brew.sh](https://brew.sh).

```bash
brew install git python postgresql@17
brew services start postgresql@17
```

**2. Baixar o projeto (só na primeira vez).**

```bash
cd ~/Documents
git clone https://github.com/samuelpattomack/GiroCerto.git
cd GiroCerto
```

**3. Instalar a biblioteca do banco num ambiente virtual (só na primeira vez).**

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/crud/requirements.txt
```

**4. Criar o banco com as tabelas e os dados de exemplo.** No macOS o usuário do banco é o seu usuário do sistema, sem senha. Rodar o `psql` de novo apaga e recria os dados.

```bash
createdb girocerto
psql -d girocerto -f sql/01_schema.sql -f sql/02_seed.sql
```

**5. Subir o sistema.**

```bash
DB_HOST=127.0.0.1 DB_USER=$(whoami) DB_PASSWORD=local DB_SSL=off .venv/bin/python scripts/servidor_local.py
```

Quando aparecer `GiroCerto local em http://localhost:8765/app.html`, abra esse endereço no navegador. O terminal fica ocupado enquanto o servidor roda; para parar, `Ctrl+C`.

**Nas próximas vezes**, basta entrar na pasta e repetir o passo 5:

```bash
cd ~/Documents/GiroCerto
DB_HOST=127.0.0.1 DB_USER=$(whoami) DB_PASSWORD=local DB_SSL=off .venv/bin/python scripts/servidor_local.py
```

### Rodar localmente no Windows

Use o **PowerShell** (menu Iniciar > digite "PowerShell"). Rode um bloco por vez.

**1. Instalar as dependências (só na primeira vez).** O instalador do PostgreSQL vai abrir: escolha uma senha para o usuário `postgres` e **anote**, ela é usada nos próximos passos. Pode aceitar o resto como está.

```powershell
winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements
winget install -e --id Python.Python.3.12 --accept-package-agreements
winget install -e --id PostgreSQL.PostgreSQL.17 --accept-package-agreements --interactive
```

**2. Colocar o PostgreSQL no PATH (só na primeira vez).** O instalador não faz isso sozinho.

```powershell
$pg = "C:\Program Files\PostgreSQL\17\bin"; $u = [Environment]::GetEnvironmentVariable("Path","User"); if ($u -notlike "*$pg*") { [Environment]::SetEnvironmentVariable("Path", "$u;$pg", "User") }
```

**Feche e abra o PowerShell de novo**, para ele enxergar os programas instalados. Para conferir, cada comando abaixo deve mostrar uma versão:

```powershell
git --version; py --version; psql --version
```

**3. Baixar o projeto (só na primeira vez).**

```powershell
cd $HOME\Documents
git clone https://github.com/samuelpattomack/GiroCerto.git
cd GiroCerto
```

**4. Instalar a biblioteca do banco num ambiente virtual (só na primeira vez).**

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r backend\crud\requirements.txt
```

**5. Criar o banco com as tabelas e os dados de exemplo.** Os comandos pedem a senha do `postgres` escolhida no passo 1. A primeira linha evita que os acentos fiquem quebrados. Rodar o `psql` de novo apaga e recria os dados.

```powershell
$env:PGCLIENTENCODING = "UTF8"
createdb -U postgres girocerto
psql -U postgres -d girocerto -f sql/01_schema.sql -f sql/02_seed.sql
```

**6. Subir o sistema.** Troque `<senha>` pela senha do `postgres`.

```powershell
$env:DB_HOST = "127.0.0.1"; $env:DB_USER = "postgres"; $env:DB_PASSWORD = "<senha>"; $env:DB_SSL = "off"
.venv\Scripts\python scripts\servidor_local.py
```

Quando aparecer `GiroCerto local em http://localhost:8765/app.html`, abra esse endereço no navegador. O PowerShell fica ocupado enquanto o servidor roda; para parar, `Ctrl+C`.

**Nas próximas vezes**, basta entrar na pasta e repetir o passo 6 (as variáveis valem só para a janela aberta):

```powershell
cd $HOME\Documents\GiroCerto
$env:DB_HOST = "127.0.0.1"; $env:DB_USER = "postgres"; $env:DB_PASSWORD = "<senha>"; $env:DB_SSL = "off"
.venv\Scripts\python scripts\servidor_local.py
```

### O que testar

Em `http://localhost:8765/app.html`:

1. Crie um cliente, clique em **Editar**, mude o e-mail e salve. Um aviso aparece no canto da tela e a linha fica destacada.
2. Na aba **Veículos**, cadastre um veículo para esse cliente (placa no formato `ABC1234` ou `ABC1D23`).
3. Tente excluir o cliente: o sistema bloqueia, porque ele tem veículo.
4. Exclua o veículo e depois o cliente.
5. Em **Serviços**, desative um serviço. Em **Ordens**, abra uma ordem, adicione serviços e mude o status para **Concluída**: a ordem deixa de aceitar alterações.
6. Em **Relatórios**, veja o faturamento por mês e os serviços mais realizados.

O envio de fotos e PDFs precisa do S3 de verdade e só funciona na AWS (passo 10). Localmente, a tela mostra "Upload de anexos não configurado".

A landing page fica em `http://localhost:8765/index.html`. Para testar a API pelo terminal (macOS, ou Git Bash no Windows), com o servidor rodando em outra janela: `./scripts/testar-api.sh http://localhost:8765/api`.

### Problemas comuns

| Mensagem ou sintoma | Solução |
|---------------------|---------|
| `command not found` / `não é reconhecido como nome de cmdlet` | O programa não foi instalado ou o terminal não foi reaberto depois da instalação. No Windows, confira o passo 2. |
| `createdb: database "girocerto" already exists` | O banco já existe. Pode seguir para o `psql`. |
| `password authentication failed for user "postgres"` | Senha errada. Use a mesma escolhida na instalação do PostgreSQL. |
| `connection refused` ao criar o banco ou subir o servidor | O PostgreSQL não está rodando. macOS: `brew services start postgresql@17`. Windows: abra **Serviços** e inicie `postgresql-x64-17`. |
| `Address already in use` / porta 8765 ocupada | Já tem um servidor aberto em outra janela. Feche-o com `Ctrl+C` ou use outra porta: `PORTA=8766` (macOS) ou `$env:PORTA = "8766"` (Windows) antes do comando. |
| A página abre, mas mostra "Não foi possível falar com a API" | Confira a mensagem de erro no terminal do servidor. Normalmente é usuário ou senha do banco errados no comando de subir o sistema. |
| Mudei algo em `web/` e a página não mudou | Recarregue sem cache: `Cmd+Shift+R` (macOS) ou `Ctrl+Shift+R` (Windows). Se mudou o `app.py`, reinicie o servidor. |
| "Upload de anexos não configurado" | Esperado no teste local. O upload só funciona na AWS (passo 10). |
| Acentos quebrados nos dados (Windows) | Faltou `$env:PGCLIENTENCODING = "UTF8"`. Rode de novo o passo 5 inteiro. |

## Publicar na AWS

### Visão geral da infraestrutura

```
Navegador ──> S3 girocerto-web-5j11 (site estático: index.html, app.html)
    │
    ├──> API Gateway (REST, stage prod)
    │       ├── /{proxy+}             ──> Lambda girocerto-crud ───────┐
    │       └── /relatorios/{proxy+}  ──> Lambda girocerto-relatorios ─┼──> RDS PostgreSQL
    │                                     (subnets privadas)          │    (subnets privadas)
    └──PUT (URL pré-assinada)──> S3 girocerto-anexos-5j11 (privado)   │
                                    │ evento ObjectCreated uploads/   │
                                    └──> Lambda girocerto-processa-anexo ──┘
                                         (lê o original e grava thumbs/ pelo Gateway Endpoint)
EC2 bastion (subnet pública) ──5432──> RDS   (só para rodar os scripts SQL)
```

Detalhes e justificativas em `specs/design.md`. Todos os recursos são criados pelo console ou pela CLI (sem CloudFormation/Terraform/SAM). Os nomes abaixo são os usados pelo grupo; se mudar algum, mantenha o mesmo nas etapas seguintes.

Região: **us-east-1**.

Nenhuma senha fica no repositório. A senha do banco é definida no passo 4 e informada só no console (variável de ambiente da Lambda) e no terminal do bastion.


### 1. VPC e subnets

Console: **VPC > Your VPCs > Create VPC > VPC only**.

| Campo | Valor |
|-------|-------|
| Name | `girocerto-vpc` |
| IPv4 CIDR | `10.0.0.0/16` |

Depois, em **VPC > Subnets > Create subnet**, na `girocerto-vpc`:

| Nome | AZ | CIDR |
|------|----|------|
| `subnet-publica-a` | us-east-1a | `10.0.1.0/24` |
| `subnet-privada-a` | us-east-1a | `10.0.11.0/24` |
| `subnet-privada-b` | us-east-1b | `10.0.12.0/24` |

Na `subnet-publica-a`: **Actions > Edit subnet settings > Enable auto-assign public IPv4 address**.

### 2. Internet Gateway e tabelas de rota

1. **Internet gateways > Create**: `girocerto-igw`. Depois **Actions > Attach to VPC > girocerto-vpc**.
2. **Route tables > Create**: `rt-publica` na `girocerto-vpc`.
   - Routes > Edit routes > Add route: `0.0.0.0/0` → Internet Gateway `girocerto-igw`.
   - Subnet associations > `subnet-publica-a`.
3. **Route tables > Create**: `rt-privada` na `girocerto-vpc`.
   - Sem rota para a internet (fica só a rota `local`).
   - Subnet associations > `subnet-privada-a` e `subnet-privada-b`.
4. **Endpoints > Create endpoint** (necessário a partir do RF-03, mas pode ser criado agora; é gratuito):
   - Service: `com.amazonaws.us-east-1.s3`, tipo **Gateway**.
   - VPC `girocerto-vpc`, route table `rt-privada`.

Não criar NAT Gateway.

### 3. Security Groups

**EC2 > Security Groups > Create security group**, todos na `girocerto-vpc`. Crie os três vazios primeiro e depois edite as regras, porque um referencia o outro.

| SG | Entrada | Saída |
|----|---------|-------|
| `sg-lambda` | nenhuma | PostgreSQL 5432 → `sg-rds`; HTTPS 443 → prefix list `com.amazonaws.us-east-1.s3` |
| `sg-rds` | PostgreSQL 5432 ← `sg-lambda`; PostgreSQL 5432 ← `sg-bastion` | remover a regra padrão (não precisa de saída) |
| `sg-bastion` | SSH 22 ← **My IP** (ajustar a cada sessão) | PostgreSQL 5432 → `sg-rds`; HTTPS 443 e HTTP 80 → `0.0.0.0/0` (instalar o `psql`) |

### 4. RDS PostgreSQL

1. **RDS > Subnet groups > Create DB subnet group**: `girocerto-db-subnets`, VPC `girocerto-vpc`, subnets `subnet-privada-a` e `subnet-privada-b`.
2. **RDS > Databases > Create database > Standard create**:

| Campo | Valor |
|-------|-------|
| Engine | PostgreSQL 16 |
| Template | Free tier (ou Dev/Test) |
| DB instance identifier | `girocerto-db` |
| Master username | `girocerto_admin` |
| Credentials management | Self managed; definir uma senha forte e guardar fora do repositório |
| Instance class | `db.t3.micro` |
| Storage | 20 GB gp3, sem autoscaling |
| VPC | `girocerto-vpc` |
| DB subnet group | `girocerto-db-subnets` |
| **Public access** | **No** |
| VPC security group | só `sg-rds` (remover o `default`) |
| Additional configuration > Initial database name | `girocerto` |
| Backup retention | 1 dia; Performance Insights e Enhanced monitoring desligados |

Quando ficar **Available**, copie o **Endpoint** (aba Connectivity & security). Ele é um nome DNS e não muda entre sessões.

### 5. Bastion e scripts SQL

1. **EC2 > Launch instance**:
   - Nome `girocerto-bastion`, Amazon Linux 2023, `t3.micro`.
   - Key pair: `vockey` (a chave `labsuser.pem` fica em **AWS Details** no Learner Lab).
   - Network: `girocerto-vpc`, `subnet-publica-a`, auto-assign public IP habilitado, SG `sg-bastion`.
   - Advanced details > IAM instance profile: `LabInstanceProfile`.
2. Copie os scripts e entre na instância (troque `<ip-bastion>` pelo IP público atual):

   **macOS / Linux:**

```bash
chmod 400 labsuser.pem
scp -i labsuser.pem sql/*.sql ec2-user@<ip-bastion>:~
ssh -i labsuser.pem ec2-user@<ip-bastion>
```

   **Windows (PowerShell, OpenSSH já vem no Windows 10/11).** O `icacls` faz o papel do `chmod 400`; sem ele o `ssh` recusa a chave:

```powershell
icacls labsuser.pem /inheritance:r /grant:r "$($env:USERNAME):R"
scp -i labsuser.pem sql/01_schema.sql sql/02_seed.sql ec2-user@<ip-bastion>:~
ssh -i labsuser.pem ec2-user@<ip-bastion>
```

3. No bastion:

```bash
sudo dnf install -y postgresql16
export PGHOST=<endpoint-rds> PGUSER=girocerto_admin PGDATABASE=girocerto PGSSLMODE=require
psql -v ON_ERROR_STOP=1 -f 01_schema.sql
psql -v ON_ERROR_STOP=1 -f 02_seed.sql
psql -c '\dt'
```

O `psql` pede a senha definida no passo 4. O `01_schema.sql` apaga e recria as tabelas, então rodá-lo de novo zera os dados.

### 6. Lambda `girocerto-crud`

1. Gere os pacotes das três Lambdas. O script instala as dependências para Linux/Python 3.12 (`pg8000` e, na `processa_anexo`, `Pillow`), copia o código, baixa o certificado do RDS (`global-bundle.pem`) e gera `build/crud.zip`, `build/relatorios.zip` e `build/processa_anexo.zip`. Esses arquivos não vão para o Git. Para gerar só um: `./scripts/empacotar.sh crud`.

   **macOS / Linux** (precisa de Python 3 com `pip3`, `curl` e `zip`):

```bash
./scripts/empacotar.sh
```

   **Windows:** o script é bash e o Git Bash não traz o `zip`. Rode no **AWS CloudShell** (ícone `>_` no topo do console), que é Linux e já tem tudo:

```bash
git clone https://github.com/samuelpattomack/GiroCerto.git
cd GiroCerto
./scripts/empacotar.sh
```

   Depois, no CloudShell, **Actions > Download file** com o caminho `GiroCerto/build/crud.zip` (e os outros dois `.zip`). Também é possível enviar o zip direto para a Lambda pelo próprio CloudShell, depois de criá-la no passo 2:

```bash
aws lambda update-function-code --function-name girocerto-crud --zip-file fileb://build/crud.zip
```

2. **Lambda > Create function > Author from scratch**:

| Campo | Valor |
|-------|-------|
| Name | `girocerto-crud` |
| Runtime | Python 3.12, x86_64 |
| Execution role | Use an existing role > `LabRole` |
| Advanced settings > Enable VPC | `girocerto-vpc`, subnets `subnet-privada-a` e `subnet-privada-b`, SG `sg-lambda` |

3. **Code > Upload from > .zip file** > `build/crud.zip`. Em **Runtime settings**, o handler é `app.handler`.
4. **Configuration > General configuration**: memória 256 MB, timeout 15 s.
5. **Configuration > Environment variables**:

| Chave | Valor |
|-------|-------|
| `DB_HOST` | endpoint do RDS |
| `DB_NAME` | `girocerto` |
| `DB_USER` | `girocerto_admin` |
| `DB_PASSWORD` | senha do passo 4 |
| `ANEXOS_BUCKET` | `girocerto-anexos-5j11` (bucket do passo 10; pode ser adicionada depois) |

6. Teste em **Test** com o evento abaixo; deve voltar `statusCode: 200` e a lista de clientes:

```json
{ "httpMethod": "GET", "path": "/clientes", "pathParameters": { "proxy": "clientes" } }
```

Os logs ficam em **CloudWatch > Log groups > /aws/lambda/girocerto-crud**.

### 7. API Gateway

1. **API Gateway > Create API > REST API > Build**: nome `girocerto-api`, endpoint Regional.
2. **Create resource**: marque **Proxy resource**, resource path `/`, resource name `{proxy+}`. Não marque CORS (a própria Lambda responde o `OPTIONS` e envia os cabeçalhos CORS).
3. No método **ANY** do `/{proxy+}`: integração **Lambda function**, **Lambda proxy integration** ligado, função `girocerto-crud`.
4. **Deploy API** > New stage `prod`.
5. Copie o **Invoke URL**, algo como `https://abc123.execute-api.us-east-1.amazonaws.com/prod`. Essa URL não muda entre sessões.

Teste:

```bash
curl https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/clientes
```

```bash
./scripts/testar-api.sh https://<api-id>.execute-api.us-east-1.amazonaws.com/prod
```

O script cria um cliente e um veículo, consulta, atualiza, tenta excluir o cliente com veículo (deve dar 409) e depois exclui os dois. No Windows, rode-o no CloudShell ou no Git Bash. O `curl` simples funciona também no PowerShell (`curl.exe ...`).

Rotas disponíveis: ver tabela em `specs/design.md`.

### 8. Front-end no S3

1. Bucket e hospedagem (só na primeira vez):

```bash
aws s3 mb s3://girocerto-web-5j11 --region us-east-1
aws s3api put-public-access-block --bucket girocerto-web-5j11 \
  --public-access-block-configuration BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false
aws s3api put-bucket-policy --bucket girocerto-web-5j11 --policy '{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::girocerto-web-5j11/*"
  }]
}'
aws s3 website s3://girocerto-web-5j11 --index-document index.html
```

2. Gere o `config.js` com a URL da API e publique (repita sempre que mudar algo em `web/`):

   **macOS / Linux / CloudShell:**

```bash
API_URL=https://<api-id>.execute-api.us-east-1.amazonaws.com/prod
echo "window.GIROCERTO_CONFIG = { apiUrl: \"$API_URL\" };" > web/config.js
aws s3 sync web/ s3://girocerto-web-5j11 --exclude config.example.js
```

   **Windows (PowerShell):**

```powershell
$API_URL = "https://<api-id>.execute-api.us-east-1.amazonaws.com/prod"
"window.GIROCERTO_CONFIG = { apiUrl: `"$API_URL`" };" | Set-Content -Encoding utf8 web/config.js
aws s3 sync web/ s3://girocerto-web-5j11 --exclude config.example.js
```

3. Acesse `http://girocerto-web-5j11.s3-website-us-east-1.amazonaws.com` (landing) e `.../app.html` (sistema).

Sem AWS CLI na máquina, os mesmos comandos funcionam no **CloudShell** do console, ou pelo console: S3 > Create bucket > desmarcar "Block all public access" > Permissions > Bucket policy > Properties > Static website hosting > Enable > Upload da pasta `web/` (com o `config.js` gerado).


### 9. Lambda `girocerto-relatorios` (RF-04)

1. **Lambda > Create function**, igual ao passo 6.2, com nome `girocerto-relatorios` (Python 3.12, `LabRole`, VPC `girocerto-vpc`, subnets privadas, `sg-lambda`).
2. **Code > Upload from > .zip file** > `build/relatorios.zip`. Handler `app.handler`. Memória 256 MB, timeout 15 s.
3. **Environment variables**: as mesmas `DB_HOST`, `DB_NAME`, `DB_USER` e `DB_PASSWORD` da `girocerto-crud`.
4. Teste com o evento:

```json
{ "httpMethod": "GET", "path": "/relatorios/faturamento-mensal", "pathParameters": { "proxy": "faturamento-mensal" }, "queryStringParameters": { "inicio": "2026-01-01", "fim": "2026-12-31" } }
```

5. No **API Gateway** `girocerto-api`:
   - Selecione o recurso `/` > **Create resource** > Resource name `relatorios` (sem proxy) > Create.
   - Selecione `/relatorios` > **Create resource** > ligue **Proxy resource** > Resource name `{proxy+}` > Create.
   - No **ANY** de `/relatorios/{proxy+}`: Lambda function, **Lambda proxy integration** ligado, função `girocerto-relatorios`.
   - **Deploy API** > stage `prod` (o existente).

   O API Gateway escolhe sempre o caminho mais específico, então `/relatorios/...` vai para a `girocerto-relatorios` e o resto continua na `girocerto-crud`.

6. Teste:

```bash
curl "https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/relatorios/faturamento-mensal?inicio=2026-01-01&fim=2026-12-31"
curl "https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/relatorios/servicos-mais-realizados"
```

Sem `inicio` e `fim`, os relatórios usam os últimos 12 meses.

### 10. Anexos: bucket, CORS, Lambda `girocerto-processa-anexo` e evento (RF-02, RF-03)

**10.1 Bucket privado com CORS.** No CloudShell (ou terminal com AWS CLI):

```bash
aws s3 mb s3://girocerto-anexos-5j11 --region us-east-1
aws s3api put-bucket-cors --bucket girocerto-anexos-5j11 --cors-configuration '{
  "CORSRules": [{
    "AllowedOrigins": ["http://girocerto-web-5j11.s3-website-us-east-1.amazonaws.com"],
    "AllowedMethods": ["PUT", "GET"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3000
  }]
}'
```

O bucket fica com o bloqueio de acesso público ligado (padrão). O navegador envia e lê os arquivos só por URLs pré-assinadas, geradas pela `girocerto-crud`.

Pelo console: S3 > Create bucket `girocerto-anexos-5j11` (deixe "Block all public access" marcado) > Permissions > **Cross-origin resource sharing (CORS)** > Edit > cole só o conteúdo de `CORSRules` como uma lista JSON.

**10.2 Lambda.** **Lambda > Create function**, igual ao passo 6.2, com nome `girocerto-processa-anexo` (Python 3.12, `LabRole`, VPC, subnets privadas, `sg-lambda`).

- **Code > Upload from > .zip file** > `build/processa_anexo.zip`. Handler `app.handler`.
- **General configuration**: memória **512 MB**, timeout **30 s** (gerar miniatura de foto grande usa mais memória).
- **Environment variables**: `DB_HOST`, `DB_NAME`, `DB_USER` e `DB_PASSWORD`, iguais às da `girocerto-crud`.

Ela acessa o S3 pelo Gateway Endpoint do passo 2.4 (sem NAT). Sem esse endpoint, ou sem a saída 443 do `sg-lambda` para a prefix list do S3, a Lambda dá timeout ao ler o arquivo.

**10.3 Evento.** S3 > `girocerto-anexos-5j11` > **Properties** > **Event notifications** > **Create event notification**:

| Campo | Valor |
|-------|-------|
| Event name | `processa-anexo` |
| Prefix | `uploads/` |
| Event types | **All object create events** |
| Destination | Lambda function > `girocerto-processa-anexo` |

O prefixo `uploads/` é obrigatório: a Lambda grava as miniaturas em `thumbs/`, e sem o filtro ela dispararia a si mesma.

**10.4 Ligar a `girocerto-crud` ao bucket.** Na `girocerto-crud`, envie o `build/crud.zip` novo (passo 6.3) e confira a variável `ANEXOS_BUCKET` = `girocerto-anexos-5j11`.

### 11. Publicar a versão nova do site e testar

Repita o passo 8.2 (gerar o `config.js` e `aws s3 sync`). Depois, em `.../app.html`:

1. **Ordens** > abra uma ordem > em "Fotos e documentos" envie um JPG ou PNG.
2. O anexo aparece como **Processando** e, em poucos segundos, mostra a miniatura e fica **Processado**.
3. Em **CloudWatch > Log groups > /aws/lambda/girocerto-processa-anexo**, o log mostra o arquivo, as dimensões e `situacao = PROCESSADO`.
4. No bastion: `psql -c "SELECT id, nome_original, tamanho_bytes, largura, altura, situacao FROM anexo ORDER BY id DESC LIMIT 5;"`
5. **Relatórios** mostra o faturamento por mês e os serviços mais realizados. Conclua uma ordem com serviços e clique em **Atualizar** para ver o número mudar.

## Ao iniciar uma nova sessão do Learner Lab

Os recursos continuam existindo; só o que é cobrado por hora é parado quando a sessão termina.

1. **RDS**: se estiver `Stopped`, **Actions > Start** e esperar `Available`. O endpoint não muda.
2. **API Gateway, Lambdas e S3**: nada a fazer. A URL da API, o `config.js` e o evento do bucket de anexos continuam válidos.
3. **Bastion** (só se precisar rodar SQL): **Instance state > Start**, pegar o **novo IP público** e atualizar a regra SSH do `sg-bastion` para **My IP**.

Nenhum IP está no código: o front usa a URL do API Gateway e a Lambda usa o endpoint DNS do RDS.
