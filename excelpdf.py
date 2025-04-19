#!/usr/bin/env python3
import os
import sys
import argparse

try:
    import win32com.client as win32
except ImportError:
    print("pywin32 is required. Install with: pip install pywin32", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Export Excel workbook to PDFs by sheet."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input Excel file path (.xls, .xlsx, .xlsm)",
    )
    args = parser.parse_args()

    input_path = args.input
    if not os.path.isfile(input_path):
        print(f"Error: file {input_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    ext = os.path.splitext(input_path)[1].lower()
    if ext not in [".xls", ".xlsx", ".xlsm"]:
        print(
            "Error: input must be an Excel file (.xls, .xlsx, .xlsm)", file=sys.stderr
        )
        sys.exit(1)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    out_dir = os.path.dirname(os.path.abspath(input_path))
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    # Remove all exported PDF files before exporting
    import glob

    pattern = os.path.join(out_dir, f"{base_name}_*.pdf")
    for old_pdf in glob.glob(pattern):
        try:
            os.remove(old_pdf)
            print(f"Removed old PDF: {old_pdf}")
        except Exception as e:
            print(f"WARNING: Could not remove {old_pdf}: {e}", file=sys.stderr)

    excel = win32.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    # Disable automatic link updates and security prompts
    excel.AskToUpdateLinks = False
    try:
        excel.AutomationSecurity = 3  # msoAutomationSecurityForceDisable
    except Exception:
        pass

    abs_path = os.path.abspath(input_path)
    print(f"Opening workbook: {abs_path}")
    try:
        # Open workbook without flags to see if read-only prevents sheet loading
        wb = excel.Workbooks.Open(abs_path)
        print(f"Workbook opened, COM object: {wb}")
    except Exception as e:
        print(f"Failed to open workbook: {e}", file=sys.stderr)
        excel.Quit()
        sys.exit(1)
    if wb is None:
        print(f"Error: Excel did not return a workbook object.", file=sys.stderr)
        excel.Quit()
        sys.exit(1)
    try:
        sheet_count = wb.Worksheets.Count
        print(f"Workbook has {sheet_count} sheet(s)")
        if sheet_count == 0:
            print("No worksheets found in the workbook.", file=sys.stderr)
            wb.Close(False)
            excel.Quit()
            sys.exit(1)
        for i in range(1, sheet_count + 1):
            sheet = wb.Worksheets(i)
            sheet_name = sheet.Name
            print(f"Processing sheet: {sheet_name}")
            safe_name = "".join(
                c if c.isalnum() or c in (" ", "_") else "_" for c in sheet_name
            ).strip()
            out_file = os.path.join(out_dir, f"{base_name}_{safe_name}.pdf")
            try:
                # Use named args for COM ExportAsFixedFormat
                sheet.ExportAsFixedFormat(Type=0, Filename=out_file)
                print(f"Exported {sheet_name} to {out_file}")
            except Exception as e:
                print(
                    f"WARNING: Failed to export '{sheet_name}' to PDF. File: {out_file}\n  Reason: {e}",
                    file=sys.stderr,
                )
    finally:
        wb.Close(False)
        excel.Quit()


if __name__ == "__main__":
    main()
