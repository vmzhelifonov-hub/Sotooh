import os
import time

os.environ["AWS_EC2_METADATA_DISABLED"] = "true"

import django

django.setup()

import boto3
from botocore.client import Config
from django.conf import settings

t0 = time.time()
client = boto3.client(
    "s3",
    endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
    config=Config(signature_version="s3v4", connect_timeout=3, read_timeout=5, retries={"max_attempts": 2}),
)
t1 = time.time()
print("client create:", round(t1 - t0, 2), "s")

t2 = time.time()
client.upload_fileobj(__import__("io").BytesIO(b"x" * 20000), settings.AWS_STORAGE_BUCKET_NAME, "dbg/boto.bin")
t3 = time.time()
print("upload:", round(t3 - t2, 2), "s")

t4 = time.time()
url = client.generate_presigned_url("get_object", Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": "dbg/boto.bin"}, ExpiresIn=3600)
t5 = time.time()
print("presigned url:", round(t5 - t4, 2), "s")
