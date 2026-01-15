#!/usr/bin/env bash
set -euo pipefail

API_ID="${API_ID:-}"
STAGE="${STAGE:-local}"
BASE_URL="${BASE_URL:-}"

if [[ -z "${BASE_URL}" ]]; then
  if [[ -z "${API_ID}" ]]; then
    echo "Set API_ID or BASE_URL before running." >&2
    echo "Example: API_ID=abcd1234 $0" >&2
    echo "Or: BASE_URL=http://localhost:4566/restapis/abcd1234/local/_user_request_ $0" >&2
    exit 1
  fi
  BASE_URL="http://localhost:4566/restapis/${API_ID}/${STAGE}/_user_request_"
fi

echo "Base URL: ${BASE_URL}"

USER_ID="${USER_ID:-user-1}"
IMAGE_PATH="${IMAGE_PATH:-./sample.jpg}"

if [[ ! -f "${IMAGE_PATH}" ]]; then
  echo "Image file not found: ${IMAGE_PATH}" >&2
  exit 1
fi

echo "1) Upload JSON base64"
IMAGE_BASE64="$(python - <<'PY'
import base64, sys
path = sys.argv[1]
with open(path, "rb") as fh:
    print(base64.b64encode(fh.read()).decode("utf-8"))
PY
"${IMAGE_PATH}")"
UPLOAD_JSON_RESPONSE="$(curl -s -X POST "${BASE_URL}/images/upload-json" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"${USER_ID}\",\"file_name\":\"sample.jpg\",\"content_type\":\"image/jpeg\",\"image_base64\":\"${IMAGE_BASE64}\",\"tags\":[\"test\"],\"description\":\"sample\"}")"
echo "${UPLOAD_JSON_RESPONSE}"
IMAGE_ID="$(
  UPLOAD_JSON_RESPONSE="${UPLOAD_JSON_RESPONSE}" python - <<'PY'
import json, os
resp = os.environ.get("UPLOAD_JSON_RESPONSE", "{}")
print(json.loads(resp).get("image_id", ""))
PY
)"

if [[ -z "${IMAGE_ID}" ]]; then
  echo "Failed to parse image_id from JSON upload response." >&2
  exit 1
fi

echo "2) Upload multipart"
curl -s -X POST "${BASE_URL}/images/upload-multipart" \
  -F "user_id=${USER_ID}" \
  -F "tags=a,b" \
  -F "description=sample" \
  -F "file=@${IMAGE_PATH}" | cat
echo ""

echo "3) List images"
curl -s "${BASE_URL}/images?user_id=${USER_ID}&tag=test" | cat
echo ""

echo "4) Get metadata"
curl -s "${BASE_URL}/images/${IMAGE_ID}" | cat
echo ""

echo "5) Download image (base64)"
curl -s "${BASE_URL}/images/${IMAGE_ID}/download" | cat
echo ""

echo "6) Delete image"
curl -s -X DELETE "${BASE_URL}/images/${IMAGE_ID}" | cat
echo ""

echo "Done."

