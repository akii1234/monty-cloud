#!/usr/bin/env bash
set -euo pipefail

STAGE="${STAGE:-local}"
STACK_NAME="${STACK_NAME:-monty-cloud-${STAGE}}"
REGION="${AWS_REGION:-us-east-1}"
ARTIFACT_BUCKET="${ARTIFACT_BUCKET:-monty-cloud-artifacts-${STAGE}}"
CODE_KEY="${CODE_KEY:-lambda.zip}"
IMAGES_BUCKET="${IMAGES_BUCKET:-monty-cloud-images-${STAGE}}"
IMAGES_TABLE="${IMAGES_TABLE:-monty-cloud-images-${STAGE}}"
LOCALSTACK_ENDPOINT="${LOCALSTACK_ENDPOINT:-http://localhost:4566}"

if ! command -v awslocal >/dev/null 2>&1; then
  echo "awslocal is not installed. Install with: pip install awscli-local" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/.build"
ZIP_PATH="${BUILD_DIR}/${CODE_KEY}"

mkdir -p "${BUILD_DIR}"
rm -f "${ZIP_PATH}"
(cd "${ROOT_DIR}" && zip -rq "${ZIP_PATH}" src)

awslocal s3 mb "s3://${ARTIFACT_BUCKET}" >/dev/null 2>&1 || true
awslocal s3 cp "${ZIP_PATH}" "s3://${ARTIFACT_BUCKET}/${CODE_KEY}"

awslocal cloudformation deploy \
  --stack-name "${STACK_NAME}" \
  --template-file "${ROOT_DIR}/template.yaml" \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    Stage="${STAGE}" \
    ImagesBucketName="${IMAGES_BUCKET}" \
    ImagesTableName="${IMAGES_TABLE}" \
    CodeS3Bucket="${ARTIFACT_BUCKET}" \
    CodeS3Key="${CODE_KEY}" \
    LocalstackEndpoint="${LOCALSTACK_ENDPOINT}" \
  --region "${REGION}"

API_ID="$(awslocal cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiId'].OutputValue" \
  --output text \
  --region "${REGION}")"

if [[ -n "${API_ID}" && "${API_ID}" != "None" ]]; then
  echo "API ID: ${API_ID}"
  echo "Base URL: http://localhost:4566/restapis/${API_ID}/${STAGE}/_user_request_"
fi

