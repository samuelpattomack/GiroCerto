"""Lambda processa-anexo do GiroCerto (RF-03).

Disparada pelo evento ObjectCreated do bucket de anexos, só no prefixo
uploads/. Para cada arquivo novo: lê os metadados (tipo e tamanho), gera
uma miniatura de até 320 px em thumbs/ se for imagem e grava o resultado
na tabela anexo do RDS (situacao PROCESSADO ou ERRO).

Roda na VPC e fala com o S3 pelo Gateway Endpoint, sem NAT. A miniatura
vai para thumbs/, fora de uploads/, para não disparar a própria Lambda.
"""

import io
import urllib.parse

import boto3
from PIL import Image, UnidentifiedImageError

import banco

TAMANHO_MAXIMO = 10 * 1024 * 1024
LADO_MINIATURA = 320

s3 = boto3.client("s3")


def chave_miniatura(chave):
    # uploads/ordens/7/abc.png -> thumbs/ordens/7/abc.jpg
    caminho = chave[len("uploads/"):].rsplit(".", 1)[0]
    return f"thumbs/{caminho}.jpg"


def gerar_miniatura(bucket, chave):
    original = s3.get_object(Bucket=bucket, Key=chave)["Body"].read()
    with Image.open(io.BytesIO(original)) as img:
        largura, altura = img.size
        img.thumbnail((LADO_MINIATURA, LADO_MINIATURA))
        saida = io.BytesIO()
        img.convert("RGB").save(saida, "JPEG", quality=82)
    destino = chave_miniatura(chave)
    s3.put_object(Bucket=bucket, Key=destino, Body=saida.getvalue(), ContentType="image/jpeg")
    return largura, altura, destino


def processar(bucket, chave):
    anexo = banco.um("SELECT id, tipo FROM anexo WHERE chave_s3 = :chave", chave=chave)
    if anexo is None:
        print(f"Ignorado: {chave} não está registrado na tabela anexo")
        return

    meta = s3.head_object(Bucket=bucket, Key=chave)
    tamanho, tipo = meta["ContentLength"], meta.get("ContentType", "")
    print(f"Anexo {anexo['id']}: {chave} ({tipo}, {tamanho} bytes)")

    largura = altura = miniatura = None
    situacao = "PROCESSADO"
    if tamanho > TAMANHO_MAXIMO:
        print(f"Anexo {anexo['id']}: maior que 10 MB")
        situacao = "ERRO"
    elif tipo != anexo["tipo"]:
        print(f"Anexo {anexo['id']}: tipo enviado {tipo} difere do registrado {anexo['tipo']}")
        situacao = "ERRO"
    elif tipo.startswith("image/"):
        try:
            largura, altura, miniatura = gerar_miniatura(bucket, chave)
            print(f"Anexo {anexo['id']}: {largura}x{altura}, miniatura em {miniatura}")
        except (UnidentifiedImageError, OSError) as e:
            print(f"Anexo {anexo['id']}: imagem inválida: {e}")
            situacao = "ERRO"

    banco.sql(
        """UPDATE anexo SET tamanho_bytes = :tamanho, largura = :largura, altura = :altura,
                  chave_miniatura = :miniatura, situacao = :situacao
           WHERE id = :id""",
        id=anexo["id"], tamanho=tamanho, largura=largura, altura=altura,
        miniatura=miniatura, situacao=situacao,
    )
    print(f"Anexo {anexo['id']}: situacao = {situacao}")


def handler(event, context):
    for registro in event.get("Records", []):
        bucket = registro["s3"]["bucket"]["name"]
        # A chave vem codificada na notificação (espaço vira +)
        chave = urllib.parse.unquote_plus(registro["s3"]["object"]["key"])
        if not chave.startswith("uploads/"):
            continue
        try:
            processar(bucket, chave)
        except Exception:
            banco.descartar_conexao()
            raise
    return {"processados": len(event.get("Records", []))}
