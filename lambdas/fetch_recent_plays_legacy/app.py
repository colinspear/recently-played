import base64
import json
from datetime import datetime
from pathlib import Path

import requests
import boto3

LOCAL_FILE_SYS = "/tmp"
S3_BUCKET = "spotify-data-1204198333"

s3_client = boto3.client("s3")
secrets_client = boto3.client('secretsmanager')

username = 'colinspear1'
scope = 'user-read-recently-played'
secret_name = "spotify-data/recently-played"
region = "us-east-1"


def get_secret(secret_name, region):
    """Retrieve a secret from AWS Secrets Manager."""
    client = boto3.client('secretsmanager', region)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        raise e
    else:
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return json.loads(secret)  # Assuming the secret is stored as a JSON string
        else:
            raise Exception("Secret not found or not in expected format")


def update_secret(secret_name, new_secret_values):
    """Update a secret in AWS Secrets Manager."""
    client = boto3.client('secretsmanager')
    
    try:
        update_secret_response = client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(new_secret_values)
        )
    except Exception as e:
        print(f"Error updating secret: {e}")
        raise e
    else:
        return update_secret_response  # Contains information about the updated secret


def is_token_expired(access_token):
    """Check if the current access token is expired."""
    test_url = "https://api.spotify.com/v1/me/player/recently-played"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(test_url, headers=headers)
    return response.status_code == 401  # 401 status code indicates an expired or invalid token


def refresh_access_token(refresh_token, client_id, client_secret):
    """Refresh the access token using the refresh token."""
    token_url = 'https://accounts.spotify.com/api/token'
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    headers = {
        'Authorization': f'Basic {base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()}'
    }

    response = requests.post(token_url, data=payload, headers=headers)

    if response.status_code == 200:
        new_token_info = response.json()
        return new_token_info
    else:
        # TODO: Handle error (e.g., log it, raise an exception)
        return None


def get_songs(access_token, client_id, client_secret):
    """Fetch songs, refresh token if expired."""

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "limit": 50
    }

    response = requests.get(
        "https://api.spotify.com/v1/me/player/recently-played", 
        headers=headers,
        params=params
        )

    if response.status_code != 200:
        print(f"Error in API request: {response.status_code}", response.json())
        return None

    return response.json()  # Assuming a successful response returns JSON


def _get_time():
    now = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    return now


def write_to_local(data, time, loc="/tmp"):
    with open(f'{loc}/{time}-recently-played.json', 'w') as d:
        json.dump(data, d)
    

def lambda_handler(event, context):
    time = _get_time()
    secrets = get_secret(secret_name, region)

    client_id = secrets["CLIENT_ID"]
    client_secret = secrets["CLIENT_SECRET"]
    access_token = secrets["ACCESS_TOKEN"]
    refresh_token = secrets["REFRESH_TOKEN"]

    if is_token_expired(access_token):
        print("Token expired, refreshing...")
        new_token_info = refresh_access_token(refresh_token, client_id, client_secret)

        if not new_token_info:
            raise Exception("Failed to refresh token")
        
        key_values = {
            'CLIENT_ID': client_id,
            'CLIENT_SECRET': client_secret,
            'ACCESS_TOKEN': new_token_info['access_token'],
            'REFRESH_TOKEN': refresh_token
        }
        update_secret(secret_name, key_values)
        
        access_token = new_token_info['access_token']

    data = get_songs(access_token, client_id=client_id, client_secret=client_secret)
    write_to_local(data, time, loc=LOCAL_FILE_SYS)
    files = Path(LOCAL_FILE_SYS).glob("*recently-played.json")
    for f in files:
        s3_client.upload_file(str(f), S3_BUCKET, "data/" + str(f.name))
        