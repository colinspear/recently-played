# DEV UTILITY
# This script is no longer used in production. Kept for local testing or reference.

import boto3
import os

s3 = boto3.client("s3")
bucket = "spotify-data-1204198333"
prefix = "data/"
local_dir = "cached_data"

os.makedirs(local_dir, exist_ok=True)

def download_all():
    objects = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    for obj in objects.get("Contents", []):
        key = obj["Key"]
        if key.endswith(".json"):
            local_path = os.path.join(local_dir, os.path.basename(key))
            if not os.path.exists(local_path):
                print(f"Downloading {key}...")
                body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
                with open(local_path, "wb") as f:
                    f.write(body)
            else:
                print(f"Skipping {key}, already cached")

if __name__ == "__main__":
    download_all()
