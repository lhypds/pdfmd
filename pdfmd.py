#!/usr/bin/env python
import os
import click
from dotenv import load_dotenv  # load .env for environment variables
from utils.aws_utils import s3_upload
from utils.azure_ai_utils import azure_ai_pdfmd
from utils.pdfplumber_utils import pdfplumber_pdfmd

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
@click.option(
    "-e",
    "--engine",
    "engine",
    type=click.Choice(["azureai", "plumber"], case_sensitive=False),
    default="azureai",
    help="Extraction engine: azureai (default) or plumber",
)
def main(input_path, engine):
    click.echo("[INFO] Starting PDF to Markdown conversion...")

    # derive output markdown path
    base, _ = os.path.splitext(input_path)
    output_path = f"{base}_pdfmd.md"

    # choose extraction engine
    if engine.lower() == "azureai":
        if not AWS_S3_BUCKET:
            click.echo("[ERROR] AWS_S3_BUCKET environment variable must be set.")
            return

        # upload and verify PDF on S3 for Azure AI
        pdf_url = s3_upload(input_path, AWS_S3_BUCKET)

        # analyze via Azure AI and generate markdown
        try:
            result_path = azure_ai_pdfmd(pdf_url, output_path)
        except Exception as e:
            click.echo(f"[ERROR] {e}")
            return

    if engine.lower() == "plumber":
        click.echo("[INFO] Using pdfplumber for extraction...")
        try:
            result_path = pdfplumber_pdfmd(input_path, output_path)
        except Exception as e:
            click.echo(f"[ERROR] {e}")
            return

    if os.path.exists(result_path):
        click.echo(f"[INFO] Markdown saved to: {result_path}")
    else:
        click.echo("[ERROR] Markdown file not found.")


if __name__ == "__main__":
    main()
