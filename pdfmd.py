#!/usr/bin/env python
import os
import time
import json
import requests
import click
import boto3  # AWS S3 client
from dotenv import load_dotenv  # load .env for environment variables

load_dotenv()
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
)

# Azure Document Intelligence REST API configuration
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
# normalize endpoint to avoid double slashes
AZURE_ENDPOINT = AZURE_ENDPOINT.rstrip("/") if AZURE_ENDPOINT else None
API_VERSION = "2024-11-30"
MODEL_ID = "prebuilt-layout"

# AWS S3 bucket for uploads
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")


@click.command()
@click.option("-i", "--input", "input_path", required=True, help="Input PDF file path")
@click.option(
    "-o", "--output", "output_path", required=True, help="Output Markdown file path"
)
def main(input_path, output_path):
    click.echo("[INFO] Starting PDF to Markdown conversion...")
    if not AZURE_ENDPOINT or not AZURE_API_KEY:
        click.echo(
            "Error: AZURE_ENDPOINT and AZURE_API_KEY environment variables must be set."
        )
        return

    if not AWS_S3_BUCKET:
        click.echo("[ERROR] AWS_S3_BUCKET environment variable must be set.")
        return

    # upload PDF to S3
    click.echo(f"[INFO] Uploading {input_path} to S3 bucket {AWS_S3_BUCKET}...")
    s3 = boto3.client("s3")
    key = os.path.basename(input_path)
    s3.upload_file(input_path, AWS_S3_BUCKET, key)
    # generate presigned URL for the uploaded PDF
    pdf_url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": AWS_S3_BUCKET, "Key": key}, ExpiresIn=3600
    )
    click.echo(f"[INFO] Uploaded PDF URL: {pdf_url}")

    click.echo("[INFO] Verifying uploaded PDF URL accessibility via GET...")
    try:
        resp = requests.get(pdf_url, stream=True)
        resp.raise_for_status()
        click.echo("[INFO] PDF URL is accessible.")
        resp.close()
    except Exception as e:
        click.echo(f"[ERROR] Unable to access PDF URL: {e}")
        return

    # analyze via URL source
    analyze_url = f"{AZURE_ENDPOINT}/documentintelligence/documentModels/{MODEL_ID}:analyze?_overload=analyzeDocument&api-version={API_VERSION}"
    click.echo(f"[INFO] Sending analyze request to Azure: {analyze_url}")
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_API_KEY,
        "Content-Type": "application/json",
    }
    response = requests.post(analyze_url, headers=headers, json={"urlSource": pdf_url})
    response.raise_for_status()
    operation_location = response.headers.get("Operation-Location")
    click.echo(
        f"[INFO] Analyze operation initiated. Operation-Location: {operation_location}"
    )

    # submit request and poll
    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("Analyzing document", start=False)
        progress.start_task(task)

        click.echo("[INFO] Polling analysis status...")
        while True:
            poll = requests.get(
                operation_location, headers={"Ocp-Apim-Subscription-Key": AZURE_API_KEY}
            )
            poll.raise_for_status()
            result = poll.json()
            status = result.get("status")
            click.echo(f"[INFO] Current analysis status: {status}")
            if status and status.lower() == "succeeded":
                click.echo("[INFO] Analysis succeeded.")
                break
            elif status and status.lower() == "failed":
                click.echo("[ERROR] Analysis failed.")
                return
            time.sleep(1)

    click.echo("[INFO] Parsing analysis result...")
    analyze_result = result.get("analyzeResult", {})
    md = []

    # paragraphs
    paragraphs = analyze_result.get("paragraphs", [])
    for p in paragraphs:
        text = p.get("content", "").strip()
        if text:
            md.append(text)
            md.append("")

    # tables
    tables = analyze_result.get("tables", [])
    for table in tables:
        rows = table.get("rowCount", 0)
        cols = table.get("columnCount", 0)
        # initialize empty table grid
        grid = [["" for _ in range(cols)] for _ in range(rows)]
        for cell in table.get("cells", []):
            r = cell.get("rowIndex")
            c = cell.get("columnIndex")
            content = cell.get("content", "").strip()
            grid[r][c] = content
        # header row
        header = "| " + " | ".join(grid[0]) + " |"
        separator = "| " + " | ".join(["---"] * cols) + " |"
        md.append(header)
        md.append(separator)
        for row in grid[1:]:
            md.append("| " + " | ".join(row) + " |")
        md.append("")

    # write markdown
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


if __name__ == "__main__":
    main()
