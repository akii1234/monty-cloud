import base64
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from . import storage
from .utils import (
    build_response,
    decode_base64_image,
    decode_pagination_key,
    encode_pagination_key,
    get_body_bytes,
    parse_multipart,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_s3_key(user_id: str, image_id: str, file_name: str) -> str:
    safe_name = file_name.replace("/", "_")
    return f"{user_id}/{image_id}/{safe_name}"


def _parse_tags(raw: Optional[Any]) -> list:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(tag).strip() for tag in raw if str(tag).strip()]
    return [tag.strip() for tag in str(raw).split(",") if tag.strip()]


def health(_event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    return build_response(200, {"status": "ok"})


def upload_json(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    try:
        payload = json.loads(event.get("body") or "{}")
        user_id = payload.get("user_id")
        file_name = payload.get("file_name")
        content_type = payload.get("content_type")
        image_base64 = payload.get("image_base64")
        if not all([user_id, file_name, content_type, image_base64]):
            return build_response(400, {"message": "user_id, file_name, content_type, image_base64 required"})

        image_bytes = decode_base64_image(image_base64)
        image_id = str(uuid.uuid4())
        created_at = _now_iso()
        tags = _parse_tags(payload.get("tags"))
        description = payload.get("description", "")

        s3_key = _build_s3_key(user_id, image_id, file_name)
        storage.s3_client().put_object(
            Bucket=storage.images_bucket(),
            Key=s3_key,
            Body=image_bytes,
            ContentType=content_type,
        )

        metadata = {
            "user_id": user_id,
            "created_at": created_at,
            "image_id": image_id,
            "file_name": file_name,
            "content_type": content_type,
            "size_bytes": len(image_bytes),
            "tags": tags,
            "description": description,
            "s3_bucket": storage.images_bucket(),
            "s3_key": s3_key,
        }
        storage.put_metadata(metadata)

        return build_response(201, {"image_id": image_id, "created_at": created_at})
    except ValueError as exc:
        return build_response(400, {"message": str(exc)})


def upload_multipart(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    headers = event.get("headers") or {}
    content_type = headers.get("content-type") or headers.get("Content-Type")
    if not content_type:
        return build_response(400, {"message": "Content-Type header required"})

    fields, files = parse_multipart(get_body_bytes(event), content_type)
    file_payload = files.get("file")
    if not file_payload:
        return build_response(400, {"message": "file field required"})

    user_id = fields.get("user_id")
    if not user_id:
        return build_response(400, {"message": "user_id field required"})

    file_name = file_payload["filename"]
    file_bytes = file_payload["content"]
    file_content_type = file_payload["content_type"]

    image_id = str(uuid.uuid4())
    created_at = _now_iso()
    tags = _parse_tags(fields.get("tags"))
    description = fields.get("description", "")

    s3_key = _build_s3_key(user_id, image_id, file_name)
    storage.s3_client().put_object(
        Bucket=storage.images_bucket(),
        Key=s3_key,
        Body=file_bytes,
        ContentType=file_content_type,
    )

    metadata = {
        "user_id": user_id,
        "created_at": created_at,
        "image_id": image_id,
        "file_name": file_name,
        "content_type": file_content_type,
        "size_bytes": len(file_bytes),
        "tags": tags,
        "description": description,
        "s3_bucket": storage.images_bucket(),
        "s3_key": s3_key,
    }
    storage.put_metadata(metadata)

    return build_response(201, {"image_id": image_id, "created_at": created_at})


def list_images(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    params = event.get("queryStringParameters") or {}
    user_id = params.get("user_id")
    if not user_id:
        return build_response(400, {"message": "user_id query parameter required"})

    created_from = params.get("created_from")
    created_to = params.get("created_to")
    tag = params.get("tag")
    content_type = params.get("content_type")
    limit = int(params.get("limit", 50))
    next_token = params.get("next_token")

    items, last_key = storage.query_metadata(
        user_id=user_id,
        created_from=created_from,
        created_to=created_to,
        tag=tag,
        content_type=content_type,
        limit=limit,
        last_evaluated_key=decode_pagination_key(next_token),
    )

    for item in items:
        item.pop("s3_bucket", None)
        item.pop("s3_key", None)

    return build_response(
        200,
        {
            "items": items,
            "next_token": encode_pagination_key(last_key),
        },
    )


def get_image_metadata(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    image_id = (event.get("pathParameters") or {}).get("imageId")
    if not image_id:
        return build_response(400, {"message": "imageId path parameter required"})

    item = storage.get_metadata_by_image_id(image_id)
    if not item:
        return build_response(404, {"message": "Image not found"})

    item.pop("s3_bucket", None)
    item.pop("s3_key", None)
    return build_response(200, item)


def download_image(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    image_id = (event.get("pathParameters") or {}).get("imageId")
    if not image_id:
        return build_response(400, {"message": "imageId path parameter required"})

    item = storage.get_metadata_by_image_id(image_id)
    if not item:
        return build_response(404, {"message": "Image not found"})

    s3_response = storage.s3_client().get_object(
        Bucket=item["s3_bucket"],
        Key=item["s3_key"],
    )
    body_bytes = s3_response["Body"].read()
    encoded = base64.b64encode(body_bytes).decode("utf-8")

    headers = {
        "Content-Type": item.get("content_type", "application/octet-stream"),
        "Content-Disposition": f'attachment; filename="{item.get("file_name", "image")}"',
    }
    return build_response(200, encoded, headers=headers, is_base64=True)


def delete_image(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    image_id = (event.get("pathParameters") or {}).get("imageId")
    if not image_id:
        return build_response(400, {"message": "imageId path parameter required"})

    item = storage.get_metadata_by_image_id(image_id)
    if not item:
        return build_response(404, {"message": "Image not found"})

    storage.s3_client().delete_object(Bucket=item["s3_bucket"], Key=item["s3_key"])
    storage.delete_metadata(item["user_id"], item["created_at"])

    return build_response(200, {"message": "Image deleted"})

