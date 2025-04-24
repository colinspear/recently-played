# Recently Played: Personal Spotify Listening Dashboard

This project is a serverless pipeline and dashboard that tracks personal Spotify listening history. It includes:

- AWS Lambda functions for ingestion, enrichment, and transformation
- S3 for storage, caching, and public delivery
- A Streamlit dashboard hosted on Streamlit Cloud
- Daily automation with CloudWatch Events and GitHub Actions
- Optional local development workflows

## Architecture Overview

1. **Data Ingestion (Lambda)**  
   The `fetch_recent_plays` Lambda pulls recent listening data from the Spotify API and stores it in a private S3 bucket as raw `.json`. This function runs daily via CloudWatch.

2. **Data Processing (Lambda)**  
   The `spotify-recently-played-process-to-csv` Lambda reads new `.json` from S3, extracts structured listening records, enriches them with artist genre metadata, and writes a unified `.csv` to a public S3 bucket.  
   - deduplication based on `played_at`  
   - genre caching and key tracking stored in versioned S3  
   - deployed as a zip built with Docker using AWS base images

3. **Dashboard (Streamlit)**  
   The dashboard reads directly from the public S3 CSV. It displays:
   - daily listening time with weekday benchmarks
   - top artists and tracks (last 30 days)
   - hourly listening patterns
   - genre distribution with mock-enriched labels
   - dashboard-level refresh timestamp synced to GitHub Actions trigger

   Hosted on Streamlit Cloud and updated daily via a no-op commit using GitHub Actions.

## Running Locally

To run the Streamlit app locally:

```bash
cd dashboard/
pip install -r requirements.txt
streamlit run app.py
```

If a local CSV exists at data/processed/listening_data.csv, it will be used. Otherwise, set:

```bash
export LISTENING_CSV_URL=https://<your-bucket>.s3.amazonaws.com/processed/listening_data.csv
```

## Deployment

- Lambda packaging: see build_docker.sh in lambdas/process_to_csv/
- Streamlit Cloud: set LISTENING_CSV_URL as an env var
- Daily redeploy: see .github/workflows/daily-refresh.yml
