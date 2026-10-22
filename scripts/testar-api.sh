#!/usr/bin/env bash
# Percorre o CRUD de clientes e veículos na API publicada.
# Uso: ./scripts/testar-api.sh https://<api-id>.execute-api.us-east-1.amazonaws.com/prod
set -euo pipefail
API="${1:?informe a URL do stage do API Gateway}"
API="${API%/}"

chamar() {
  echo
  echo ">>> $1 $2 ${3:-}"
  curl -sS -X "$1" "$API$2" -H "Content-Type: application/json" ${3:+-d "$3"} -w "\n[HTTP %{http_code}]\n"
}
id_de() { python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])'; }

SUFIXO=$(date +%H%M%S)
TEL="1190${SUFIXO}0"
PLACA="TST${SUFIXO:0:1}A${SUFIXO:4:2}"

chamar GET /clientes
CLIENTE=$(curl -sS -X POST "$API/clientes" -H "Content-Type: application/json" \
  -d "{\"nome\":\"Cliente Teste $SUFIXO\",\"telefone\":\"$TEL\"}" | id_de)
echo; echo "Cliente criado: id=$CLIENTE"
chamar PUT "/clientes/$CLIENTE" '{"email":"teste@example.com"}'

VEICULO=$(curl -sS -X POST "$API/veiculos" -H "Content-Type: application/json" \
  -d "{\"clienteId\":$CLIENTE,\"placa\":\"$PLACA\",\"marca\":\"Fiat\",\"modelo\":\"Uno\",\"ano\":2010}" | id_de)
echo; echo "Veículo criado: id=$VEICULO placa=$PLACA"
chamar GET "/clientes/$CLIENTE"
chamar PUT "/veiculos/$VEICULO" '{"ano":2011}'
chamar GET "/veiculos?clienteId=$CLIENTE"

echo; echo "--- exclusão bloqueada: cliente com veículo (espera 409)"
chamar DELETE "/clientes/$CLIENTE"

chamar DELETE "/veiculos/$VEICULO"
chamar DELETE "/clientes/$CLIENTE"
chamar GET "/clientes/$CLIENTE"
