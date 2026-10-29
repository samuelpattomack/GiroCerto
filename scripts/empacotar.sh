#!/usr/bin/env bash
# Gera build/<função>.zip para cada Lambda (runtime Python 3.12, x86_64).
# Uso: ./scripts/empacotar.sh            (todas)
#      ./scripts/empacotar.sh crud       (só uma: crud, relatorios ou processa_anexo)
set -euo pipefail
cd "$(dirname "$0")/.."

FUNCOES=("$@")
[ ${#FUNCOES[@]} -eq 0 ] && FUNCOES=(crud relatorios processa_anexo)

mkdir -p build
# Certificado da AWS para as Lambdas validarem o TLS do RDS
[ -f build/global-bundle.pem ] || curl -sSf -o build/global-bundle.pem \
  https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem

for f in "${FUNCOES[@]}"; do
  [ -d "backend/$f" ] || { echo "Função desconhecida: $f"; exit 1; }
  rm -rf "build/$f" "build/$f.zip" && mkdir -p "build/$f"
  pip3 install -q -r "backend/$f/requirements.txt" -t "build/$f" \
    --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all:
  cp backend/"$f"/*.py "build/$f/"
  # banco.py compartilhado (a crud tem a própria conexão)
  [ "$f" = crud ] || cp backend/comum/*.py "build/$f/"
  cp build/global-bundle.pem "build/$f/"
  (cd "build/$f" && zip -qr "../$f.zip" .)
  echo "Pacote gerado: build/$f.zip ($(du -h "build/$f.zip" | cut -f1))"
done
