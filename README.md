# GiroCerto

Sistema de gestão para oficinas mecânicas. Projeto 2 de Computação em Nuvem, Mackenzie 2026.2, turma 5J11.

## Integrantes

| Nome | RA |
|------|----|
| Lucas Zeferino Baracat | 10396267 |
| Samuel Patto Marcondes Manfredini Ferreira | 32155549 |
|  |  |
|  |  |

## Onde está cada coisa

| Arquivo | Conteúdo |
|---------|----------|
| `specs/spec.md` | Problema, personas, histórias e critérios de aceite |
| `specs/design.md` | Arquitetura, rede, Security Groups, modelo ER, rotas e ADRs |
| `docs/ia-log.md` | Registro do uso do Copilot |
| `web/` | Landing page publicada no S3 |

## Publicar a landing page no S3

Pré-requisito: sessão do Learner Lab iniciada e AWS CLI configurada com as credenciais da sessão (AWS Details > AWS CLI).

1. Criar o bucket (o nome precisa ser único):

```bash
aws s3 mb s3://girocerto-web-5j11 --region us-east-1
```

2. Liberar acesso público ao bucket:

```bash
aws s3api put-public-access-block --bucket girocerto-web-5j11 \
  --public-access-block-configuration BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false
```

3. Aplicar a política de leitura pública:

```bash
aws s3api put-bucket-policy --bucket girocerto-web-5j11 --policy '{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::girocerto-web-5j11/*"
  }]
}'
```

4. Ativar hospedagem de site estático:

```bash
aws s3 website s3://girocerto-web-5j11 --index-document index.html
```

5. Enviar os arquivos:

```bash
aws s3 sync web/ s3://girocerto-web-5j11
```

6. Acessar em `http://girocerto-web-5j11.s3-website-us-east-1.amazonaws.com`

Pelo console o caminho é o mesmo: S3 > Create bucket > desmarcar "Block all public access" > Permissions > Bucket policy > Properties > Static website hosting > Enable > Upload da pasta `web/`.
