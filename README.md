PDF A4 Tiler

A Python desktop application that tiles PDF artwork across multiple A4 pages at 100% scale, making large designs easy to print and assemble.

Features
True 100% Scale: Preserves the original artwork size for accurate printing.
Crop Marks: Includes corner crop marks for easy cutting and trimming.
Alignment Crosshairs: Helps align multiple printed sheets precisely.
Reference Scale Bar: Adds a 10 mm or 20 mm reference bar to each page.
Tile Identification: Displays page number, source page, row, and column.
Batch Processing: Processes an entire folder of PDF files in one go.
Adjustable Overlap: Supports overlap settings from 0 to 24.9 mm.
A4 Orientation: Supports portrait and landscape layouts.
Non-Destructive Processing: Keeps original PDF files unchanged.
Vector Preservation: Maintains crisp text and vector graphics without rasterization.
Requirements
Python 3.12
CustomTkinter
PyMuPDF
PyInstaller (for building the Windows executable)

Install the dependencies:

bash
pip install -r requirements.txt

Run the Application

Clone the repository:

bash
git clone https://github.com/YousufAbdullah0001/PDF-A4-Tiler.git


Navigate to the project directory:

bash
cd PDF-A4-Tiler


Run the application:

bash
python main.py

Replace the repository URL and folder name if your GitHub repository uses a different name.
Build for Windows

Install PyInstaller:

bash
pip install pyinstaller


Build the executable:

bash
pyinstaller --onedir --windowed --collect-all customtkinter main.py


The generated application will be available in:

text
dist/main/

How to Use
Launch the application.
Select a PDF file or choose a folder for batch processing.
Configure the A4 orientation and overlap settings.
Process the artwork into tiled A4 pages.
Open the generated PDFs and print at 100% scale.
Cut along the crop marks and align the sheets using the registration marks.

Important: Disable options such as “Fit to page” when printing. Always print at 100% or “Actual Size” to preserve the artwork dimensions.

Output

Processed files are saved in the A4_Tiled/ output folder, keeping the original files untouched.

Project Structure
text
PDF-A4-Tiler/
├── main.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── .github/
│   └── workflows/
│       └── build.yml
└── screenshots/

License

This project is licensed under the MIT License. See the LICENSE file for details.

Author

YousufAbdullah0001

GitHub: @YousufAbdullah0001
