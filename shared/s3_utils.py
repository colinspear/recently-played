import json
import boto3
from io import BytesIO

def load_seen_keys(bucket, key="internal/seen_s3_keys.json"):
    s3 = boto3.client("s3")
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        return set(json.load(obj["Body"]))
    except s3.exceptions.NoSuchKey:
        return set()

def save_seen_keys(keys, bucket, key="internal/seen_s3_keys.json"):
    s3 = boto3.client("s3")
    data = json.dumps(list(keys)).encode("utf-8")
    s3.upload_fileobj(BytesIO(data), bucket, key)

def filter_new_s3_keys(bucket, prefix="data/", seen_keys=None):
    seen_keys = seen_keys or set()
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    all_keys = set()
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".json"):
                all_keys.add(key)
    return sorted(all_keys - seen_keys)

def update_seen_keys(prev, new, bucket):
    updated = prev.union(new)
    save_seen_keys(updated, bucket)
