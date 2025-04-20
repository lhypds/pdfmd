#!/usr/bin/env python
import os
import click
from utils.azure_ai_utils import azure_ai_pdfmd
from utils.pdfplumber_utils import pdfplumber_pdfmd


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
    type=click.Choice(["azureai", "pdfplumber"], case_sensitive=False),
    default="azureai",
    help="Extraction engine: azureai (default) or pdfplumber",
)
def main(input_path, engine):
    click.echo("[INFO] Starting PDF to Markdown conversion...")

    # derive output markdown path
    base, _ = os.path.splitext(input_path)
    output_path = f"{base}_pdfmd.md"

    try:
        # choose extraction engine
        if engine.lower() == "azureai":
            click.echo("[INFO] Using Azure AI for extraction...")
            result_path = azure_ai_pdfmd(input_path, output_path)

        if engine.lower() == "pdfplumber":
            click.echo("[INFO] Using pdfplumber for extraction...")
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
