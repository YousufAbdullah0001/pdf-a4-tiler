# PDF → A4 Tiler

Split large PDF pages into A4 sheets at **true 100% scale** — no scaling, no rasterization.

> Perfect for tiling large artwork, schematics, blueprints, or posters for physical printing.

##  Features

| Feature | Detail |
|---------|--------|
|  True 100% Scale | Artwork placed at exact source size — print at 100% |
|  Crop Marks | 4-corner ticks in margin, never crosses the design |
|  Alignment Crosshairs | Registration marks for precise multi-sheet assembly |
|  Reference Scale Bar | 10 mm or 20 mm bar on every page |
|  Tile Identification | Page no., source page, row & col in footer |
|  Batch Processing | Entire folder → `A4_Tiled/` subfolder in one click |
|  Overlap Control | 0–24.9 mm adjustable overlap |
|  Portrait / Landscape | A4 orientation selectable |
|  Non-Destructive | Originals never modified |
|  Vector Preserved | No rasterization — text & vectors stay crisp |

##  **Screenshot**

<!-- Replace with your actual screenshot -->
![App Screenshot](screenshots/app.png)

##  **Installation**


# 1. Create virtual environment (optional but recommended)
```
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt
```

**Usage**

Launch:

```python main.py```

Select folder containing your PDF files (Browse button).

**Configure:**
A4 Orientation: Portrait / Landscape
Overlap: 0–24.9 mm (default: 5 mm)
Reference Scale: 10 mm or 20 mm
Click "Convert All PDFs" — output appears in A4_Tiled/ subfolder.

**Output Structure**

your_folder/
├── blueprint.pdf          ← original (unchanged)
├── poster.pdf             ← original (unchanged)
└── A4_Tiled/
    ├── blueprint_A4_Tiled.pdf
    └── poster_A4_Tiled.pdf   



**Printing Tips**
Set printer to 100% scale (disable "Fit to page")
Use the scale bar to verify accuracy
Align sheets using crosshair marks
Crop along the tick marks (outside artwork)

