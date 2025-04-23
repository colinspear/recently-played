# DEV UTILITY
# This script is no longer used in production. Kept for local testing or reference.

import json
import pandas as pd
from datetime import datetime
from pathlib import Path

def parse_recently_played(json_path: str, output_path: str):
    with open(json_path, 'r') as f:
        data = json.load(f)

    items = data['items']
    records = []

    for item in items:
        track = item['track']
        album = track['album']
        artist = track['artists'][0]  # take first artist

        record = {
            'played_at': item['played_at'],
            'track_name': track['name'],
            'track_uri': track['uri'],
            'artist_name': artist['name'],
            'artist_uri': artist['uri'],
            'album_name': album['name'],
            'album_uri': album['uri'],
            'duration_ms': track['duration_ms'],
            'explicit': track['explicit'],
            'context_type': item.get('context', {}).get('type'),
            'context_uri': item.get('context', {}).get('uri'),
        }

        # convert timestamp for human readability
        record['played_at_local'] = datetime.fromisoformat(record['played_at'].replace('Z', '+00:00'))
        record['date'] = record['played_at_local'].date()
        record['hour'] = record['played_at_local'].hour

        records.append(record)

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"Processed {len(df)} rows to {output_path}")

if __name__ == '__main__':
    # adjust these paths as needed
    input_path = 'data/2025-04-16-164859-recently-played.json'
    output_path = 'data/processed_recently_played.csv'
    parse_recently_played(input_path, output_path)

