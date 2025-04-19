import os
import boto3
import requests
import click
import sys  # exit on errors


def upload_and_verify_pdf(input_path: str, bucket: str, expiration: int = 3600) -> str:
    """Upload a PDF to S3, generate presigned URL, verify accessibility, and return URL."""
    click.echo(f"[INFO] Uploading {input_path} to S3 bucket {bucket}...")
    s3 = boto3.client("s3")
    key = os.path.basename(input_path)
    s3.upload_file(input_path, bucket, key)
    pdf_url = s3.generate_presigned_url(
        'get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=expiration
    )
    click.echo(f"[INFO] Uploaded PDF URL: {pdf_url}")
    click.echo("[INFO] Verifying uploaded PDF URL accessibility via GET...")
    try:
        resp = requests.get(pdf_url, stream=True)
        resp.raise_for_status()
    except Exception as e:
        click.echo(f"[ERROR] Unable to access PDF URL: {e}")
        sys.exit(1)
    click.echo("[INFO] PDF URL is accessible.")
    resp.close()
    return pdf_url
