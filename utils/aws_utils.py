import os
import boto3
import requests
import click
import sys  # exit on errors


def s3_upload(input_path: str, bucket: str, expiration: int = 3600) -> str:
    """Upload a file to S3, generate presigned URL, verify accessibility, and return URL."""
    click.echo(f"[INFO] Uploading {input_path} to S3 bucket {bucket}...")
    s3 = boto3.client("s3")
    key = os.path.basename(input_path)
    s3.upload_file(input_path, bucket, key)
    file_url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expiration
    )
    click.echo(f"[INFO] Uploaded file URL: {file_url}")
    click.echo("[INFO] Verifying uploaded file URL accessibility via GET...")
    try:
        resp = requests.get(file_url, stream=True)
        resp.raise_for_status()
    except Exception as e:
        click.echo(f"[ERROR] Unable to access file URL: {e}")
        sys.exit(1)
    click.echo("[INFO] file URL is accessible.")
    resp.close()
    return file_url
