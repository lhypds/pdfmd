#!/usr/bin/env python
import os
import sys
import subprocess
import click


@click.command()
@click.option("-i", "--input", "input_pdf", required=True, help="Input PDF file path")
@click.option(
    "-c",
    "--crop",
    "crop",
    is_flag=True,
    default=False,
    help="Crop PDF image area before processing",
)
@click.option(
    "--page",
    "page",
    type=int,
    default=0,
    help="Page index (0-based) to crop; only relevant with -c",
)
def main(input_pdf, crop, page):
    """Crop the specified page (if requested) then convert to Markdown."""
    base = os.path.splitext(os.path.basename(input_pdf))[0]
    # Determine source PDF for Markdown conversion
    target_pdf = input_pdf
    if crop:
        click.echo(f"[INFO] Cropping page {page} via pdfcrop.py...")
        crop_cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "pdfcrop.py"),
            "-i",
            input_pdf,
            "--page",
            str(page),
        ]
        subprocess.run(crop_cmd, check=True)
        target_pdf = f"{base}_pdfcrop.pdf"
    click.echo(f"[INFO] Converting {target_pdf} to Markdown...")
    md_cmd = [
        sys.executable,
        os.path.join(os.path.dirname(__file__), "pdfmd.py"),
        "-i",
        target_pdf,
    ]
    subprocess.run(md_cmd, check=True)


if __name__ == "__main__":
    main()
