#!/usr/bin/env bash
set -euo pipefail

TABLE_NAME="${IMAGES_TABLE:-monty-cloud-images-local}"
BUCKET_NAME="${IMAGES_BUCKET:-monty-cloud-images-local}"
REGION="${AWS_REGION:-us-east-1}"

awslocal s3 mb "s3://${BUCKET_NAME}" || true

awslocal dynamodb create-table \
  --table-name "${TABLE_NAME}" \
  --billing-mode PAY_PER_REQUEST \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=created_at,AttributeType=S \
    AttributeName=image_id,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=created_at,KeyType=RANGE \
  --global-secondary-indexes \
    "IndexName=image_id_index,KeySchema=[{AttributeName=image_id,KeyType=HASH}],Projection={ProjectionType=ALL}" \
  --region "${REGION}" || true

