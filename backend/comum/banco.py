"""Conexão com o RDS e respostas HTTP, compartilhado pelas Lambdas
relatorios e processa-anexo. Vai na raiz do .zip de cada uma
(scripts/empacotar.sh). Variáveis: DB_HOST, DB_PORT, DB_NAME, DB_USER,
DB_PASSWORD e, só para teste local, DB_SSL=off.
"""

import datetime
import decimal
import json
import os
import ssl

import pg8000.native

CORS_HEADERS = {
    "Access-Control-Allow-Origin": os.environ.get("CORS_ORIGIN", "*"),
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

# Criada fora do handler para ser reaproveitada entre invocações (ADR-001)
_conn = None


def _ssl_context():
    ca = os.path.join(os.path.dirname(__file__), "global-bundle.pem")
    if os.path.exists(ca):
        return ssl.create_default_context(cafile=ca)
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


def descartar_conexao():
    """Chamado quando a conexão reaproveitada caiu; a próxima chamada reconecta."""
    global _conn
    _conn = None


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
