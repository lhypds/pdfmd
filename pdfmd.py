#!/usr/bin/env python
import os
import time
import json
import requests
import click
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
API_VERSION = "2024-11-30"
MODEL_ID = "prebuilt-layout"


@click.command()
@click.option("-i", "--input", "input_path", required=True, help="Input PDF file path")
@click.option(
    "-o", "--output", "output_path", required=True, help="Output Markdown file path"
)
def main(input_path, output_path):
    """Convert a PDF to Markdown using Azure Document Intelligence REST API"""
    if not AZURE_ENDPOINT or not AZURE_API_KEY:
        click.echo(
            "Error: AZURE_ENDPOINT and AZURE_API_KEY environment variables must be set."
        )
        return

    # read PDF
    with open(input_path, "rb") as f:
        pdf_data = f.read()

    analyze_url = f"{AZURE_ENDPOINT}/formrecognizer/documentModels/{MODEL_ID}:analyze?api-version={API_VERSION}"

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_API_KEY,
        "Content-Type": "application/pdf",
    }

    # submit request and poll
    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("Analyzing document", start=False)
        progress.start_task(task)

        response = requests.post(analyze_url, headers=headers, data=pdf_data)
        response.raise_for_status()
        operation_location = response.headers.get("Operation-Location")

        # poll
        while True:
            poll = requests.get(
                operation_location, headers={"Ocp-Apim-Subscription-Key": AZURE_API_KEY}
            )
            poll.raise_for_status()
            result = poll.json()
            status = result.get("status")
            if status and status.lower() == "succeeded":
                break
            elif status and status.lower() == "failed":
                click.echo("Analysis failed")
                return
            time.sleep(1)

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
