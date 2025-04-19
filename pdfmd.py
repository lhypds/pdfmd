#!/usr/bin/env python
import os
import time
import json
import requests
import click
import glob  # for cleanup of temporary files
from dotenv import load_dotenv  # load .env for environment variables
from utils.aws_utils import upload_and_verify_pdf
from pdfcrop import select_and_redact

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
    "-c",
    "--crop",
    "crop",
    is_flag=True,
    default=False,
    help="Crop PDF image area before processing",
)
def main(input_path, crop):
    click.echo("[INFO] Starting PDF to Markdown conversion...")
    # derive output markdown path
    base, _ = os.path.splitext(input_path)
    output_path = f"{base}_pdfmd.md"
    # Remove existing markdown output to avoid stale content
    if os.path.exists(output_path):
        os.remove(output_path)
    if crop:
        base, _ = os.path.splitext(input_path)
        cropped_pdf = f"{base}_pdfcrop.pdf"
        cropped_img = f"{base}_crop.png"
        click.echo(f"[INFO] Cropping PDF: {input_path} -> {cropped_pdf}")
        img_paths = select_and_redact(input_path, cropped_pdf, cropped_img)
        click.echo(f"[INFO] Using cropped PDF for processing: {cropped_pdf}")
        input_path = cropped_pdf
    if not AZURE_ENDPOINT or not AZURE_API_KEY:
        click.echo(
            "Error: AZURE_ENDPOINT and AZURE_API_KEY environment variables must be set."
        )
        return

    if not AWS_S3_BUCKET:
        click.echo("[ERROR] AWS_S3_BUCKET environment variable must be set.")
        return

    # upload and verify PDF on S3
    pdf_url = upload_and_verify_pdf(input_path, AWS_S3_BUCKET)

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
    raw_paragraphs = analyze_result.get("paragraphs", [])
    raw_tables = analyze_result.get("tables", [])
    # identify paragraphs included in tables
    table_para_idxs = set()
    for t in raw_tables:
        for cell in t.get("cells", []):
            for elem in cell.get("elements", []):
                if elem.startswith("/paragraphs/"):
                    table_para_idxs.add(int(elem.split("/")[-1]))
    # build items list (paragraphs + tables) with positions
    items = []
    for idx, p in enumerate(raw_paragraphs):
        if idx in table_para_idxs:
            continue
        br = p.get("boundingRegions", [{}])[0]
        pg = br.get("pageNumber", 0)
        poly = br.get("polygon", [0, 0])
        items.append((pg, poly[1], poly[0], "para", p))
    for t in raw_tables:
        br = t.get("boundingRegions", [{}])[0]
        pg = br.get("pageNumber", 0)
        poly = br.get("polygon", [0, 0])
        items.append((pg, poly[1], poly[0], "table", t))
    # sort combined items
    items.sort(key=lambda x: (x[0], x[1], x[2]))
    # emit in order
    for _, _, _, kind, obj in items:
        if kind == "para":
            text = obj.get("content", "").strip()
            if text:
                md.append(text)
                md.append("")
        else:  # table
            rows = obj.get("rowCount", 0)
            cols = obj.get("columnCount", 0)
            grid = [["" for _ in range(cols)] for _ in range(rows)]
            for cell in obj.get("cells", []):
                r, c = cell.get("rowIndex"), cell.get("columnIndex")
                grid[r][c] = cell.get("content", "").strip()
            md.append("| " + " | ".join(grid[0]) + " |")
            md.append("| " + " | ".join(["---"] * cols) + " |")
            for row in grid[1:]:
                md.append("| " + " | ".join(row) + " |")
            md.append("")

    # write markdown to derived output path
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    click.echo(f"[INFO] Markdown saved to: {output_path}")
    # Report cropped image outputs in one line
    if crop and img_paths:
        click.echo(f"[INFO] Cropped images saved to: {', '.join(img_paths)}")


if __name__ == "__main__":
    main()
