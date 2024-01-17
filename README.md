# Recently played Spotify songs

An app that downloads my most recently played songs on Spotify to an AWS S3 bucket every 12 hours. Built using the AWS Toolkit and SAM CLI.

AWS tools used:

- Lambda (performs extraction and loading)
- S3 (stores extracted data)
- IAM (manages permissions for other AWS services)
- Secrets Manager (stores Spotify API credentials)
- EventBridge Scheduler (schedules runs)
- boto3 AWS Python SDK (retrieves and updates secrets, writes JSON to S3)

This app was built using AWS Toolkit and developed and configured locally. It sends a request to the Spotify API every 12 hours and downloads a JSON object of the songs I have listened to most recently. This is then saved to an S3 bucket which I will be able to process further in the future.

