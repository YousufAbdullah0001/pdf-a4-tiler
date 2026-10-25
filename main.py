import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import threading
import pymupdf as fitz  
import customtkinter as ctk

# ─── Constants ────────────────────────────────────────────────────────────────
MM = 72 / 25.4
A4_W = 210 * MM
A4_H = 297 * MM

SIDE = 8 * MM
TOP = 8 * MM
BOTTOM = 5 * MM
FOOTER = 22 * MM

CROP_COLOR = (0.15, 0.15, 0.15)
GUIDE_COLOR = (0.55, 0.55, 0.55)


def mm(value):
    return value * MM


def get_a4(orientation):
    if orientation == "Landscape":
        return A4_H, A4_W
    return A4_W, A4_H


def get_layout(orientation):
    page_w, page_h = get_a4(orientation)
    left = SIDE
    top = TOP
    tile_w = page_w - 2 * SIDE
    tile_h = page_h - TOP - BOTTOM - FOOTER
    if tile_w <= 0 or tile_h <= 0:
        raise ValueError("Invalid page layout.")
    return page_w, page_h, left, top, tile_w, tile_h


def make_tiles(rect, tile_w, tile_h, overlap):
    step_x = tile_w - overlap
    step_y = tile_h - overlap
    if step_x <= 0 or step_y <= 0:
        raise ValueError("Overlap must be smaller than tile area.")

    xs = [rect.x0]
    while xs[-1] + tile_w < rect.x1 - 0.01:
        xs.append(xs[-1] + step_x)

    ys = [rect.y0]
    while ys[-1] + tile_h < rect.y1 - 0.01:
        ys.append(ys[-1] + step_y)

    tiles = []
    for row, y in enumerate(ys, 1):
        for col, x in enumerate(xs, 1):
            clip = fitz.Rect(x, y, min(x + tile_w, rect.x1), min(y + tile_h, rect.y1))
            tiles.append((clip, row, col))
    return tiles


def draw_crop_marks(page, x, y, w, h):
    length = mm(3)
    gap = mm(0.7)
    pen = 0.55
    corners = [
        (x, y, -1, -1),
        (x + w, y, 1, -1),
        (x, y + h, -1, 1),
        (x + w, y + h, 1, 1),
    ]
    for cx, cy, sx, sy in corners:
        page.draw_line((cx + sx * gap, cy), (cx + sx * (gap + length), cy),
                       color=CROP_COLOR, width=pen)
        page.draw_line((cx, cy + sy * gap), (cx, cy + sy * (gap + length)),
                       color=CROP_COLOR, width=pen)


def draw_alignment_marks(page, x, y, w, h):
    arm = mm(2)
    positions = [(x - mm(3), y + h / 2), (x + w + mm(3), y + h / 2)]
    for cx, cy in positions:
        page.draw_line((cx - arm, cy), (cx + arm, cy), color=GUIDE_COLOR, width=0.45)
        page.draw_line((cx, cy - arm), (cx, cy + arm), color=GUIDE_COLOR, width=0.45)


def draw_footer(page, page_no, total_pages, scale_mm,
                filename, source_page, row, col, page_w, page_h):
    footer_y = page_h - FOOTER + mm(1)
    page.draw_line((mm(5), footer_y), (page_w - mm(5), footer_y),
                   color=GUIDE_COLOR, width=0.5)

    sx = mm(10)
    sy = page_h - mm(10)
    bar_len = mm(scale_mm)
    tick = mm(2)

    page.draw_line((sx, sy), (sx + bar_len, sy), color=(0, 0, 0), width=1)
    page.draw_line((sx, sy - tick), (sx, sy + tick), color=(0, 0, 0), width=0.8)
    page.draw_line((sx + bar_len, sy - tick), (sx + bar_len, sy + tick), color=(0, 0, 0), width=0.8)

    page.insert_text((sx, page_h - mm(14)),
                     f"{scale_mm} mm reference - print at 100%",
                     fontsize=7, fontname="helv")
    page.insert_text((mm(10), page_h - mm(3)),
                     f"Page {page_no}/{total_pages} | Source page {source_page} | Tile row {row}, col {col}",
                     fontsize=6.5, fontname="helv")
    label = Path(filename).stem[:24]
    page.insert_text((page_w - mm(55), page_h - mm(14)), label, fontsize=6, fontname="helv")


def process_pdf(pdf_path, output_path, orientation, overlap_mm, scale_mm):
    page_w, page_h, left, top, tile_w, tile_h = get_layout(orientation)
    overlap = mm(overlap_mm)

    src = fitz.open(pdf_path)
    out = fitz.open()

    try:
        jobs = []
        for source_index, source_page in enumerate(src):
            tiles = make_tiles(source_page.rect, tile_w, tile_h, overlap)
            for clip, row, col in tiles:
                jobs.append((source_index, clip, source_index + 1, row, col))

        total_pages = len(jobs)

        for page_no, job in enumerate(jobs, start=1):
            src_index, clip, source_page_no, row, col = job
            page = out.new_page(width=page_w, height=page_h)

            target = fitz.Rect(left, top, left + clip.width, top + clip.height)
            page.show_pdf_page(target, src, src_index, clip=clip, keep_proportion=False)

            draw_crop_marks(page, left, top, clip.width, clip.height)
            draw_alignment_marks(page, left, top, clip.width, clip.height)
            draw_footer(page, page_no, total_pages, scale_mm,
                        pdf_path.name, source_page_no, row, col, page_w, page_h)

        out.save(output_path, garbage=4, deflate=True)
    finally:
        out.close()
        src.close()


# ─── Modern GUI (CustomTkinter) ───────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PDF to A4 Tiler — True 100% Scale")
        self.geometry("780x640")
        self.minsize(700, 580)

        self.folder_var = ctk.StringVar(value="")
        self.orientation_var = ctk.StringVar(value="Portrait")
        self.overlap_var = ctk.StringVar(value="5")
        self.scale_var = ctk.StringVar(value="20")
        self.count_var = ctk.StringVar(value="Select a folder")
        self.status_var = ctk.StringVar(value="Ready")
        self._processing = False

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="PDF → A4 Tiler",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Split large PDF pages into A4 sheets at true 100% scale",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        # ── Tabview ──
        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=10)
        self.tabs.grid_columnconfigure(0, weight=1)
        self.tabs.grid_rowconfigure(0, weight=1)

        self.tab_convert = self.tabs.add("⚙  Convert")
        self.tab_features = self.tabs.add("✦  Features")

        self._build_convert_tab()
        self._build_features_tab()

    def _build_convert_tab(self):
        t = self.tab_convert
        t.grid_columnconfigure(0, weight=1)
        t.grid_rowconfigure(4, weight=1)

        # Folder row
        folder_frame = ctk.CTkFrame(t, fg_color="transparent")
        folder_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        folder_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(folder_frame, text="PDF Folder",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w", columnspan=2
        )

        row = ctk.CTkFrame(folder_frame, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", columnspan=2, pady=(4, 0))
        row.grid_columnconfigure(0, weight=1)

        self.folder_entry = ctk.CTkEntry(row, textvariable=self.folder_var,
                                         placeholder_text="Select folder containing PDFs…")
        self.folder_entry.grid(row=0, column=0, sticky="ew")
        self.folder_entry.bind("<FocusOut>", lambda e: self._refresh_count())

        ctk.CTkButton(row, text="Browse", width=90, command=self._browse).grid(
            row=0, column=1, padx=(8, 0)
        )

        ctk.CTkLabel(t, textvariable=self.count_var,
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 10))

        # Settings frame
        settings = ctk.CTkFrame(t)
        settings.grid(row=2, column=0, sticky="ew", padx=10, pady=4)
        settings.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(settings, text="Layout Settings",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4), columnspan=2
        )

        # ✅ Fix 2: CTkOptionMenu with command callback (no textvariable)
        ctk.CTkLabel(settings, text="A4 Orientation").grid(
            row=1, column=0, sticky="w", padx=12, pady=4
        )
        self.orientation_menu = ctk.CTkOptionMenu(
            settings, values=["Portrait", "Landscape"],
            width=140, command=lambda v: self.orientation_var.set(v)
        )
        self.orientation_menu.set(self.orientation_var.get())
        self.orientation_menu.grid(row=1, column=1, sticky="w", padx=12, pady=4)

        ctk.CTkLabel(settings, text="Overlap (mm)").grid(
            row=2, column=0, sticky="w", padx=12, pady=4
        )
        ctk.CTkEntry(settings, textvariable=self.overlap_var, width=100).grid(
            row=2, column=1, sticky="w", padx=12, pady=4
        )

        ctk.CTkLabel(settings, text="Reference Scale").grid(
            row=3, column=0, sticky="w", padx=12, pady=4
        )
        self.scale_menu = ctk.CTkOptionMenu(
            settings, values=["10", "20"],
            width=140, command=lambda v: self.scale_var.set(v)
        )
        self.scale_menu.set(self.scale_var.get())
        self.scale_menu.grid(row=3, column=1, sticky="w", padx=12, pady=(4, 12))

        # Progress + Status
        self.progress = ctk.CTkProgressBar(t)
        self.progress.set(0)
        self.progress.grid(row=3, column=0, sticky="ew", padx=10, pady=(16, 4))

        ctk.CTkLabel(t, textvariable=self.status_var,
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=4, column=0, sticky="w", padx=10, pady=4)

        # Convert button
        self.convert_btn = ctk.CTkButton(
            t, text="🚀  Convert All PDFs",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44, command=self._convert_all
        )
        self.convert_btn.grid(row=5, column=0, sticky="e", padx=10, pady=(4, 12))

    def _build_features_tab(self):
        t = self.tab_features
        t.grid_columnconfigure(0, weight=1)
        t.grid_rowconfigure(0, weight=1)

        content = ctk.CTkScrollableFrame(t, fg_color="transparent")
        content.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        content.grid_columnconfigure(0, weight=1)

        features = [
            ("📐 True 100% Scale", "No scaling — artwork is placed at exact source size. Print at 100% for accurate dimensions."),
            ("✂️ Crop Marks Outside Artwork", "Short crop ticks at all 4 corners, placed in the margin. No cut line crosses the design."),
            ("🎯 Alignment Crosshairs", "Registration marks in left/right safe margins for precise multi-sheet assembly."),
            ("📏 Reference Scale Bar", "Every page includes a 10 mm or 20 mm scale bar to verify print accuracy."),
            ("📄 Tile Identification", "Page number, source page, row & column printed in the footer of every sheet."),
            ("📁 Batch Processing", "Select a folder → all PDFs converted at once into an A4_Tiled subfolder."),
            ("🔄 Overlap Control", "Adjustable overlap (0–24.9 mm) for easier physical alignment of tiled sheets."),
            ("🖥️ Portrait & Landscape", "Choose A4 orientation to match your source artwork direction."),
            ("🔒 Non-Destructive", "Originals are never modified. Output goes to a separate A4_Tiled folder."),
            ("⚡ Vector Preserved", "Uses PyMuPDF show_pdf_page — text and vectors stay crisp, no rasterization."),
        ]

        ctk.CTkLabel(content, text="Features",
                     font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, sticky="w", pady=(4, 12)
        )

        for i, (title, desc) in enumerate(features, 1):
            card = ctk.CTkFrame(content)
            card.grid(row=i, column=0, sticky="ew", pady=4, padx=4)
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(card, text=title,
                         font=ctk.CTkFont(size=13, weight="bold")).grid(
                row=0, column=0, sticky="w", padx=12, pady=(8, 2)
            )
            ctk.CTkLabel(card, text=desc,
                         font=ctk.CTkFont(size=12),
                         text_color="gray",
                         wraplength=600, justify="left").grid(
                row=1, column=0, sticky="w", padx=12, pady=(0, 8)
            )

        info = ctk.CTkFrame(content, fg_color="transparent")
        info.grid(row=len(features) + 1, column=0, sticky="ew", pady=(16, 4))
        info.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(info, text="⚙  Tech Stack",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=4
        )
        ctk.CTkLabel(info,
                     text="Python  •  CustomTkinter  •  PyMuPDF (pymupdf)\n"
                          "Output: A4_Tiled/  •  Input PDFs unchanged",
                     font=ctk.CTkFont(size=12), text_color="gray").grid(
            row=1, column=0, sticky="w", padx=4, pady=(2, 8)
        )

    # ── Methods ───────────────────────────────────────────────────────────────
    def _browse(self):
        folder = filedialog.askdirectory(title="Select folder containing PDFs")
        if folder:
            self.folder_var.set(folder)
            self._refresh_count()

    def _refresh_count(self):
        folder = Path(self.folder_var.get().strip())
        if folder.is_dir():
            pdfs = [p for p in folder.glob("*.pdf") if not p.stem.endswith("_A4_Tiled")]
            self.count_var.set(f"✅ {len(pdfs)} PDF file(s) found")
        else:
            self.count_var.set("Select a folder containing PDFs")

    def _convert_all(self):
        if self._processing:
            return

        folder = Path(self.folder_var.get().strip())
        if not folder.is_dir():
            ctk.CTkMessageBox(self, "Select a valid folder first.")
            return

        try:
            overlap = float(self.overlap_var.get())
            scale_size = int(self.scale_var.get())
            if overlap < 0 or overlap >= 25:
                raise ValueError
            if scale_size not in (10, 20):
                raise ValueError
            get_layout(self.orientation_var.get())
        except (ValueError, TypeError):
            ctk.CTkMessageBox(self, "Invalid settings.\nOverlap: 0–24.9 mm\nScale: 10 or 20 mm")
            return

        pdfs = sorted(p for p in folder.glob("*.pdf") if not p.stem.endswith("_A4_Tiled"))
        if not pdfs:
            ctk.CTkMessageBox(self, "No PDF files found in the selected folder.")
            return

        output_dir = folder / "A4_Tiled"
        output_dir.mkdir(exist_ok=True)

        self._processing = True
        self.convert_btn.configure(state="disabled", text="Processing…")
        self.progress.set(0)

        threading.Thread(
            target=self._worker,
            args=(pdfs, output_dir, self.orientation_var.get(), overlap, scale_size),
            daemon=True
        ).start()

    def _worker(self, pdfs, output_dir, orientation, overlap, scale_size):
        errors = []
        done = 0
        total = len(pdfs)

        for i, pdf in enumerate(pdfs, start=1):
            self.after(0, lambda i=i, pdf=pdf: self.status_var.set(
                f"Processing {i}/{total}: {pdf.name}"
            ))
            self.after(0, lambda i=i: self.progress.set(i / total))

            output = output_dir / f"{pdf.stem}_A4_Tiled.pdf"
            try:
                process_pdf(pdf, output, orientation, overlap, scale_size)
                done += 1
            except Exception as exc:
                errors.append(f"{pdf.name}: {exc}")

        self.after(0, lambda: self._on_done(done, total, errors, output_dir))

    def _on_done(self, done, total, errors, output_dir):
        self._processing = False
        self.convert_btn.configure(state="normal", text="🚀  Convert All PDFs")
        self.status_var.set("Finished")

        msg = f"✅ Converted: {done}/{total}\n❌ Failed: {len(errors)}\n\n📁 Output: {output_dir}"
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors[:8])

        ctk.CTkMessageBox(self, msg, title="Conversion Complete")


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()   