import os
from typing import Any, Dict, List, Optional, Tuple

import boto3
from boto3.dynamodb.conditions import Attr, Key


def _endpoint_url() -> Optional[str]:
    endpoint = os.getenv("LOCALSTACK_ENDPOINT")
    return endpoint or None


def dynamodb_resource():
    return boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-1"), endpoint_url=_endpoint_url())


def s3_client():
    return boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"), endpoint_url=_endpoint_url())


def images_table():
    return dynamodb_resource().Table(os.environ["IMAGES_TABLE"])


def images_bucket() -> str:
    return os.environ["IMAGES_BUCKET"]


def put_metadata(item: Dict[str, Any]) -> None:
    images_table().put_item(Item=item)


def get_metadata_by_image_id(image_id: str) -> Optional[Dict[str, Any]]:
    response = images_table().query(
        IndexName="image_id_index",
        KeyConditionExpression=Key("image_id").eq(image_id),
        Limit=1,
    )
    items = response.get("Items", [])
    return items[0] if items else None


def delete_metadata(user_id: str, created_at: str) -> None:
    images_table().delete_item(Key={"user_id": user_id, "created_at": created_at})


def query_metadata(
    user_id: str,
    created_from: Optional[str] = None,
    created_to: Optional[str] = None,
    tag: Optional[str] = None,
    content_type: Optional[str] = None,
    limit: int = 50,
    last_evaluated_key: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    key_condition = Key("user_id").eq(user_id)
    if created_from and created_to:
        key_condition &= Key("created_at").between(created_from, created_to)
    elif created_from:
        key_condition &= Key("created_at").gte(created_from)
    elif created_to:
        key_condition &= Key("created_at").lte(created_to)

    filter_expression = None
    if tag:
        filter_expression = Attr("tags").contains(tag)
    if content_type:
        content_expr = Attr("content_type").eq(content_type)
        filter_expression = content_expr if filter_expression is None else filter_expression & content_expr

    params: Dict[str, Any] = {
        "KeyConditionExpression": key_condition,
        "Limit": limit,
        "ScanIndexForward": False,
    }
    if filter_expression is not None:
        params["FilterExpression"] = filter_expression
    if last_evaluated_key:
        params["ExclusiveStartKey"] = last_evaluated_key

    response = images_table().query(**params)
    return response.get("Items", []), response.get("LastEvaluatedKey")

