pdfmd
=====

This tool converts a PDF into Markdown text and tables using Azure AI Document Intelligence.


Setup
-----

1. Create a virtual environment and activate it:

   ```
   python -m venv venv
   venv\Scripts\Activate
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your Azure and AWS configuration:

   ```dotenv
   AZURE_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com
   AZURE_API_KEY=<your-key>
   AWS_S3_BUCKET=<your-bucket-name>
   AWS_ACCESS_KEY_ID=<your-aws-access-key-id>
   AWS_SECRET_ACCESS_KEY=<your-aws-secret-access-key>
   ```


Usage
-----

Convert a PDF to Markdown:

```
python pdfmd.py -i input.pdf -o output.md
```

Cropping Option  
Crop to save and remove images in document.  

```bash
python pdfmd.py -i input.pdf -o output.md -c
```

- Use `-c, --crop` to interactively select and redact one or more areas on the specified PDF page before conversion.
- Each selection is exported as numbered PNGs (`base_1.png`, `base_2.png`, …) and redacted in the output PDF.
- By default the preview uses a 2× zoom (render at about 144 dpi) for a high‑resolution view and precise drawing.  
  You can adjust the zoom or target page by customizing `pdfcrop.py` directly or using its CLI flags.

Standalone Crop Tool

You can run `pdfcrop.py` on its own to interactively select and redact areas from a PDF:
```bash
python pdfcrop.py input.pdf redacted.pdf base.png [--page N] [--zoom Z]
```
- `input.pdf`: source PDF
- `redacted.pdf`: output PDF with white‑boxed redactions
- `base.png`: base filename for exported PNG crops (e.g. `base_1.png`, `base_2.png`, …)
- `--page N`: (optional) zero‑based page index to render (default: 0)
- `--zoom Z`: (optional) rendering zoom factor (default: 2.0)


Notes
-----

- Progress bar is displayed during analysis.
- Requires an Azure Document Intelligence resource with the `prebuilt-layout` model.
