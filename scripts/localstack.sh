#!/usr/bin/env bash
set -euo pipefail

STAGE="${STAGE:-local}"

if ! command -v awslocal >/dev/null 2>&1; then
  echo "awslocal is not installed. Install with: pip install awscli-local" >&2
  exit 1
fi

echo "Deploying CloudFormation (stage: ${STAGE})..."
bash "$(dirname "$0")/deploy_localstack.sh"

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

