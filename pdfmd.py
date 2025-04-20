#!/usr/bin/env python
import os
import time
import requests
import click
from dotenv import load_dotenv  # load .env for environment variables
from utils.aws_utils import s3_upload
from utils.azure_ai_utils import azure_ai_pdfmd

load_dotenv()

# AWS S3 bucket for uploads
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")


@click.command()
@click.option(
    "-i",
    "--input",
    "input_path",
    required=True,
    help="Input PDF file path",
)
def main(input_path):
    click.echo("[INFO] Starting PDF to Markdown conversion...")

    # derive output markdown path
    base, _ = os.path.splitext(input_path)
    output_path = f"{base}_pdfmd.md"

    if not AWS_S3_BUCKET:
        click.echo("[ERROR] AWS_S3_BUCKET environment variable must be set.")
        return

    # upload and verify PDF on S3
    pdf_url = s3_upload(input_path, AWS_S3_BUCKET)

    # analyze via Azure and generate markdown
    try:
        result_path = azure_ai_pdfmd(pdf_url, output_path)
    except Exception as e:
        click.echo(f"[ERROR] {e}")
        return
    click.echo(f"[INFO] Markdown saved to: {result_path}")


if __name__ == "__main__":
    main()
