import base64
import binascii
import json
from cgi import parse_header
from typing import Any, Dict, Optional, Tuple

from requests_toolbelt.multipart import decoder


def build_response(
    status_code: int,
    body: Any,
    headers: Optional[Dict[str, str]] = None,
    is_base64: bool = False,
) -> Dict[str, Any]:
    response_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
    }
    if headers:
        response_headers.update(headers)

    if isinstance(body, (dict, list)):
        body = json.dumps(body)
    elif body is None:
        body = ""

    return {
        "statusCode": status_code,
        "headers": response_headers,
        "body": body,
        "isBase64Encoded": is_base64,
    }


def get_body_bytes(event: Dict[str, Any]) -> bytes:
    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        return base64.b64decode(body)
    return body.encode("utf-8")


def decode_base64_image(data: str) -> bytes:
    if "base64," in data:
        data = data.split("base64,", 1)[1]
    try:
        return base64.b64decode(data)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid base64 image data") from exc


def parse_multipart(body: bytes, content_type: str) -> Tuple[Dict[str, str], Dict[str, Dict[str, Any]]]:
    fields: Dict[str, str] = {}
    files: Dict[str, Dict[str, Any]] = {}

    parsed = decoder.MultipartDecoder(body, content_type)
    for part in parsed.parts:
        disposition = part.headers.get(b"Content-Disposition", b"").decode("utf-8")
        _, params = parse_header(disposition)
        name = params.get("name")
        if not name:
            continue
        filename = params.get("filename")
        if filename:
            file_content_type = part.headers.get(b"Content-Type", b"application/octet-stream").decode("utf-8")
            files[name] = {
                "filename": filename,
                "content_type": file_content_type,
                "content": part.content,
            }
        else:
            fields[name] = part.text

    return fields, files


def encode_pagination_key(key: Optional[Dict[str, Any]]) -> Optional[str]:
    if not key:
        return None
    raw = json.dumps(key)
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


def decode_pagination_key(token: Optional[str]) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    raw = base64.b64decode(token.encode("utf-8")).decode("utf-8")
    return json.loads(raw)

