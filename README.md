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
   PDFCROP_ZOOM_LEVEL=2
   ```


Usage
-----

Split, crop PDF and convert to Markdown:

```bash
python main.py -i input.pdf -c
```

Convert a PDF to Markdown:

```bash
python pdfmd.py -i input.pdf
```

The PDF converter will only take care the 1st page of the input PDF ifle.

Crop Tool

Run `pdfcrop.py` independently to select, crop, and redact:

```bash
python pdfcrop.py -i input.pdf --page 1
```

It will popup a window let user crop areas, if crop it will delete the area and save as <page>_<crop_id>.png.
If use Ctrl will just delete the area, this can be used to remove unnecessary part.
Use Ctrl + Z to undo crop.

- `-i/--input`: source PDF (required)
- `--page N`: 1‑based page index (required)
- Selections always export as `1.png`, `2.png` ...
- Zoom level is now read from the `PDFCROP_ZOOM_LEVEL` environment variable (set in `.env`; default 2).


Notes
-----

- Progress bar is displayed during analysis.
- Requires an Azure Document Intelligence resource with the `prebuilt-layout` model.
