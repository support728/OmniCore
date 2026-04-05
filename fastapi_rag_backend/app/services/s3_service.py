import boto3

from fastapi_rag_backend.app.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )


def ensure_bucket() -> None:
    client = get_s3_client()
    buckets = [b["Name"] for b in client.list_buckets().get("Buckets", [])]
    if settings.s3_bucket not in buckets:
        client.create_bucket(Bucket=settings.s3_bucket)


def upload_bytes(file_bytes: bytes, object_key: str, content_type: str) -> None:
    client = get_s3_client()
    client.put_object(
        Bucket=settings.s3_bucket,
        Key=object_key,
        Body=file_bytes,
        ContentType=content_type,
    )


def download_bytes(object_key: str) -> bytes:
    client = get_s3_client()
    obj = client.get_object(Bucket=settings.s3_bucket, Key=object_key)
    return obj["Body"].read()
