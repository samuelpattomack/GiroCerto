"""Lambda relatorios do GiroCerto (RF-04, HU-06).

Atrás do recurso /relatorios/{proxy+} do API Gateway (integração proxy).
Só considera ordens CONCLUIDA, pela data de saída, no intervalo
?inicio=AAAA-MM-DD&fim=AAAA-MM-DD (padrão: últimos 12 meses).
"""

import datetime

from pg8000.exceptions import DatabaseError, InterfaceError

import banco


class ErroApi(Exception):
    def __init__(self, status, mensagem):
        super().__init__(mensagem)
        self.status = status
        self.mensagem = mensagem


def periodo(q):
    try:
        fim = datetime.date.fromisoformat(q["fim"]) if q.get("fim") else datetime.date.today()
        if q.get("inicio"):
            inicio = datetime.date.fromisoformat(q["inicio"])
        else:
            # Primeiro dia do mês, 11 meses antes do fim: 12 meses completos
            meses = fim.year * 12 + fim.month - 1 - 11
            inicio = datetime.date(meses // 12, meses % 12 + 1, 1)
    except ValueError:
        raise ErroApi(400, "Datas devem estar no formato AAAA-MM-DD.")
    if inicio > fim:
        raise ErroApi(400, "A data de início deve ser anterior à data de fim.")
    return inicio, fim


def faturamento_mensal(q):
    inicio, fim = periodo(q)
    meses = banco.sql(
        """SELECT to_char(date_trunc('month', o.data_saida), 'YYYY-MM') AS mes,
                  COUNT(DISTINCT o.id) AS ordens,
                  SUM(i.quantidade * i.valor_unitario) AS total
           FROM ordem_servico o
           JOIN item_ordem i ON i.ordem_id = o.id
           WHERE o.status = 'CONCLUIDA'
             AND o.data_saida BETWEEN :inicio AND :fim
           GROUP BY date_trunc('month', o.data_saida)
           ORDER BY mes""",
        inicio=inicio, fim=fim,
    )
    return {
        "inicio": inicio, "fim": fim, "meses": meses,
        "totalOrdens": sum(m["ordens"] for m in meses),
        "totalFaturado": sum((m["total"] for m in meses), 0),
    }


def servicos_mais_realizados(q):
    inicio, fim = periodo(q)
    servicos = banco.sql(
        """SELECT s.id, s.nome, s.categoria,
                  SUM(i.quantidade) AS quantidade,
                  COUNT(DISTINCT o.id) AS ordens,
                  SUM(i.quantidade * i.valor_unitario) AS receita
           FROM item_ordem i
           JOIN servico s ON s.id = i.servico_id
           JOIN ordem_servico o ON o.id = i.ordem_id
           WHERE o.status = 'CONCLUIDA'
             AND o.data_saida BETWEEN :inicio AND :fim
           GROUP BY s.id, s.nome, s.categoria
           ORDER BY quantidade DESC, receita DESC
           LIMIT 10""",
        inicio=inicio, fim=fim,
    )
    return {"inicio": inicio, "fim": fim, "servicos": servicos}


ROTAS = {
    "faturamento-mensal": faturamento_mensal,
    "servicos-mais-realizados": servicos_mais_realizados,
}


def handler(event, context):
    metodo = event.get("httpMethod", "GET")
    if metodo == "OPTIONS":
        return banco.resposta(204)
    if metodo != "GET":
        return banco.resposta(405, {"erro": "Relatórios só aceitam GET."})

    caminho = (event.get("pathParameters") or {}).get("proxy") or event.get("path", "")
    nome = caminho.strip("/").split("/")[-1]
    acao = ROTAS.get(nome)
    if acao is None:
        return banco.resposta(404, {"erro": "Relatório não encontrado."})

    query = event.get("queryStringParameters") or {}
    for tentativa in range(2):
        try:
            return banco.resposta(200, acao(query))
        except ErroApi as e:
            return banco.resposta(e.status, {"erro": e.mensagem})
        except DatabaseError as e:
            print("Erro do banco:", e)
            return banco.resposta(500, {"erro": "Erro interno no banco de dados."})
        except (InterfaceError, OSError) as e:
            print("Falha de conexão, tentativa", tentativa + 1, ":", e)
            banco.descartar_conexao()
    return banco.resposta(503, {"erro": "Banco de dados indisponível."})
