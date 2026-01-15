#!/usr/bin/env bash
set -euo pipefail

STAGE="${STAGE:-local}"

if ! command -v localstack >/dev/null 2>&1; then
  echo "localstack is not installed. Install with: pip install localstack" >&2
  exit 1
fi

if ! command -v serverless >/dev/null 2>&1; then
  echo "serverless is not installed. Install with: npm i -g serverless" >&2
  exit 1
fi

echo "Starting LocalStack..."
localstack start -d

echo "Deploying Serverless (stage: ${STAGE})..."
serverless deploy --stage "${STAGE}"

echo "Fetching API ID..."
API_ID="$(awslocal apigateway get-rest-apis --query 'items[0].id' --output text)"
if [[ -z "${API_ID}" || "${API_ID}" == "None" ]]; then
  echo "Could not find API Gateway ID. Is LocalStack running?" >&2
  exit 1
fi

BASE_URL="http://localhost:4566/restapis/${API_ID}/${STAGE}/_user_request_"
echo "Base URL: ${BASE_URL}"

echo "Calling /health"
curl -s "${BASE_URL}/health" | cat
echo ""

echo "Done."

