# API Documentation

Base URL (local):
`http://localhost:4566/restapis/<api-id>/local/_user_request_`

Tip: run `bash scripts/deploy_localstack.sh` and use the printed Base URL.

## Health
`GET /health`

Response:
```json
{ "status": "ok" }
```

## Upload Image (JSON base64)
`POST /images/upload-json`

Headers:
- `Content-Type: application/json`

Body:
```json
{
  "user_id": "user-1",
  "file_name": "photo.jpg",
  "content_type": "image/jpeg",
  "image_base64": "<base64>",
  "tags": ["travel", "summer"],
  "description": "Beach"
}
```

Response:
```json
{
  "image_id": "uuid",
  "created_at": "2024-01-01T00:00:00+00:00"
}
```

Example:
```bash
curl -X POST "$BASE_URL/images/upload-json" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user-1","file_name":"photo.jpg","content_type":"image/jpeg","image_base64":"<base64>"}'
```

## Upload Image (multipart/form-data)
`POST /images/upload-multipart`

Form fields:
- `user_id` (required)
- `file` (required)
- `tags` (optional, comma-separated)
- `description` (optional)

Example:
```bash
curl -X POST "$BASE_URL/images/upload-multipart" \
  -F user_id=user-1 \
  -F tags=travel,summer \
  -F description=Beach \
  -F file=@./photo.jpg
```

## List Images
`GET /images`

Query parameters:
- `user_id` (required)
- `created_from` (optional, ISO8601)
- `created_to` (optional, ISO8601)
- `tag` (optional)
- `content_type` (optional)
- `limit` (optional, default 50)
- `next_token` (optional)

Response:
```json
{
  "items": [],
  "next_token": null
}
```

Example:
```bash
curl "$BASE_URL/images?user_id=user-1&tag=travel"
```

## Get Image Metadata
`GET /images/{imageId}`

Response:
```json
{
  "user_id": "user-1",
  "created_at": "2024-01-01T00:00:00+00:00",
  "image_id": "uuid",
  "file_name": "photo.jpg",
  "content_type": "image/jpeg",
  "size_bytes": 12345,
  "tags": ["travel"],
  "description": "Beach"
}
```

## Download Image
`GET /images/{imageId}/download`

Returns base64-encoded body with `isBase64Encoded: true`.

Example:
```bash
curl "$BASE_URL/images/<imageId>/download"
```

## Delete Image
`DELETE /images/{imageId}`

Response:
```json
{ "message": "Image deleted" }
```

## Errors
Common error response:
```json
{ "message": "Error details" }
```

