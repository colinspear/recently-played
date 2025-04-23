import json
import boto3
from io import BytesIO

GENRE_CACHE_KEY = "internal/genre_cache.json"

def load_genre_cache(bucket):
    s3 = boto3.client("s3")
    try:
        obj = s3.get_object(Bucket=bucket, Key=GENRE_CACHE_KEY)
        return json.load(obj["Body"])
    except s3.exceptions.NoSuchKey:
        return {}

def save_genre_cache(cache, bucket):
    s3 = boto3.client("s3")
    data = json.dumps(cache).encode("utf-8")
    s3.upload_fileobj(BytesIO(data), bucket, GENRE_CACHE_KEY)

