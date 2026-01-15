import os

import boto3
import pytest
from moto import mock_dynamodb, mock_s3


@pytest.fixture()
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("IMAGES_BUCKET", "test-images-bucket")
    monkeypatch.setenv("IMAGES_TABLE", "test-images-table")
    monkeypatch.delenv("LOCALSTACK_ENDPOINT", raising=False)
    return os.environ


@pytest.fixture()
def aws_services(aws_env):
    with mock_s3(), mock_dynamodb():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=os.environ["IMAGES_BUCKET"])

        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName=os.environ["IMAGES_TABLE"],
            BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "created_at", "AttributeType": "S"},
                {"AttributeName": "image_id", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "created_at", "KeyType": "RANGE"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "image_id_index",
                    "KeySchema": [{"AttributeName": "image_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        )
        table.wait_until_exists()
        yield

