#!/usr/bin/env bash
# Gera build/crud.zip para enviar à Lambda girocerto-crud (runtime Python 3.12, x86_64).
# Uso: ./scripts/empacotar-crud.sh
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf build/crud && mkdir -p build/crud
pip3 install -q -r backend/crud/requirements.txt -t build/crud \
  --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all:
cp backend/crud/app.py build/crud/
# Certificado da AWS para a Lambda validar o TLS do RDS
curl -sSf -o build/crud/global-bundle.pem https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem

rm -f build/crud.zip
(cd build/crud && zip -qr ../crud.zip .)
echo "Pacote gerado: build/crud.zip ($(du -h build/crud.zip | cut -f1))"
