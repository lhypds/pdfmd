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


def select_and_redact(
    pdf_path: str, out_pdf: str, out_img: str, page_index: int = 0, zoom: float = 2.0
) -> None:
    """
    1. Renders page_index with the given zoom.
    2. Opens a Tk window to let the user draw a rectangle.
    3. Saves the cropped selection as out_img (PNG).
    4. Draws an opaque white rectangle in the PDF and saves out_pdf.
    """
    # Cleanup previous redacted PDF and cropped PNGs
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    if os.path.exists(out_pdf):
        os.remove(out_pdf)
    for old in glob.glob(f"{base_name}_crop_*.png"):
        os.remove(old)

    doc = fitz.open(pdf_path)
    page = doc[page_index]

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
        sel["rect"] = canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="red"
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
        selections.append((x0, y0, x1, y1))

    # Bind mouse events for drawing rectangles
    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

    # bind finish key
    def on_done(event):
        root.quit()

    root.bind("<Return>", on_done)
    root.mainloop()  # Blocks until Enter pressed
    root.destroy()

    if not selections:
        print("No area selected; exiting.")
        return

    # Prepare base for image outputs
    base_img = out_img
    if base_img.lower().endswith(".png"):
        base_img = base_img[:-4]

    # Process each selection: save crop and mark redaction
    for idx, (x0, y0, x1, y1) in enumerate(selections, start=1):
        # Save cropped selection as PNG
        cropped = img.crop((x0, y0, x1, y1))
        img_path = f"{base_img}_{idx}.png"
        cropped.save(img_path, "PNG")
        print(f"✓  Cropped image exported to {img_path}")
        # Mark for redaction
        rect_pdf = fitz.Rect(x0 / zoom, y0 / zoom, x1 / zoom, y1 / zoom)
        page.add_redact_annot(rect_pdf, fill=(1, 1, 1))
    # Apply all redactions
    page.apply_redactions()

    doc.save(out_pdf)
    doc.close()
    print(f"✓  Redacted page saved to {out_pdf}")


# Command-line interface
def main_cli():
    parser = argparse.ArgumentParser(
        description="Crop and redact regions of a PDF and export selections as PNG"
    )
    parser.add_argument(
        "-i", "--input", dest="input_pdf", required=True, help="Input PDF file path"
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_pdf",
        help="Output (redacted) PDF file path; defaults to '<input_basename>_pdfcrop.pdf'",
        default=None,
    )
    parser.add_argument(
        "--page", type=int, default=0, help="Page index (0-based) to crop, default 0"
    )
    parser.add_argument(
        "--zoom", type=float, default=2.0, help="Zoom factor for rendering, default 2.0"
    )
    args = parser.parse_args()
    # Derive default output PDF if not provided
    if not args.output_pdf:
        base = os.path.splitext(os.path.basename(args.input_pdf))[0]
        args.output_pdf = f"{base}_pdfcrop.pdf"
    # Derive base image name for PNG exports
    base = os.path.splitext(os.path.basename(args.input_pdf))[0]
    base_img = f"{base}_crop.png"
    select_and_redact(
        args.input_pdf,
        args.output_pdf,
        base_img,
        args.page,
        args.zoom,
    )


if __name__ == "__main__":
    main_cli()
