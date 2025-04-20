![ChatGPT Image Apr 20, 2025, 05_19_22 AM](https://github.com/user-attachments/assets/a701d46a-5c8b-4246-946f-6c67992f60c0)

pdfmd
=====

This tool uses Azure AI Document Intelligence to extract and convert text and tables from PDFs into Markdown, and crops images within the PDF—all optimized for input into generative AI systems.


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

Crop remove images in PDF (and save) and convert to Markdown:  

```bash
python main.py -i input.pdf -c
```

- `-c` for enable crop, if no image in file no need crop.  
- `-i` for input file. Input can be multiple files or folder. If input is a folder it will loop all PDFs in the folder.  
- The output will be a Markdown file with many PNG files.  
- This can be used as generative AI's input.  

Modules

1. pdfmd.py  

Input file must be single page PDF, if it is multiple pages, it will only process the first page.  
Convert a PDF to Markdown:

```bash
python pdfmd.py -i input.pdf
```

- `-i` can only process single PDF file.  

Output file (single): `<input_basename>_pdfmd.md`  

2. pdfcrop.py  

Crop area to remove (press Ctrl) or corp to both remove and save as PNG, output crop removed PDF:  

```bash
python pdfcrop.py -i input.pdf --page 1
```

It will popup a window let user crop areas, if crop it will remove the area and save as PNG.  
If use Ctrl will just delete the area. This can be used to remove unnecessary part in PDF.  
Use Ctrl + Z to undo crop.  
Crop output is single page PDF.  

- `-i/--input`: source PDF (required)  
- `--page N`: 1‑based page index (required)  
- Zoom level is now read from the `PDFCROP_ZOOM_LEVEL` environment variable (set in `.env`; default 2).  

Output PDF file (single): `<input_basename>_pdfcrop_<page>.pdf`  
Output PNG files (multiple): `<input_basename>_pdfcrop_<page>_<index>.png`  

3. excelpdf.py  

Convert Excel to PDFs, one sheet one PDF file.  

```bash
python excelpdf.py -i input.xslx
```

Output file (multiple): `<input_basename>_excelpdf_<sheet>.pdf`  

4. pdfsplit.py

Splitting multple page PDF to single page PDFs.  

Run `pdfsplit.py` to split each page of a PDF into its own file:
```bash
python pdfsplit.py -i input.pdf
```

- `-i/--input`: source PDF file path (required)

Output file (multiple): `<input_basename>_pdfsplit_<page>.pdf`  


Notes
-----

- Progress bar is displayed during analysis.
- Requires an Azure Document Intelligence resource with the `prebuilt-layout` model.
