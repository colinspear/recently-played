import os
import json
import pandas as pd
import boto3
from io import StringIO

from shared.s3_utils import load_seen_keys, filter_new_s3_keys, update_seen_keys
from shared.genre import get_spotify_token, fetch_artist_genres
from shared.genre_cache import load_genre_cache, save_genre_cache

SOURCE_BUCKET = os.environ["SOURCE_BUCKET"]
DEST_BUCKET = os.environ["DEST_BUCKET"]
DEST_KEY = "processed/listening_data.csv"

s3 = boto3.client("s3")

def read_raw_json():
    seen_keys = load_seen_keys(SOURCE_BUCKET)
    new_keys = filter_new_s3_keys(SOURCE_BUCKET, seen_keys=seen_keys)
    records = []

    for key in new_keys:
        try:
            body = s3.get_object(Bucket=SOURCE_BUCKET, Key=key)["Body"].read()
            payload = json.loads(body)
            for item in payload.get("items", []):
                track = item["track"]
                artist = track["artists"][0]
                album = track["album"]
                records.append({
                    "played_at": item["played_at"],
                    "track_name": track["name"],
                    "track_uri": track["uri"],
                    "artist_name": artist["name"],
                    "artist_uri": artist["uri"],
                    "album_name": album["name"],
                    "album_uri": album["uri"],
                    "duration_ms": track["duration_ms"],
                    "explicit": track["explicit"],
                    "context_type": item["context"]["type"] if item.get("context") else None,
                    "context_uri": item["context"]["uri"] if item.get("context") else None,
                })
        except Exception as e:
            print(f"Failed to process {key}: {e}")

    if new_keys:
        update_seen_keys(seen_keys, set(new_keys), SOURCE_BUCKET)

    return pd.DataFrame(records).drop_duplicates(subset="played_at")


def process_data(df):
    df["played_at_local"] = pd.to_datetime(df["played_at"], utc=True, format="ISO8601")
    df["date"] = df["played_at_local"].dt.date
    df["hour"] = df["played_at_local"].dt.hour

    # genre enrichment
    token = get_spotify_token()
    genre_cache = load_genre_cache(SOURCE_BUCKET)
    unique_uris = df["artist_uri"].unique()
    missing_uris = [uri for uri in unique_uris if uri not in genre_cache]

    if missing_uris:
        fresh = fetch_artist_genres(missing_uris, token)
        genre_cache.update(fresh)
        save_genre_cache(genre_cache, SOURCE_BUCKET)

    df["genre"] = df["artist_uri"].map(genre_cache)
    return df
    

def append_to_existing(df_new):
    try:
        obj = s3.get_object(Bucket=DEST_BUCKET, Key=DEST_KEY)
        df_existing = pd.read_csv(obj["Body"], parse_dates=["played_at_local"])
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    except s3.exceptions.NoSuchKey:
        df_combined = df_new

    # deduplicate by played_at
    df_combined = (
        df_combined
        .drop_duplicates(subset="played_at")
        .sort_values("played_at_local")
        .reset_index(drop=True)
    )

    return df_combined


def save_to_s3(df, bucket=DEST_BUCKET, key=DEST_KEY):
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())
    print(f"[upload] wrote {len(df)} rows to s3://{bucket}/{key}")


def handler(event=None, context=None):
    df = read_raw_json()
    if df.empty:
        print("No new data to process.")
        return {"rows": 0, "status": "noop"}

    new_df = process_data(df)
    df = append_to_existing(new_df)
    save_to_s3(df)
    return {"rows": len(df), "status": "ok"}


if __name__ == "__main__":
    print(handler())
