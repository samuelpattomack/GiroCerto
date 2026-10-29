"""Lambda crud do GiroCerto (RF-01 e RF-02).

Recebe as requisições do API Gateway (REST, integração proxy em /{proxy+})
e roteia pelo método e caminho. Entidades: clientes, veiculos, servicos e
ordens (com itens e anexos). Conexão com o RDS configurada por variáveis de
ambiente: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD. Os anexos usam o
bucket da variável ANEXOS_BUCKET.
"""

import datetime
import decimal
import json
import os
import re
import ssl
import uuid

import pg8000.native
from pg8000.exceptions import DatabaseError, InterfaceError

CORS_HEADERS = {
    "Access-Control-Allow-Origin": os.environ.get("CORS_ORIGIN", "*"),
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

PLACA_RE = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CATEGORIAS = ("MOTOR", "FREIO", "SUSPENSAO", "ELETRICA", "REVISAO", "OUTROS")
STATUS = ("ABERTA", "EM_ANDAMENTO", "CONCLUIDA", "CANCELADA")
STATUS_FECHADOS = ("CONCLUIDA", "CANCELADA")

# Criada fora do handler para ser reaproveitada entre invocações (ADR-001)
_conn = None


class ErroApi(Exception):
    def __init__(self, status, mensagem):
        super().__init__(mensagem)
        self.status = status
        self.mensagem = mensagem


def _ssl_context():
    ca = os.path.join(os.path.dirname(__file__), "global-bundle.pem")
    if os.path.exists(ca):
        return ssl.create_default_context(cafile=ca)
    # Sem o bundle da AWS no pacote a conexão continua criptografada,
    # mas sem validar o certificado do servidor.
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def conexao():
    global _conn
    if _conn is None:
        _conn = pg8000.native.Connection(
            host=os.environ["DB_HOST"],
            port=int(os.environ.get("DB_PORT", "5432")),
            database=os.environ.get("DB_NAME", "girocerto"),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            ssl_context=None if os.environ.get("DB_SSL") == "off" else _ssl_context(),
            timeout=10,
        )
    return _conn


def camel(nome):
    partes = nome.split("_")
    return partes[0] + "".join(p.capitalize() for p in partes[1:])


def sql(query, **params):
    """Executa a query e devolve as linhas como dicts com chaves em camelCase."""
    conn = conexao()
    linhas = conn.run(query, **params)
    if not conn.columns:
        return []
    nomes = [camel(c["name"]) for c in conn.columns]
    return [dict(zip(nomes, linha)) for linha in linhas]


def um(query, **params):
    linhas = sql(query, **params)
    return linhas[0] if linhas else None


def para_json(valor):
    if isinstance(valor, decimal.Decimal):
        return float(valor)
    if isinstance(valor, (datetime.date, datetime.datetime)):
        return valor.isoformat()
    raise TypeError(f"tipo não serializável: {type(valor)}")


def resposta(status, corpo=None):
    return {
        "statusCode": status,
        "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
        "body": "" if corpo is None else json.dumps(corpo, default=para_json, ensure_ascii=False),
    }


# ---------- validação ----------

def texto(dados, campo, obrigatorio=True, maximo=200):
    valor = dados.get(campo)
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        if obrigatorio:
            raise ErroApi(400, f"O campo '{campo}' é obrigatório.")
        return None
    if not isinstance(valor, str):
        raise ErroApi(400, f"O campo '{campo}' deve ser texto.")
    valor = valor.strip()
    if len(valor) > maximo:
        raise ErroApi(400, f"O campo '{campo}' aceita no máximo {maximo} caracteres.")
    return valor


def inteiro(dados, campo, minimo=None, maximo=None, obrigatorio=True):
    valor = dados.get(campo)
    if valor is None or valor == "":
        if obrigatorio:
            raise ErroApi(400, f"O campo '{campo}' é obrigatório.")
        return None
    try:
        valor = int(valor)
    except (TypeError, ValueError):
        raise ErroApi(400, f"O campo '{campo}' deve ser um número inteiro.")
    if (minimo is not None and valor < minimo) or (maximo is not None and valor > maximo):
        raise ErroApi(400, f"O campo '{campo}' está fora do intervalo permitido.")
    return valor


def dinheiro(dados, campo, obrigatorio=True):
    valor = dados.get(campo)
    if valor is None or valor == "":
        if obrigatorio:
            raise ErroApi(400, f"O campo '{campo}' é obrigatório.")
        return None
    try:
        valor = decimal.Decimal(str(valor)).quantize(decimal.Decimal("0.01"))
    except decimal.InvalidOperation:
        raise ErroApi(400, f"O campo '{campo}' deve ser um valor numérico.")
    return valor


def data(dados, campo, obrigatorio=True):
    valor = dados.get(campo)
    if valor is None or valor == "":
        if obrigatorio:
            raise ErroApi(400, f"O campo '{campo}' é obrigatório.")
        return None
    if isinstance(valor, datetime.date):
        return valor
    try:
        return datetime.date.fromisoformat(str(valor))
    except ValueError:
        raise ErroApi(400, f"O campo '{campo}' deve estar no formato AAAA-MM-DD.")


def opcao(dados, campo, opcoes):
    valor = texto(dados, campo).upper()
    if valor not in opcoes:
        raise ErroApi(400, f"O campo '{campo}' deve ser um de: {', '.join(opcoes)}.")
    return valor


def buscar_ou_404(query, nome, **params):
    linha = um(query, **params)
    if linha is None:
        feminino = nome.startswith("Ordem")
        raise ErroApi(404, f"{nome} não encontrad{'a' if feminino else 'o'}.")
    return linha


# ---------- clientes (HU-01) ----------

def validar_cliente(d):
    telefone = re.sub(r"\D", "", texto(d, "telefone", maximo=30))
    if not 10 <= len(telefone) <= 13:
        raise ErroApi(400, "Telefone deve ter DDD e número (10 a 13 dígitos).")
    email = texto(d, "email", obrigatorio=False, maximo=160)
    if email and not EMAIL_RE.match(email):
        raise ErroApi(400, "E-mail em formato inválido.")
    return {"nome": texto(d, "nome", maximo=120), "telefone": telefone, "email": email}


def listar_clientes(q):
    busca = (q.get("busca") or "").strip()
    return 200, sql(
        """SELECT c.*, COUNT(v.id) AS total_veiculos
           FROM cliente c LEFT JOIN veiculo v ON v.cliente_id = c.id
           WHERE :busca = '' OR c.nome ILIKE '%' || :busca || '%' OR c.telefone LIKE '%' || :busca || '%'
           GROUP BY c.id ORDER BY c.nome""",
        busca=busca,
    )


def obter_cliente(id):
    cliente = buscar_ou_404("SELECT * FROM cliente WHERE id = :id", "Cliente", id=id)
    cliente["veiculos"] = sql("SELECT * FROM veiculo WHERE cliente_id = :id ORDER BY placa", id=id)
    return 200, cliente


def criar_cliente(d):
    c = validar_cliente(d)
    return 201, um(
        "INSERT INTO cliente (nome, telefone, email) VALUES (:nome, :telefone, :email) RETURNING *", **c
    )


def atualizar_cliente(id, d):
    atual = buscar_ou_404("SELECT * FROM cliente WHERE id = :id", "Cliente", id=id)
    c = validar_cliente({**atual, **d})
    return 200, um(
        "UPDATE cliente SET nome = :nome, telefone = :telefone, email = :email WHERE id = :id RETURNING *",
        id=id, **c,
    )


def excluir_cliente(id):
    buscar_ou_404("SELECT id FROM cliente WHERE id = :id", "Cliente", id=id)
    sql("DELETE FROM cliente WHERE id = :id", id=id)
    return 204, None


# ---------- veículos (HU-02) ----------

def validar_veiculo(d):
    placa = re.sub(r"[\s-]", "", texto(d, "placa", maximo=10)).upper()
    if not PLACA_RE.match(placa):
        raise ErroApi(400, "Placa inválida. Use o formato ABC1234 ou ABC1D23.")
    ano_max = datetime.date.today().year + 1
    return {
        "cliente_id": inteiro(d, "clienteId", minimo=1),
        "placa": placa,
        "marca": texto(d, "marca", maximo=60),
        "modelo": texto(d, "modelo", maximo=60),
        "ano": inteiro(d, "ano", minimo=1950, maximo=ano_max),
    }


def listar_veiculos(q):
    cliente_id = inteiro(q, "clienteId", minimo=1, obrigatorio=False)
    return 200, sql(
        """SELECT v.*, c.nome AS cliente_nome
           FROM veiculo v JOIN cliente c ON c.id = v.cliente_id
           WHERE CAST(:cliente_id AS INT) IS NULL OR v.cliente_id = :cliente_id
           ORDER BY v.placa""",
        cliente_id=cliente_id,
    )


def obter_veiculo(id):
    veiculo = buscar_ou_404(
        """SELECT v.*, c.nome AS cliente_nome FROM veiculo v
           JOIN cliente c ON c.id = v.cliente_id WHERE v.id = :id""",
        "Veículo", id=id,
    )
    veiculo["ordens"] = sql(
        "SELECT * FROM ordem_servico WHERE veiculo_id = :id ORDER BY data_entrada DESC, id DESC", id=id
    )
    return 200, veiculo


def criar_veiculo(d):
    v = validar_veiculo(d)
    return 201, um(
        """INSERT INTO veiculo (cliente_id, placa, marca, modelo, ano)
           VALUES (:cliente_id, :placa, :marca, :modelo, :ano) RETURNING *""",
        **v,
    )


def atualizar_veiculo(id, d):
    atual = buscar_ou_404("SELECT * FROM veiculo WHERE id = :id", "Veículo", id=id)
    v = validar_veiculo({**atual, **d})
    return 200, um(
        """UPDATE veiculo SET cliente_id = :cliente_id, placa = :placa, marca = :marca,
                  modelo = :modelo, ano = :ano
           WHERE id = :id RETURNING *""",
        id=id, **v,
    )


def excluir_veiculo(id):
    buscar_ou_404("SELECT id FROM veiculo WHERE id = :id", "Veículo", id=id)
    sql("DELETE FROM veiculo WHERE id = :id", id=id)
    return 204, None


# ---------- serviços (HU-04) ----------

def validar_servico(d):
    preco = dinheiro(d, "precoReferencia")
    if preco <= 0:
        raise ErroApi(400, "O preço de referência deve ser maior que zero.")
    ativo = d.get("ativo", True)
    if not isinstance(ativo, bool):
        raise ErroApi(400, "O campo 'ativo' deve ser true ou false.")
    return {
        "nome": texto(d, "nome", maximo=120),
        "categoria": opcao(d, "categoria", CATEGORIAS),
        "preco_referencia": preco,
        "ativo": ativo,
    }


def listar_servicos(q):
    so_ativos = q.get("ativos") == "true"
    return 200, sql(
        "SELECT * FROM servico WHERE NOT :so_ativos OR ativo ORDER BY categoria, nome",
        so_ativos=so_ativos,
    )


def criar_servico(d):
    s = validar_servico(d)
    return 201, um(
        """INSERT INTO servico (nome, categoria, preco_referencia, ativo)
           VALUES (:nome, :categoria, :preco_referencia, :ativo) RETURNING *""",
        **s,
    )


def atualizar_servico(id, d):
    atual = buscar_ou_404("SELECT * FROM servico WHERE id = :id", "Serviço", id=id)
    s = validar_servico({**atual, **d})
    return 200, um(
        """UPDATE servico SET nome = :nome, categoria = :categoria,
                  preco_referencia = :preco_referencia, ativo = :ativo
           WHERE id = :id RETURNING *""",
        id=id, **s,
    )


def excluir_servico(id):
    buscar_ou_404("SELECT id FROM servico WHERE id = :id", "Serviço", id=id)
    sql("DELETE FROM servico WHERE id = :id", id=id)
    return 204, None


# ---------- ordens de serviço (HU-03) ----------

def validar_ordem(d):
    return {
        "veiculo_id": inteiro(d, "veiculoId", minimo=1),
        "data_entrada": data(d, "dataEntrada", obrigatorio=False) or datetime.date.today(),
        "quilometragem": inteiro(d, "quilometragem", minimo=0),
        "descricao": texto(d, "descricao", maximo=2000),
        "status": opcao({"status": d.get("status") or "ABERTA"}, "status", STATUS),
    }


def listar_ordens(q):
    status = (q.get("status") or "").upper()
    if status and status not in STATUS:
        raise ErroApi(400, f"Status deve ser um de: {', '.join(STATUS)}.")
    veiculo_id = inteiro(q, "veiculoId", minimo=1, obrigatorio=False)
    return 200, sql(
        """SELECT o.*, v.placa, v.modelo, c.nome AS cliente_nome,
                  COALESCE(SUM(i.quantidade * i.valor_unitario), 0) AS total
           FROM ordem_servico o
           JOIN veiculo v ON v.id = o.veiculo_id
           JOIN cliente c ON c.id = v.cliente_id
           LEFT JOIN item_ordem i ON i.ordem_id = o.id
           WHERE (:status = '' OR o.status = :status)
             AND (CAST(:veiculo_id AS INT) IS NULL OR o.veiculo_id = :veiculo_id)
           GROUP BY o.id, v.id, c.id
           ORDER BY o.data_entrada DESC, o.id DESC""",
        status=status, veiculo_id=veiculo_id,
    )


def obter_ordem(id):
    ordem = buscar_ou_404(
        """SELECT o.*, v.placa, v.marca, v.modelo, c.id AS cliente_id, c.nome AS cliente_nome
           FROM ordem_servico o
           JOIN veiculo v ON v.id = o.veiculo_id
           JOIN cliente c ON c.id = v.cliente_id
           WHERE o.id = :id""",
        "Ordem de serviço", id=id,
    )
    ordem["itens"] = sql(
        """SELECT i.servico_id, s.nome, s.categoria, i.quantidade, i.valor_unitario,
                  i.quantidade * i.valor_unitario AS subtotal
           FROM item_ordem i JOIN servico s ON s.id = i.servico_id
           WHERE i.ordem_id = :id ORDER BY s.nome""",
        id=id,
    )
    ordem["total"] = sum((i["subtotal"] for i in ordem["itens"]), decimal.Decimal("0"))
    ordem["anexos"] = sql("SELECT * FROM anexo WHERE ordem_id = :id ORDER BY enviado_em", id=id)
    return 200, ordem


def criar_ordem(d):
    o = validar_ordem(d)
    if o["status"] in STATUS_FECHADOS:
        raise ErroApi(400, "Uma ordem nova deve começar como ABERTA ou EM_ANDAMENTO.")
    buscar_ou_404("SELECT id FROM veiculo WHERE id = :id", "Veículo", id=o["veiculo_id"])
    return 201, um(
        """INSERT INTO ordem_servico (veiculo_id, data_entrada, quilometragem, descricao, status)
           VALUES (:veiculo_id, :data_entrada, :quilometragem, :descricao, :status) RETURNING *""",
        **o,
    )


def ordem_editavel(id):
    ordem = buscar_ou_404("SELECT * FROM ordem_servico WHERE id = :id", "Ordem de serviço", id=id)
    if ordem["status"] in STATUS_FECHADOS:
        raise ErroApi(409, f"A ordem está {ordem['status']} e não aceita mais alterações.")
    return ordem


def atualizar_ordem(id, d):
    atual = ordem_editavel(id)
    o = validar_ordem({**atual, **d})
    # HU-03: ao concluir, a data de saída é preenchida automaticamente
    o["data_saida"] = datetime.date.today() if o["status"] == "CONCLUIDA" else None
    if o["data_saida"] and o["data_saida"] < o["data_entrada"]:
        raise ErroApi(400, "A data de entrada não pode ser posterior à data de conclusão.")
    return 200, um(
        """UPDATE ordem_servico SET veiculo_id = :veiculo_id, data_entrada = :data_entrada,
                  data_saida = :data_saida, quilometragem = :quilometragem,
                  descricao = :descricao, status = :status
           WHERE id = :id RETURNING *""",
        id=id, **o,
    )


def excluir_ordem(id):
    ordem = buscar_ou_404("SELECT status FROM ordem_servico WHERE id = :id", "Ordem de serviço", id=id)
    if ordem["status"] != "ABERTA":
        raise ErroApi(409, "Só é possível excluir ordens com status ABERTA.")
    sql("DELETE FROM ordem_servico WHERE id = :id", id=id)
    return 204, None


def adicionar_item(ordem_id, d):
    ordem_editavel(ordem_id)
    servico_id = inteiro(d, "servicoId", minimo=1)
    servico = buscar_ou_404("SELECT * FROM servico WHERE id = :id", "Serviço", id=servico_id)
    if not servico["ativo"]:
        raise ErroApi(409, "Este serviço está desativado.")
    quantidade = inteiro({"quantidade": d.get("quantidade", 1)}, "quantidade", minimo=1)
    # HU-04: o preço de referência é sugerido, mas pode ser alterado na ordem
    valor = dinheiro(d, "valorUnitario", obrigatorio=False)
    if valor is None:
        valor = servico["precoReferencia"]
    if valor < 0:
        raise ErroApi(400, "O valor unitário não pode ser negativo.")
    # Mesmo serviço duas vezes na ordem: soma a quantidade (chave composta)
    sql(
        """INSERT INTO item_ordem (ordem_id, servico_id, quantidade, valor_unitario)
           VALUES (:ordem_id, :servico_id, :quantidade, :valor)
           ON CONFLICT (ordem_id, servico_id)
           DO UPDATE SET quantidade = item_ordem.quantidade + EXCLUDED.quantidade,
                         valor_unitario = EXCLUDED.valor_unitario""",
        ordem_id=ordem_id, servico_id=servico_id, quantidade=quantidade, valor=valor,
    )
    return 201, obter_ordem(ordem_id)[1]


def remover_item(ordem_id, servico_id):
    ordem_editavel(ordem_id)
    removido = um(
        "DELETE FROM item_ordem WHERE ordem_id = :o AND servico_id = :s RETURNING servico_id",
        o=ordem_id, s=servico_id,
    )
    if removido is None:
        raise ErroApi(404, "Este serviço não está na ordem.")
    return 204, None


# ---------- anexos (HU-05, RF-02) ----------

TIPOS_ANEXO = {"image/jpeg": "jpg", "image/png": "png", "application/pdf": "pdf"}
TAMANHO_MAXIMO = 10 * 1024 * 1024


def cliente_s3():
    # boto3 já vem no runtime da Lambda; importado aqui para o CRUD rodar
    # localmente sem ele. Gerar URL pré-assinada não usa rede.
    import boto3
    from botocore.config import Config
    return boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"),
                        config=Config(signature_version="s3v4"))


def gerar_upload_url(ordem_id, d):
    buscar_ou_404("SELECT id FROM ordem_servico WHERE id = :id", "Ordem de serviço", id=ordem_id)
    nome = texto(d, "nomeArquivo", maximo=200)
    tipo = (texto(d, "tipo", maximo=60) or "").lower()
    if tipo not in TIPOS_ANEXO:
        raise ErroApi(400, "Só são aceitos arquivos JPG, PNG e PDF.")
    tamanho = inteiro(d, "tamanho", minimo=1)
    if tamanho > TAMANHO_MAXIMO:
        raise ErroApi(400, "O arquivo deve ter no máximo 10 MB.")
    bucket = os.environ.get("ANEXOS_BUCKET")
    if not bucket:
        raise ErroApi(503, "Upload de anexos não configurado (variável ANEXOS_BUCKET).")

    chave = f"uploads/ordens/{ordem_id}/{uuid.uuid4().hex}.{TIPOS_ANEXO[tipo]}"
    # Válida por 5 minutos e só para este Content-Type (ADR-003)
    url = cliente_s3().generate_presigned_url(
        "put_object", Params={"Bucket": bucket, "Key": chave, "ContentType": tipo}, ExpiresIn=300,
    )
    # A Lambda processa-anexo muda a situação para PROCESSADO ou ERRO (RF-03)
    anexo = um(
        """INSERT INTO anexo (ordem_id, chave_s3, nome_original, tipo, tamanho_bytes)
           VALUES (:ordem_id, :chave, :nome, :tipo, :tamanho) RETURNING *""",
        ordem_id=ordem_id, chave=chave, nome=nome, tipo=tipo, tamanho=tamanho,
    )
    return 201, {"anexo": anexo, "uploadUrl": url, "headers": {"Content-Type": tipo}}


def listar_anexos(ordem_id):
    buscar_ou_404("SELECT id FROM ordem_servico WHERE id = :id", "Ordem de serviço", id=ordem_id)
    anexos = sql("SELECT * FROM anexo WHERE ordem_id = :id ORDER BY enviado_em, id", id=ordem_id)
    bucket = os.environ.get("ANEXOS_BUCKET")
    s3 = cliente_s3() if bucket and anexos else None
    for a in anexos:
        # O bucket é privado: o navegador lê por URLs de leitura temporárias
        a["url"] = a["urlMiniatura"] = None
        if s3:
            a["url"] = s3.generate_presigned_url(
                "get_object", Params={"Bucket": bucket, "Key": a["chaveS3"]}, ExpiresIn=3600)
            if a["chaveMiniatura"]:
                a["urlMiniatura"] = s3.generate_presigned_url(
                    "get_object", Params={"Bucket": bucket, "Key": a["chaveMiniatura"]}, ExpiresIn=3600)
    return 200, anexos


# ---------- roteamento ----------

ROTAS = [
    ("GET", r"clientes", lambda m, q, d: listar_clientes(q)),
    ("POST", r"clientes", lambda m, q, d: criar_cliente(d)),
    ("GET", r"clientes/(\d+)", lambda m, q, d: obter_cliente(int(m[1]))),
    ("PUT", r"clientes/(\d+)", lambda m, q, d: atualizar_cliente(int(m[1]), d)),
    ("DELETE", r"clientes/(\d+)", lambda m, q, d: excluir_cliente(int(m[1]))),
    ("GET", r"veiculos", lambda m, q, d: listar_veiculos(q)),
    ("POST", r"veiculos", lambda m, q, d: criar_veiculo(d)),
    ("GET", r"veiculos/(\d+)", lambda m, q, d: obter_veiculo(int(m[1]))),
    ("PUT", r"veiculos/(\d+)", lambda m, q, d: atualizar_veiculo(int(m[1]), d)),
    ("DELETE", r"veiculos/(\d+)", lambda m, q, d: excluir_veiculo(int(m[1]))),
    ("GET", r"servicos", lambda m, q, d: listar_servicos(q)),
    ("POST", r"servicos", lambda m, q, d: criar_servico(d)),
    ("PUT", r"servicos/(\d+)", lambda m, q, d: atualizar_servico(int(m[1]), d)),
    ("DELETE", r"servicos/(\d+)", lambda m, q, d: excluir_servico(int(m[1]))),
    ("GET", r"ordens", lambda m, q, d: listar_ordens(q)),
    ("POST", r"ordens", lambda m, q, d: criar_ordem(d)),
    ("GET", r"ordens/(\d+)", lambda m, q, d: obter_ordem(int(m[1]))),
    ("PUT", r"ordens/(\d+)", lambda m, q, d: atualizar_ordem(int(m[1]), d)),
    ("DELETE", r"ordens/(\d+)", lambda m, q, d: excluir_ordem(int(m[1]))),
    ("POST", r"ordens/(\d+)/itens", lambda m, q, d: adicionar_item(int(m[1]), d)),
    ("DELETE", r"ordens/(\d+)/itens/(\d+)", lambda m, q, d: remover_item(int(m[1]), int(m[2]))),
    ("POST", r"ordens/(\d+)/anexos/upload-url", lambda m, q, d: gerar_upload_url(int(m[1]), d)),
    ("GET", r"ordens/(\d+)/anexos", lambda m, q, d: listar_anexos(int(m[1]))),
]

# Mensagens para violações de restrição do banco (SQLSTATE)
MENSAGENS_FK = {
    "veiculo_cliente_id_fkey": "Não é possível excluir: o cliente tem veículos cadastrados.",
    "ordem_servico_veiculo_id_fkey": "Não é possível excluir: o veículo tem ordens de serviço.",
    "item_ordem_servico_id_fkey": "Este serviço já foi usado em ordens e não pode ser excluído. Desative-o.",
}
MENSAGENS_UNIQUE = {
    "cliente_telefone_key": "Já existe um cliente com este telefone.",
    "veiculo_placa_key": "Já existe um veículo com esta placa.",
}


def erro_do_banco(e, metodo):
    info = e.args[0] if e.args and isinstance(e.args[0], dict) else {}
    codigo, restricao = info.get("C"), info.get("n", "")
    if codigo == "23503":
        # No DELETE a FK violada é de um registro dependente (ON DELETE RESTRICT);
        # no POST/PUT é uma referência a um id que não existe.
        if metodo == "DELETE":
            return ErroApi(409, MENSAGENS_FK.get(restricao, "Existem registros ligados a este."))
        return ErroApi(400, "Registro relacionado não encontrado.")
    if codigo == "23505":
        return ErroApi(409, MENSAGENS_UNIQUE.get(restricao, "Registro duplicado."))
    if codigo in ("23514", "22001", "22003"):
        return ErroApi(400, "Dados inválidos para o banco.")
    return None


def despachar(metodo, caminho, query, corpo):
    caminho = caminho.strip("/")
    metodo_existe = False
    for rota_metodo, padrao, acao in ROTAS:
        m = re.fullmatch(padrao, caminho)
        if m:
            metodo_existe = True
            if rota_metodo == metodo:
                return acao(m, query, corpo)
    if metodo_existe:
        raise ErroApi(405, "Método não permitido nesta rota.")
    raise ErroApi(404, "Rota não encontrada.")


def handler(event, context):
    global _conn
    metodo = event.get("httpMethod", "GET")
    if metodo == "OPTIONS":
        return resposta(204)

    caminho = (event.get("pathParameters") or {}).get("proxy") or event.get("path", "")
    query = event.get("queryStringParameters") or {}
    try:
        corpo = json.loads(event.get("body") or "{}")
        if not isinstance(corpo, dict):
            raise ValueError
    except ValueError:
        return resposta(400, {"erro": "Corpo da requisição deve ser um objeto JSON."})

    for tentativa in range(2):
        try:
            status, dados = despachar(metodo, caminho, query, corpo)
            return resposta(status, dados)
        except ErroApi as e:
            return resposta(e.status, {"erro": e.mensagem})
        except DatabaseError as e:
            erro = erro_do_banco(e, metodo)
            if erro:
                return resposta(erro.status, {"erro": erro.mensagem})
            print("Erro do banco:", e)
            return resposta(500, {"erro": "Erro interno no banco de dados."})
        except (InterfaceError, OSError) as e:
            # Conexão reaproveitada caiu (ex.: RDS reiniciado): reconecta uma vez
            print("Falha de conexão, tentativa", tentativa + 1, ":", e)
            _conn = None
    return resposta(503, {"erro": "Banco de dados indisponível."})
