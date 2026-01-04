# Marker PDF to Markdown Converter

A simple GUI application for converting PDF files to Markdown using [marker-pdf](https://github.com/VikParuchuri/marker).

## Features

- **Multiple PDF support** - Add multiple PDFs for batch conversion
- **Custom output names** - Rename output files via editable table (double-click to edit)
- **URL downloads** - Add PDFs directly from web URLs
- **Project folders** - Automatically create organized project folders for each PDF
- **Favorites** - Save frequently used output directories for quick access
- **Page range selection** - Convert all pages or specify a custom range
- **Real-time output** - Monitor conversion progress in the terminal panel
- **Cross-platform** - Works on macOS, Windows, and Linux

## Prerequisites

- Python 3.10 or higher
- tkinter (usually included with Python)

## Installation

1. Clone or download this repository

2. Create a virtual environment:

   ```bash
   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. If tkinter is not installed:

   - **macOS (Homebrew):** `brew install python-tk@3.14` (match your Python version)
   - **Ubuntu/Debian:** `sudo apt-get install python3-tk`
   - **Windows:** Tkinter is included with the official Python installer from python.org (ensure "tcl/tk" is checked during installation)

## Running the Application

### macOS

Double-click `marker.command` or run from terminal:

```bash
.venv/bin/python marker.py
```

### Windows

Double-click `marker.bat` or run from Command Prompt:

```cmd
.venv\Scripts\python.exe marker.py
```

### Linux

```bash
.venv/bin/python marker.py
```

## Usage

1. **Add PDFs** - Click "Add Files..." to select PDFs, or "Add URL..." to download from a web link
2. **Set output names** - Double-click the "Output Name" column to rename files
3. **Choose output directory** - Browse or select from your saved favorites
4. **Configure options:**
   - **Create Project Folder** - Creates a folder for each PDF with the converted files
   - **Move PDF to output directory** - Moves the original PDF into the project folder
5. **Page range** - Optionally uncheck "All Pages" to specify a range (1-based)
6. **Convert** - Click to start conversion; monitor progress in the terminal panel
7. **Open** - Click to open the output directory in your file manager

### Output Structure

With "Create Project Folder" enabled, each PDF gets its own organized folder:

```
/output_directory/
└── My Book/
    ├── My Book.pdf                    # Original PDF (if moved)
    └── My Book_marker_output/         # Converted files
        ├── My Book.md
        └── images/
```

## License

MIT
