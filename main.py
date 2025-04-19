#!/usr/bin/env python
import os
import sys
import subprocess
import click
import fitz
import glob
import re  # for sorting markdown files


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
def main(input_pdf, crop):
    """Crop all pages (if requested) then convert to Markdown."""
    # Cleanup previous output files
    click.echo("[INFO] Cleaning up previous output files...")
    cleanup_patterns = ["*.png", "*_pdfcrop_*.pdf", "*_pdfmd.md"]
    for pattern in cleanup_patterns:
        for f in glob.glob(pattern):
            try:
                os.remove(f)
                click.echo(f"  Removed: {f}")
            except OSError as e:
                click.echo(f"  Error removing {f}: {e}", err=True)

    base = os.path.splitext(os.path.basename(input_pdf))[0]
    scripts_dir = os.path.dirname(__file__)
    if crop:
        click.echo("[INFO] Counting pages via PyMuPDF...")
        doc = fitz.open(input_pdf)
        num_pages = doc.page_count
        doc.close()
        click.echo(f"[INFO] PDF has {num_pages} pages.")
        cropped_pdfs = []

        # Phase 1: crop pages
        for i in range(1, num_pages + 1):
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

        # Phase 2: convert cropped PDFs to Markdown
        # Confirm before proceeding to Phase 2
        if not click.confirm(
            "[CONFIRM] Proceed to Phase 2: convert cropped PDFs to Markdown?",
            default=True,
        ):
            click.echo("[ABORT] Phase 2 cancelled. Exiting.")
            sys.exit(0)
        click.echo("[INFO] Phase 2: converting cropped PDFs to Markdown...")
        for pdf in cropped_pdfs:
            click.echo(f"[INFO] Converting {pdf} to Markdown...")
            md_cmd = [
                sys.executable,
                os.path.join(scripts_dir, "pdfmd.py"),
                "-i",
                pdf,
            ]
            subprocess.run(md_cmd, check=True)

        # Phase 3: combine Markdown files
        # Confirm before proceeding to Phase 3
        if click.confirm(
            "[CONFIRM] Phase 2 complete. Proceed to Phase 3: combine Markdown files?",
            default=True,
        ):
            click.echo("[INFO] Phase 3: combining Markdown files...")
            # collect and sort markdown files by page index
            md_files = sorted(
                glob.glob("*_pdfmd.md"),
                key=lambda x: int(re.search(r"_pdfcrop_(\d+)_pdfmd\.md$", x).group(1)),
            )
            combined = f"{base}_combined.md"
            with open(combined, "w", encoding="utf-8") as fout:
                for md in md_files:
                    click.echo(f"[INFO] Adding {md} to {combined}")
                    with open(md, "r", encoding="utf-8") as fin:
                        fout.write(fin.read())
                        fout.write("\n\n")
            click.echo(f"[INFO] Combined Markdown saved as {combined}")

    else:
        click.echo(f"[INFO] Converting {input_pdf} to Markdown...")
        md_cmd = [
            sys.executable,
            os.path.join(scripts_dir, "pdfmd.py"),
            "-i",
            input_pdf,
        ]
        subprocess.run(md_cmd, check=True)

    print("[INFO] All done!")


if __name__ == "__main__":
    main()
