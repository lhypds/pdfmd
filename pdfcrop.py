"""
Redact a user‑selected area in page 1 of a PDF and export the selection as PNG.
"""

import sys
import argparse
import os
import fitz  # PyMuPDF
import glob
import tkinter as tk
from PIL import Image, ImageTk
from dotenv import load_dotenv
import shutil  # for copying original PDF when no crop

# ensure the Windows console uses UTF-8 so Unicode symbols like ✓ and Japanese text can print
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()


def select_and_redact(
    pdf_path: str, out_pdf: str, page_index: int = 1, zoom: float = 2.0
) -> None:
    """
    1. Renders page_index with the given zoom.
    2. Opens a Tk window to let the user draw a rectangle.
    4. Draws an opaque white rectangle in the PDF and saves out_pdf.
    """
    # Cleanup previous redacted PDF and cropped PNGs (images named 1.png, 2.png, ...)
    if os.path.exists(out_pdf):
        os.remove(out_pdf)
    # cleanup previous PNGs for this page
    for old in glob.glob(f"{page_index}_*.png"):
        os.remove(old)

    # store paths of all cropped images
    img_paths = []
    doc = fitz.open(pdf_path)
    page = doc[page_index - 1]

    # Render page to bitmap (72 dpi * zoom)
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Tkinter UI for multiple selections
    selections = []  # store rectangle coords
    root = tk.Tk()
    root.title("Draw rectangles – Press Enter when done")
    # Instruction label
    lbl = tk.Label(root, text="Drag to select area(s). Press Enter to finish.")
    lbl.pack()
    canvas = tk.Canvas(root, width=pix.width, height=pix.height)
    canvas.pack()
    tk_img = ImageTk.PhotoImage(img)
    canvas.create_image(0, 0, anchor="nw", image=tk_img)
    # retain reference to prevent GC
    canvas.image = tk_img

    # Variables to store selection
    sel = {}

    def on_press(event):
        sel["x0"], sel["y0"] = event.x, event.y
        # detect Ctrl pressed (skip saving PNG)
        ctrl = (event.state & 0x4) != 0
        sel["skip_png"] = ctrl
        sel["rect"] = canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="gray" if ctrl else "red"
        )

    def on_drag(event):
        if "rect" in sel:
            canvas.coords(sel["rect"], sel["x0"], sel["y0"], event.x, event.y)

    def on_release(event):
        sel["x1"], sel["y1"] = event.x, event.y
        # normalize coords and store selection
        x0, y0, x1, y1 = map(int, (sel["x0"], sel["y0"], sel["x1"], sel["y1"]))
        if x0 > x1:
            x0, x1 = x1, x0
        if y0 > y1:
            y0, y1 = y1, y0
        # include skip flag and canvas rect ID for PNG
        selections.append((x0, y0, x1, y1, sel.get("skip_png", False), sel["rect"]))

    # Bind mouse events for drawing rectangles
    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

    # bind finish key
    def on_done(event):
        root.quit()

    root.bind("<Return>", on_done)

    # Bind Ctrl+Z to undo last selection
    def on_undo(event):
        if selections:
            x0, y0, x1, y1, skip, rect_id = selections.pop()
            canvas.delete(rect_id)
            print(f"↩️  Undid selection at ({x0},{y0})-({x1},{y1})")

    root.bind("<Control-z>", on_undo)
    root.mainloop()  # Blocks until Enter pressed
    root.destroy()

    if not selections:
        print("No area selected; exporting original PDF.")
        shutil.copy(pdf_path, out_pdf)
        print(f"✓  Exported original PDF to {out_pdf}")
        return []

    # Save crops (unless skipped) and collect rects for redaction
    for idx, (x0, y0, x1, y1, skip_png, _rect_id) in enumerate(selections, start=1):
        if not skip_png:
            cropped = img.crop((x0, y0, x1, y1))
            img_path = f"{page_index}_{idx}.png"
            cropped.save(img_path, "PNG")
            print(f"✓  Cropped image exported to {img_path}")
            img_paths.append(img_path)

    # Create a new PDF with only the selected page and apply true redactions
    new_doc = fitz.open()
    new_doc.insert_pdf(doc, from_page=page_index - 1, to_page=page_index - 1)
    new_page = new_doc[0]
    # Add redact annotations for each selected rect, then remove underlying content
    for x0, y0, x1, y1, _skip_png, _rect_id in selections:
        rect_pdf = fitz.Rect(x0 / zoom, y0 / zoom, x1 / zoom, y1 / zoom)
        new_page.add_redact_annot(rect_pdf, fill=(1, 1, 1))
    new_page.apply_redactions()
    # Save with compression to keep file size small
    new_doc.save(out_pdf, deflate=True, garbage=4)
    new_doc.close()
    doc.close()  # Close the original document
    print(f"✓  Redacted page saved to {out_pdf}")
    return img_paths


# Command-line interface
def main_cli():
    parser = argparse.ArgumentParser(
        description="Crop and redact regions of a PDF and export selections as PNG"
    )
    parser.add_argument(
        "-i", "--input", dest="input_pdf", required=True, help="Input PDF file path"
    )
    parser.add_argument(
        "--page",
        type=int,
        required=True,
        help="Page index (1-based) to crop.",
    )
    args = parser.parse_args()
    # Always derive redacted PDF output path from input basename
    base = os.path.splitext(os.path.basename(args.input_pdf))[0]
    output_pdf = f"{base}_pdfcrop_{args.page}.pdf"
    # read zoom level from environment
    try:
        zoom = float(os.getenv("PDFCROP_ZOOM_LEVEL", "2"))
    except ValueError:
        zoom = 2.0
    select_and_redact(
        args.input_pdf,
        output_pdf,
        args.page,
        zoom,
    )


if __name__ == "__main__":
    main_cli()
