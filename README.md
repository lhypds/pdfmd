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


Notes
-----

- Progress bar is displayed during analysis.
- Requires an Azure Document Intelligence resource with the `prebuilt-layout` model.
