"""
Redact a user‑selected area in page 1 of a PDF and export the selection as PNG.
"""

import sys
import fitz  # PyMuPDF
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
    doc = fitz.open(pdf_path)
    page = doc[page_index]

    # Render page to bitmap (72 dpi * zoom)
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Tkinter UI
    root = tk.Tk()
    root.title("Drag to select area – Release mouse button to confirm")
    canvas = tk.Canvas(root, width=pix.width, height=pix.height)
    canvas.pack()
    tk_img = ImageTk.PhotoImage(img)
    canvas.create_image(0, 0, anchor="nw", image=tk_img)

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
        root.quit()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

    root.mainloop()  # Blocks until mouse released
    root.destroy()

    if "x1" not in sel:  # User closed window without selecting
        print("No area selected; exiting.")
        return

    # Normalise coordinates
    x0, y0, x1, y1 = map(int, (sel["x0"], sel["y0"], sel["x1"], sel["y1"]))
    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0

    # 3 Save cropped selection as PNG
    cropped = img.crop((x0, y0, x1, y1))
    cropped.save(out_img, "PNG")

    # 4 Paint white rectangle in the PDF (convert px → PDF pts via zoom)
    rect_pdf = fitz.Rect(x0 / zoom, y0 / zoom, x1 / zoom, y1 / zoom)
    shape = page.new_shape()
    shape.draw_rect(rect_pdf)
    shape.finish(fill=(1, 1, 1))  # opaque white
    shape.commit()

    doc.save(out_pdf)
    doc.close()
    print(f"✓  Redacted page saved to   {out_pdf}")
    print(f"✓  Cropped image exported to {out_img}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage:  python redact_crop.py  input.pdf  output.pdf  cropped.png")
        sys.exit(1)
    select_and_redact(*sys.argv[1:])
