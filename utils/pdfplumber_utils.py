import pdfplumber


def pdfplumber_pdfmd(input_path: str, output_path: str) -> str:
    """
    Extract text and tables from a PDF using pdfplumber and write markdown output.
    Returns the path to the generated markdown file.
    """
    # collect items with position info
    items = []
    with pdfplumber.open(input_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # only process first page
            if page_num > 1:
                break

            # get table bounding boxes first to skip words inside tables
            tables = page.find_tables() or []
            table_bboxes = [tbl.bbox for tbl in tables]

            # get all word positions and initialize filtered word list
            all_words = page.extract_words() or []
            words = []

            # filter out words inside table bboxes
            for w in all_words:
                x0, top = w.get("x0"), w.get("top")
                inside_table = False
                for tb in table_bboxes:
                    tx0, ttop, tx1, tbottom = tb
                    # ignore if upper-left corner of word lies within table bbox
                    if x0 >= tx0 and x0 <= tx1 and top >= ttop and top <= tbottom:
                        inside_table = True
                        break
                if not inside_table:
                    words.append(w)

            # group filtered words into lines based on vertical proximity
            tolerance = 3  # vertical tolerance for grouping words in the same line
            words_sorted = sorted(words, key=lambda w: (w["top"], w["x0"]))
            lines = []
            current_line = []
            current_y = None
            for w in words_sorted:
                y = w.get("top", 0)
                if current_y is None or abs(y - current_y) <= tolerance:
                    current_line.append(w)
                    current_y = current_y or y
                else:
                    lines.append(current_line)
                    current_line = [w]
                    current_y = y
            if current_line:
                lines.append(current_line)

            # emit each line as a paragraph
            for line in lines:
                content = " ".join(w["text"] for w in line)
                y0 = line[0].get("top", 0)
                # debug print paragraph(position) info
                print(f"[DEBUG] Paragraph on page {page_num} at y={y0}")
                items.append((page_num, y0, "para", content))

            # tables: append table items after paragraphs
            for tbl in tables:
                print(f"[DEBUG] Found table: {tbl.extract()}")
                bbox = tbl.bbox  # (x0, top, x1, bottom)
                print(f"[DEBUG] Table on page {page_num} bbox={bbox}")
                items.append((page_num, bbox[1], "table", tbl))

    # sort items by page then vertical position
    items.sort(key=lambda x: (x[0], x[1]))

    # emit markdown
    with open(output_path, "w", encoding="utf-8") as f:
        for _, _, kind, obj in items:
            if kind == "para":
                f.write(obj)
                f.write("\n\n")
            else:
                # obj is a pdfplumber Table
                table = obj.extract()
                # header
                f.write("| " + " | ".join(table[0]) + " |\n")
                f.write("| " + " | ".join(["---"] * len(table[0])) + " |\n")
                for row in table[1:]:
                    cells = [cell or "" for cell in row]
                    f.write("| " + " | ".join(cells) + " |\n")
                f.write("\n")

    return output_path
