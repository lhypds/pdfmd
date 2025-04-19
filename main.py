#!/usr/bin/env python
import os
import sys
import subprocess
import fitz  # PyMuPDF
import click
import glob


@click.command()
@click.option("-i", "--input", "input_pdf", required=True, help="Input PDF file path")
@click.option(
    "-c",
    "--crop",
    "crop",
    is_flag=True,
    default=False,
    help="Apply cropping to each page",
)
def main(input_pdf, crop):
    """Split multi-page PDFs, optionally crop each page, then convert each to Markdown."""
    # count pages
    doc = fitz.open(input_pdf)
    page_count = len(doc)
    doc.close()

    # capture base filename for later cleanup
    base = os.path.splitext(os.path.basename(input_pdf))[0]
    # Phase 1: split PDF if multi-page
    if page_count > 1:
        click.echo(f"[INFO] Detected {page_count} pages; splitting PDF...")
        split_cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "pdfsplit.py"),
            "-i",
            input_pdf,
        ]
        subprocess.run(split_cmd, check=True)
        page_files = [f"{base}_pdfsplit_{i}.pdf" for i in range(1, page_count + 1)]
    else:
        page_files = [input_pdf]

    # Phase 2: crop pages if requested
    processing_files = page_files
    if crop:
        click.echo(f"[INFO] Cropping {len(page_files)} pages...")
        cropped_files = []
        for idx, pf in enumerate(page_files, start=1):
            click.echo(f"[INFO] Cropping page {idx} via pdfcrop.py...")
            crop_cmd = [
                sys.executable,
                os.path.join(os.path.dirname(__file__), "pdfcrop.py"),
                "-i",
                pf,
            ]
            subprocess.run(crop_cmd, check=True)
            # rename exported PNGs from 1.png,2.png -> <page>_1.png, etc.
            for img in glob.glob("[0-9]*.png"):
                new_img = f"{idx}_{img}"
                os.rename(img, new_img)
                click.echo(f"[INFO] Renamed {img} to {new_img}")
            base_name = os.path.splitext(os.path.basename(pf))[0]
            cropped_pdf = f"{base_name}_pdfcrop.pdf"
            cropped_files.append(cropped_pdf)
        processing_files = cropped_files

    # Phase 3: convert each file to Markdown
    click.echo(f"[INFO] Ready to convert {len(processing_files)} file(s) to Markdown.")
    if not click.confirm("Proceed with Markdown conversion?", default=True):
        click.echo("[INFO] Aborting and cleaning up generated files...")
        # remove split PDFs
        for f in glob.glob(f"{base}_pdfsplit_*.pdf"):
            os.remove(f)
            click.echo(f"[CLEANUP] Removed {f}")
        # remove cropped PDFs
        for f in glob.glob(f"{base}_pdfcrop.pdf"):
            os.remove(f)
            click.echo(f"[CLEANUP] Removed {f}")
        # remove PNGs
        for f in glob.glob(f"*.png"):
            os.remove(f)
            click.echo(f"[CLEANUP] Removed {f}")
        sys.exit(0)
    for pf in processing_files:
        click.echo(f"[INFO] Converting {pf} to Markdown...")
        md_cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "pdfmd.py"),
            "-i",
            pf,
        ]
        subprocess.run(md_cmd, check=True)


if __name__ == "__main__":
    main()
