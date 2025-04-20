import os
import time
import requests
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
)
from utils.aws_utils import s3_upload


# Load env variables
def _load_env():
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


_load_env()

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_ENDPOINT = AZURE_ENDPOINT.rstrip("/") if AZURE_ENDPOINT else None
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")  # S3 bucket for uploading PDFs
API_VERSION = "2024-11-30"
MODEL_ID = "prebuilt-layout"


def azure_ai_pdfmd(pdf_path: str, output_path: str) -> str:
    """
    Upload PDF to S3, analyze via Azure Document Intelligence, and write markdown output.
    Returns the path to the generated markdown file.
    """
    if not AZURE_ENDPOINT or not AZURE_API_KEY or not AWS_S3_BUCKET:
        raise ValueError(
            "AZURE_ENDPOINT and AZURE_API_KEY environment variables must be set."
        )

    # upload and verify PDF on S3
    pdf_url = s3_upload(pdf_path, AWS_S3_BUCKET)

    # prepare analyze endpoint
    analyze_url = (
        f"{AZURE_ENDPOINT}/documentintelligence/documentModels/{MODEL_ID}:analyze"
        f"?_overload=analyzeDocument&api-version={API_VERSION}"
    )
    print(f"[INFO] Sending analyze request to Azure: {analyze_url}")
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_API_KEY,
        "Content-Type": "application/json",
    }
    response = requests.post(analyze_url, headers=headers, json={"urlSource": pdf_url})
    response.raise_for_status()
    operation_location = response.headers.get("Operation-Location")
    print(
        f"[INFO] Analyze operation initiated. Operation-Location: {operation_location}"
    )

    # Poll for results
    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("Analyzing document", start=False)
        progress.start_task(task)
        while True:
            poll = requests.get(
                operation_location, headers={"Ocp-Apim-Subscription-Key": AZURE_API_KEY}
            )
            poll.raise_for_status()
            result = poll.json()
            status = result.get("status")
            print(f"[INFO] Current analysis status: {status}")
            if status and status.lower() == "succeeded":
                print("[INFO] Analysis succeeded.")
                break
            elif status and status.lower() == "failed":
                print("[ERROR] Analysis failed.")
                return output_path
            time.sleep(1)

    # Process results into markdown
    print("[INFO] Parsing analysis result...")
    analyze_result = result.get("analyzeResult", {})
    md = []
    raw_paragraphs = analyze_result.get("paragraphs", [])
    raw_tables = analyze_result.get("tables", [])

    # identify paragraphs included in tables
    table_para_idxs = set()
    for t in raw_tables:
        for cell in t.get("cells", []):
            for elem in cell.get("elements", []):
                if elem.startswith("/paragraphs/"):
                    table_para_idxs.add(int(elem.split("/")[-1]))

    # build items list
    items = []
    for idx, p in enumerate(raw_paragraphs):
        if idx in table_para_idxs:
            continue
        br = p.get("boundingRegions", [{}])[0]
        pg = br.get("pageNumber", 0)
        poly = br.get("polygon", [0, 0])
        items.append((pg, poly[1], poly[0], "para", p))
    for t in raw_tables:
        br = t.get("boundingRegions", [{}])[0]
        pg = br.get("pageNumber", 0)
        poly = br.get("polygon", [0, 0])
        items.append((pg, poly[1], poly[0], "table", t))
    items.sort(key=lambda x: (x[0], x[1], x[2]))

    for _, _, _, kind, obj in items:
        if kind == "para":
            text = obj.get("content", "").strip()
            if text:
                md.append(text)
                md.append("")
        else:
            rows = obj.get("rowCount", 0)
            cols = obj.get("columnCount", 0)
            grid = [["" for _ in range(cols)] for _ in range(rows)]
            for cell in obj.get("cells", []):
                r, c = cell.get("rowIndex"), cell.get("columnIndex")
                content = cell.get("content", "").replace("\n", " ").strip()
                grid[r][c] = content
            md.append("| " + " | ".join(grid[0]) + " |")
            md.append("| " + " | ".join(["---"] * cols) + " |")
            for row in grid[1:]:
                md.append("| " + " | ".join(row) + " |")
            md.append("")

    # Write markdown file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    return output_path
