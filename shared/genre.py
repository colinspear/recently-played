import requests
import os
import time

def get_spotify_token(client_id=None, client_secret=None):
    client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret)
    )
    r.raise_for_status()
    return r.json().get("access_token")

def fetch_artist_genres(artist_uris, token):
    headers = {"Authorization": f"Bearer {token}"}
    genre_map = {}
    for uri in artist_uris:
        artist_id = uri.split(":")[-1]
        url = f"https://api.spotify.com/v1/artists/{artist_id}"
        for attempt in range(3):
            try:
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                genres = res.json().get("genres", [])
                genre_map[uri] = ", ".join(genres) if genres else "Unknown"
                break  # success
            except requests.exceptions.RequestException as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)  # exponential backoff
                else:
                    print(f"Failed to fetch {uri}: {e}")
                    genre_map[uri] = "Unknown"
    return genre_map
