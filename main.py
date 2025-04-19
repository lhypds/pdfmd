#!/usr/bin/env python
import os
import sys
import subprocess
from time import sleep
import click
import fitz
import glob
import re  # for sorting markdown files


@click.command()
@click.option(
    "-i",
    "--input",
    "input_pdfs",
    required=True,
    multiple=True,
    help="Input PDF file path(s) or folder(s)",
)
@click.option(
    "-c",
    "--crop",
    "crop",
    is_flag=True,
    default=False,
    help="Crop PDF image area before processing",
)
def main(input_pdfs, crop):
    """Crop all pages (if requested) then convert to Markdown for multiple PDFs or folders."""
    # Expand input_pdfs: if any entry is a directory, add all PDFs in that directory
    expanded_inputs = []

    for inp in input_pdfs:
        if os.path.isdir(inp):
            pdfs = sorted(glob.glob(os.path.join(inp, "*.pdf")))
            if not pdfs:
                click.echo(f"[WARN] No PDFs found in folder: {inp}")
            expanded_inputs.extend(pdfs)
        else:
            expanded_inputs.append(inp)

    for input_pdf in expanded_inputs:
        click.echo(f"[INFO] Processing: {input_pdf}")
        base = os.path.splitext(os.path.basename(input_pdf))[0]
        scripts_dir = os.path.dirname(__file__)

        # Phase 1: Split pages
        splited_pdfs = []
        if crop:
            click.echo("[INFO] Counting pages via PyMuPDF...")
            doc = fitz.open(input_pdf)
            num_pages = doc.page_count
            doc.close()
            click.echo(f"[INFO] PDF has {num_pages} pages.")
            cropped_pdfs = []

            for i in range(1, num_pages + 1):
                # Check the pdfcrop file exists, if exists, skip the cropping
                out_pdf = f"{base}_pdfcrop_{i}.pdf"
                if os.path.isfile(out_pdf):
                    click.echo(f"[INFO] Cropped PDF already exists: {out_pdf}")
                    cropped_pdfs.append(out_pdf)
                    continue

                click.echo(f"[INFO] Cropping page {i} via pdfcrop.py...")
                crop_cmd = [
                    sys.executable,
                    os.path.join(scripts_dir, "pdfcrop.py"),
                    "-i",
                    input_pdf,
                    "--page",
                    str(i),
                ]
                subprocess.run(crop_cmd, check=True)
                # pdfcrop.py already names output as <base>_pdfcrop_<page>.pdf
                out_pdf = f"{base}_pdfcrop_{i}.pdf"
                cropped_pdfs.append(out_pdf)
                splited_pdfs = sorted(cropped_pdfs)

        else:
            # Split input PDF into single page PDF with pdfsplit.py
            click.echo("[INFO] Splitting PDF via pdfsplit.py...")
            split_cmd = [
                sys.executable,
                os.path.join(scripts_dir, "pdfsplit.py"),
                "-i",
                input_pdf,
            ]
            subprocess.run(split_cmd, check=True)

            # pdfsplit.py names output as <base>_pdfsplit_<page>.pdf
            # Collect all split PDFs
            splited_pdfs = sorted(
                glob.glob(f"{base}_pdfsplit_*.pdf"),
                key=lambda x: int(re.search(r"_pdfsplit_(\d+)\.pdf$", x).group(1)),
            )
            click.echo(f"[INFO] Split PDFs: {splited_pdfs}")

        # Phase 2: convert cropped PDFs to Markdown
        # Confirm before proceeding to Phase 2
        if not click.confirm(
            f"[CONFIRM] Proceed to Phase 2: convert cropped PDFs to Markdown for {input_pdf}?",
            default=True,
        ):
            click.echo("[ABORT] Phase 2 cancelled. Exiting.")
            sys.exit(0)
        click.echo("[INFO] Phase 2: converting cropped PDFs to Markdown...")
        for pdf in splited_pdfs:
            # Retry loop on conversion failure
            while True:
                click.echo(
                    f"[INFO] Converting {pdf} to Markdown... (waiting 30s to avoid rate limit)"
                )
                sleep(30)
                md_cmd = [
                    sys.executable,
                    os.path.join(scripts_dir, "pdfmd.py"),
                    "-i",
                    pdf,
                ]
                try:
                    subprocess.run(md_cmd, check=True)
                    break  # success, move to next PDF
                except Exception as e:
                    click.echo(
                        f"ERROR: Failed to convert {pdf} to Markdown. Reason: {e}",
                        err=True,
                    )
                    # Prompt to retry or abort
                    if click.confirm("Retry conversion of this file?", default=False):
                        continue
                    else:
                        click.echo("Aborting Phase 2.")
                        sys.exit(1)

        # Phase 3: combine Markdown files
        # Confirm before proceeding to Phase 3
        if click.confirm(
            f"[CONFIRM] Phase 2 complete. Proceed to Phase 3: combine Markdown files for {input_pdf}?",
            default=True,
        ):
            click.echo("[INFO] Phase 3: combining Markdown files...")
            # collect and sort markdown files by page index
            md_files = sorted(
                glob.glob("*_pdfmd.md"),
                key=lambda x: int(re.search(r"_pdfcrop_(\d+)_pdfmd\.md$", x).group(1)),
            )
            combined = f"{base}_pdfmd.md"
            with open(combined, "w", encoding="utf-8") as fout:
                for md in md_files:
                    click.echo(f"[INFO] Adding {md} to {combined}")
                    with open(md, "r", encoding="utf-8") as fin:
                        fcontent = fin.read()

                        # Trim some unnecessarey text
                        # Remove ":unselected:" and ":selected:"
                        fcontent = re.sub(r":unselected:|:selected:", "", fcontent)

                        fout.write(fcontent)
                        fout.write("\n\n")
            click.echo(f"[INFO] Combined Markdown saved as {combined}")
        else:
            click.echo("[ABORT] Phase 3 cancelled.")

    print("[INFO] All done!")


if __name__ == "__main__":
    main()
