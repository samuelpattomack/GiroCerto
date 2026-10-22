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
| `backend/crud/app.py` | Lambda `girocerto-crud` (RF-01) |
| `scripts/empacotar-crud.sh` | Gera o `.zip` da Lambda |
| `scripts/testar-api.sh` | Percorre o CRUD de clientes e veículos com `curl` |
| `scripts/servidor_local.py` | Simula API Gateway e S3 para testar na máquina |
| `web/index.html` | Landing page |
| `web/app.html` | Tela de cadastro de clientes e veículos |

## Visão geral da infraestrutura

```
Navegador ──> S3 (site estático: index.html, app.html)
    │
    └──> API Gateway (REST, stage prod) ──> Lambda girocerto-crud ──> RDS PostgreSQL
                                             (subnets privadas)        (subnets privadas)
EC2 bastion (subnet pública) ──5432──> RDS   (só para rodar os scripts SQL)
```

Detalhes e justificativas em `specs/design.md`. Todos os recursos são criados pelo console ou pela CLI (sem CloudFormation/Terraform/SAM). Os nomes abaixo são os usados pelo grupo; se mudar algum, mantenha o mesmo nas etapas seguintes.

Região: **us-east-1**.

Nenhuma senha fica no repositório. A senha do banco é definida no passo 4 e informada só no console (variável de ambiente da Lambda) e no terminal do bastion.

---

## 1. VPC e subnets

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

## 2. Internet Gateway e tabelas de rota

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

## 3. Security Groups

**EC2 > Security Groups > Create security group**, todos na `girocerto-vpc`. Crie os três vazios primeiro e depois edite as regras, porque um referencia o outro.

| SG | Entrada | Saída |
|----|---------|-------|
| `sg-lambda` | nenhuma | PostgreSQL 5432 → `sg-rds`; HTTPS 443 → prefix list `com.amazonaws.us-east-1.s3` |
| `sg-rds` | PostgreSQL 5432 ← `sg-lambda`; PostgreSQL 5432 ← `sg-bastion` | remover a regra padrão (não precisa de saída) |
| `sg-bastion` | SSH 22 ← **My IP** (ajustar a cada sessão) | PostgreSQL 5432 → `sg-rds`; HTTPS 443 e HTTP 80 → `0.0.0.0/0` (instalar o `psql`) |

## 4. RDS PostgreSQL

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

## 5. Bastion e scripts SQL

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

## 6. Lambda `girocerto-crud`

1. Gere o pacote. O script instala o driver `pg8000` para Linux/Python 3.12, copia o `app.py`, baixa o certificado do RDS (`global-bundle.pem`) e gera `build/crud.zip`. Esses arquivos não vão para o Git.

   **macOS / Linux** (precisa de Python 3 com `pip3`, `curl` e `zip`):

```bash
./scripts/empacotar-crud.sh
```

   **Windows:** o script é bash e o Git Bash não traz o `zip`. Rode no **AWS CloudShell** (ícone `>_` no topo do console), que é Linux e já tem tudo:

```bash
git clone https://github.com/samuelpattomack/GiroCerto.git
cd GiroCerto
./scripts/empacotar-crud.sh
```

   Depois, no CloudShell, **Actions > Download file** com o caminho `GiroCerto/build/crud.zip`. Também é possível enviar o zip direto para a Lambda pelo próprio CloudShell, depois de criá-la no passo 2:

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

6. Teste em **Test** com o evento abaixo; deve voltar `statusCode: 200` e a lista de clientes:

```json
{ "httpMethod": "GET", "path": "/clientes", "pathParameters": { "proxy": "clientes" } }
```

Os logs ficam em **CloudWatch > Log groups > /aws/lambda/girocerto-crud**.

## 7. API Gateway

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

Rotas disponíveis: ver tabela em `specs/design.md`. Nesta entrega estão implementadas as de clientes, veículos, serviços, ordens e itens.

## 8. Front-end no S3

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

3. Acesse `http://girocerto-web-5j11.s3-website-us-east-1.amazonaws.com` (landing) e `.../app.html` (cadastros).

Sem AWS CLI na máquina, os mesmos comandos funcionam no **CloudShell** do console, ou pelo console: S3 > Create bucket > desmarcar "Block all public access" > Permissions > Bucket policy > Properties > Static website hosting > Enable > Upload da pasta `web/` (com o `config.js` gerado).

---

## Ao iniciar uma nova sessão do Learner Lab

Os recursos continuam existindo; só o que é cobrado por hora é parado quando a sessão termina.

1. **RDS**: se estiver `Stopped`, **Actions > Start** e esperar `Available`. O endpoint não muda.
2. **API Gateway, Lambda e S3**: nada a fazer. A URL da API e o `config.js` continuam válidos.
3. **Bastion** (só se precisar rodar SQL): **Instance state > Start**, pegar o **novo IP público** e atualizar a regra SSH do `sg-bastion` para **My IP**.

Nenhum IP está no código: o front usa a URL do API Gateway e a Lambda usa o endpoint DNS do RDS.

## Rodar localmente (opcional)

Para testar sem AWS, com um PostgreSQL e Python 3 na própria máquina. O `scripts/servidor_local.py` faz o papel do API Gateway e do S3. Rode os comandos na pasta raiz do repositório.

### macOS / Linux

PostgreSQL pelo Homebrew (`brew install postgresql@17` e `brew services start postgresql@17`) ou pelo gerenciador de pacotes. O usuário do banco é o do sistema, sem senha.

```bash
createdb girocerto
psql -d girocerto -f sql/01_schema.sql -f sql/02_seed.sql
pip3 install -r backend/crud/requirements.txt
DB_HOST=127.0.0.1 DB_USER=$(whoami) DB_PASSWORD=x DB_SSL=off python3 scripts/servidor_local.py
```

### Windows (PowerShell)

PostgreSQL pelo instalador oficial (postgresql.org). O usuário é `postgres`, com a senha escolhida na instalação. Se o terminal não achar `psql`/`createdb`, adicione `C:\Program Files\PostgreSQL\17\bin` ao PATH.

```powershell
$env:PGCLIENTENCODING = "UTF8"   # sem isso os acentos do seed ficam quebrados
createdb -U postgres girocerto
psql -U postgres -d girocerto -f sql/01_schema.sql -f sql/02_seed.sql
py -m pip install -r backend/crud/requirements.txt
$env:DB_HOST = "127.0.0.1"; $env:DB_USER = "postgres"; $env:DB_PASSWORD = "<senha-do-postgres>"; $env:DB_SSL = "off"
py scripts/servidor_local.py
```

### Depois de subir o servidor

Abra `http://localhost:8765/app.html`. Para parar, `Ctrl+C`. Depois de mudar algo em `web/` ou no `app.py`, reinicie o servidor e recarregue a página com `Ctrl+Shift+R` (Windows) ou `Cmd+Shift+R` (macOS).

Para testar a API pelo terminal (macOS, Linux ou Git Bash): `./scripts/testar-api.sh http://localhost:8765/api`.
