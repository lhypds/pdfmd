#!/usr/bin/env python
import os
import fitz  # PyMuPDF
import click


@click.command()
@click.option("-i", "--input", "input_pdf", required=True, help="Input PDF file path")
def main(input_pdf):
    """Split each page of the PDF into its own file."""
    base = os.path.splitext(os.path.basename(input_pdf))[0]
    doc = fitz.open(input_pdf)
    for idx in range(len(doc)):
        single = fitz.open()
        single.insert_pdf(doc, from_page=idx, to_page=idx)
        out_name = f"{base}_pdfsplit_{idx+1}.pdf"
        single.save(out_name)
        single.close()
        click.echo(f"[INFO] Exported page {idx+1} to {out_name}")
    doc.close()


if __name__ == "__main__":
    main()
