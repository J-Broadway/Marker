# Marker PDF to Markdown Converter

A simple GUI application for converting PDF files to Markdown using [marker-pdf](https://github.com/VikParuchuri/marker).

## Features

- Select input PDF and output directory via file browser
- Convert all pages or specify a custom page range
- Real-time terminal output during conversion
- Cancel in-progress conversions

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

1. Click **Browse...** next to "Input PDF" to select your PDF file
2. The output directory defaults to the same folder as the PDF, or choose a different one
3. Optionally uncheck "All Pages" to specify a page range (1-based page numbers)
4. Click **Convert** to start the conversion
5. Monitor progress in the terminal output panel
6. Click **Cancel** to stop an in-progress conversion

The converted Markdown file will be saved in the output directory.


