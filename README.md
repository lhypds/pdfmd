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

```bash
python pdfmd.py -i input.pdf [-c]
```

Cropping Option  
Use `-c, --crop` to interactively select and redact areas before conversion:

```bash
python pdfmd.py -i input.pdf -c
```
- Selections are exported as numbered PNGs (`1.png`, `2.png`, …).
- The redacted PDF used for conversion is `<input_basename>_pdfcrop.pdf`.
- The preview defaults to 2× zoom (render ~144 dpi). You can change page or zoom via the standalone tool CLI.

Standalone Crop Tool

Run `pdfcrop.py` independently to select, crop, and redact:
```bash
python pdfcrop.py -i input.pdf [--page N] [--zoom Z]
```
- `-i/--input`: source PDF (required)
- Selections always export as `1.png`, `2.png`, …
- `--page N`: zero‑based page index (default: 0, rarely used)
- `--zoom Z`: rendering zoom factor (default: 2.0)


Notes
-----

- Progress bar is displayed during analysis.
- Requires an Azure Document Intelligence resource with the `prebuilt-layout` model.
