# Recently Played: Personal Spotify Listening Dashboard

This project is a serverless pipeline and dashboard that tracks personal Spotify listening history. It includes:

- AWS Lambda functions for data ingestion and transformation
- S3 for storage and state management
- A Streamlit dashboard hosted on Streamlit Cloud
- Optional local development workflows

## Architecture Overview

1. **Data Ingestion (Legacy Lambda)**  
   The `fetch_recent_plays_legacy` Lambda pulls recent listening data from the Spotify API and stores it in a private S3 bucket as raw `.json` files. This function runs on a scheduled trigger and is preserved here as a legacy component.

2. **Data Processing (Lambda)**  
   The `spotify-recently-played-process-to-csv` Lambda reads new `.json` files from S3, extracts structured data, enriches it with genre metadata, and writes the processed `.csv` output to a public S3 bucket. Caching for processed files and genres is handled via versioned S3 objects.

3. **Dashboard (Streamlit)**  
   The Streamlit app loads the latest processed data directly from the public S3 bucket and displays listening time trends, top artists, genre insights, and more. The app auto-refreshes based on the pipeline schedule.

## Running Locally

To run the Streamlit app locally:

```bash
cd dashboard/
pip install -r requirements.txt
streamlit run app.py
```

If a local CSV exists at data/processed/listening_data.csv, it will be used. Otherwise, set the environment variable:

```bash
export LISTENING_CSV_URL=https://<your-bucket>.s3.amazonaws.com/processed/listening_data.csv
```

## Deployment

- Lambda Packaging: see build.sh in lambdas/process_to_csv/
- Streamlit Cloud: configured via .streamlit/secrets.toml and environment variables

## Legacy Components

The fetch_recent_plays_legacy function was the original ingestion Lambda used to retrieve recent Spotify listening history and push it to S3. While it is no longer actively developed, it remains a core upstream component of the pipeline and is preserved here for completeness.
