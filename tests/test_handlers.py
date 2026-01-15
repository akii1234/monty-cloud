import base64
import json

from freezegun import freeze_time
from requests_toolbelt.multipart.encoder import MultipartEncoder

from src import handlers


def _json_event(payload):
    return {"body": json.dumps(payload), "isBase64Encoded": False}


def _multipart_event(fields):
    encoder = MultipartEncoder(fields=fields)
    body = encoder.to_string()
    return {
        "headers": {"Content-Type": encoder.content_type},
        "body": base64.b64encode(body).decode("utf-8"),
        "isBase64Encoded": True,
    }


def test_upload_json_success(aws_services):
    payload = {
        "user_id": "user-1",
        "file_name": "photo.jpg",
        "content_type": "image/jpeg",
        "image_base64": base64.b64encode(b"image-bytes").decode("utf-8"),
        "tags": ["summer", "trip"],
        "description": "Beach day",
    }
    response = handlers.upload_json(_json_event(payload), None)
    body = json.loads(response["body"])
    assert response["statusCode"] == 201
    assert "image_id" in body


def test_upload_json_missing_fields(aws_services):
    response = handlers.upload_json(_json_event({"user_id": "user-1"}), None)
    assert response["statusCode"] == 400


def test_upload_multipart_success(aws_services):
    fields = {
        "user_id": "user-2",
        "tags": "a,b",
        "description": "desc",
        "file": ("avatar.png", b"file-bytes", "image/png"),
    }
    response = handlers.upload_multipart(_multipart_event(fields), None)
    body = json.loads(response["body"])
    assert response["statusCode"] == 201
    assert "image_id" in body


def test_list_images_with_filters(aws_services):
    with freeze_time("2024-01-01T10:00:00Z"):
        handlers.upload_json(
            _json_event(
                {
                    "user_id": "user-3",
                    "file_name": "one.jpg",
                    "content_type": "image/jpeg",
                    "image_base64": base64.b64encode(b"one").decode("utf-8"),
                    "tags": ["travel"],
                }
            ),
            None,
        )
    with freeze_time("2024-02-01T10:00:00Z"):
        handlers.upload_json(
            _json_event(
                {
                    "user_id": "user-3",
                    "file_name": "two.jpg",
                    "content_type": "image/png",
                    "image_base64": base64.b64encode(b"two").decode("utf-8"),
                    "tags": ["work"],
                }
            ),
            None,
        )

    event = {
        "queryStringParameters": {
            "user_id": "user-3",
            "created_from": "2024-02-01T00:00:00+00:00",
            "tag": "work",
        }
    }
    response = handlers.list_images(event, None)
    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert len(body["items"]) == 1
    assert body["items"][0]["content_type"] == "image/png"


def test_get_metadata_and_download(aws_services):
    upload_response = handlers.upload_json(
        _json_event(
            {
                "user_id": "user-4",
                "file_name": "doc.png",
                "content_type": "image/png",
                "image_base64": base64.b64encode(b"download").decode("utf-8"),
            }
        ),
        None,
    )
    image_id = json.loads(upload_response["body"])["image_id"]

    meta_response = handlers.get_image_metadata({"pathParameters": {"imageId": image_id}}, None)
    assert meta_response["statusCode"] == 200

    download_response = handlers.download_image({"pathParameters": {"imageId": image_id}}, None)
    assert download_response["statusCode"] == 200
    assert download_response["isBase64Encoded"] is True


def test_delete_image(aws_services):
    upload_response = handlers.upload_json(
        _json_event(
            {
                "user_id": "user-5",
                "file_name": "del.png",
                "content_type": "image/png",
                "image_base64": base64.b64encode(b"delete").decode("utf-8"),
            }
        ),
        None,
    )
    image_id = json.loads(upload_response["body"])["image_id"]

    delete_response = handlers.delete_image({"pathParameters": {"imageId": image_id}}, None)
    assert delete_response["statusCode"] == 200

    missing = handlers.get_image_metadata({"pathParameters": {"imageId": image_id}}, None)
    assert missing["statusCode"] == 404


def test_health():
    response = handlers.health({}, None)
    assert response["statusCode"] == 200

