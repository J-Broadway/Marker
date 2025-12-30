#!/usr/bin/env python3
"""
Marker PDF to Markdown Converter GUI
Double-click to run or: python marker.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import threading
import os
import sys
from pathlib import Path


class MarkerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Marker PDF Converter")
        self.root.geometry("750x700")
        self.root.minsize(650, 600)
        
        self.process = None
        self.is_running = False
        self.pdf_files = []  # List of selected PDF files
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- PDF File Selection ---
        file_frame = ttk.LabelFrame(main_frame, text="Input PDFs", padding="5")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Listbox to show selected files
        list_container = ttk.Frame(file_frame)
        list_container.pack(fill=tk.X, expand=True)
        
        self.pdf_listbox = tk.Listbox(
            list_container, 
            height=4,
            selectmode=tk.EXTENDED,
            font=("Menlo", 10) if sys.platform == "darwin" else ("Consolas", 9)
        )
        self.pdf_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.pdf_listbox.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.pdf_listbox.config(yscrollcommand=scrollbar.set)
        
        # Buttons for file management
        btn_container = ttk.Frame(file_frame)
        btn_container.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(btn_container, text="Add Files...", command=self.browse_pdf).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_container, text="Remove Selected", command=self.remove_selected_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_container, text="Clear All", command=self.clear_files).pack(side=tk.LEFT)
        
        # --- Output Directory Selection ---
        output_frame = ttk.LabelFrame(main_frame, text="Output Directory", padding="5")
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.output_path = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_path)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(output_frame, text="Browse...", command=self.browse_output).pack(side=tk.RIGHT)
        
        # --- Page Range Selection ---
        page_frame = ttk.LabelFrame(main_frame, text="Page Range", padding="5")
        page_frame.pack(fill=tk.X, pady=(0, 10))
        
        # All pages checkbox
        self.all_pages = tk.BooleanVar(value=True)
        self.all_pages_check = ttk.Checkbutton(
            page_frame, 
            text="All Pages", 
            variable=self.all_pages,
            command=self.toggle_page_range
        )
        self.all_pages_check.pack(side=tk.LEFT, padx=(0, 20))
        
        # Page range inputs
        range_container = ttk.Frame(page_frame)
        range_container.pack(side=tk.LEFT, fill=tk.X)
        
        ttk.Label(range_container, text="Start Page:").pack(side=tk.LEFT, padx=(0, 5))
        self.start_page = tk.StringVar(value="1")
        self.start_entry = ttk.Entry(range_container, textvariable=self.start_page, width=8)
        self.start_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(range_container, text="End Page:").pack(side=tk.LEFT, padx=(0, 5))
        self.end_page = tk.StringVar(value="1")
        self.end_entry = ttk.Entry(range_container, textvariable=self.end_page, width=8)
        self.end_entry.pack(side=tk.LEFT)
        
        # Note about page numbering
        ttk.Label(page_frame, text="(1-based page numbers)", foreground="gray").pack(side=tk.RIGHT)
        
        # Initially disable page range inputs
        self.toggle_page_range()
        
        # --- Action Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.convert_btn = ttk.Button(
            button_frame, 
            text="Convert", 
            command=self.start_conversion,
            style="Accent.TButton"
        )
        self.convert_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_btn = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=self.cancel_conversion,
            state=tk.DISABLED
        )
        self.cancel_btn.pack(side=tk.LEFT)
        
        self.clear_btn = ttk.Button(
            button_frame,
            text="Clear Log",
            command=self.clear_log
        )
        self.clear_btn.pack(side=tk.RIGHT)
        
        # --- Terminal Log Output ---
        log_frame = ttk.LabelFrame(main_frame, text="Terminal Output", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=("Menlo", 11) if sys.platform == "darwin" else ("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#d4d4d4"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
    
    def browse_pdf(self):
        """Open file dialog to select multiple PDFs."""
        filenames = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if filenames:
            for filename in filenames:
                if filename not in self.pdf_files:
                    self.pdf_files.append(filename)
                    self.pdf_listbox.insert(tk.END, Path(filename).name)
            # Auto-set output directory to same as first PDF location
            if not self.output_path.get() and self.pdf_files:
                self.output_path.set(str(Path(self.pdf_files[0]).parent))
    
    def remove_selected_files(self):
        """Remove selected files from the list."""
        selected = list(self.pdf_listbox.curselection())
        # Remove in reverse order to maintain correct indices
        for index in reversed(selected):
            self.pdf_listbox.delete(index)
            del self.pdf_files[index]
    
    def clear_files(self):
        """Clear all files from the list."""
        self.pdf_listbox.delete(0, tk.END)
        self.pdf_files.clear()
    
    def browse_output(self):
        """Open directory dialog to select output folder."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_path.set(directory)
    
    def toggle_page_range(self):
        """Enable/disable page range inputs based on checkbox."""
        state = tk.DISABLED if self.all_pages.get() else tk.NORMAL
        self.start_entry.config(state=state)
        self.end_entry.config(state=state)
    
    def log(self, message):
        """Append message to log output."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def clear_log(self):
        """Clear the log output."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def get_marker_command(self, pdf_path):
        """Build the marker CLI command for a single PDF."""
        # Find marker_single in the virtual environment
        script_dir = Path(__file__).parent.resolve()
        venv_bin = script_dir / ".venv" / ("Scripts" if sys.platform == "win32" else "bin")
        marker_cmd = venv_bin / ("marker_single.exe" if sys.platform == "win32" else "marker_single")
        
        if not marker_cmd.exists():
            # Fallback to system PATH
            marker_cmd = "marker_single"
        else:
            marker_cmd = str(marker_cmd)
        
        cmd = [marker_cmd, pdf_path, "--output_dir", self.output_path.get()]
        
        # Add page range if not all pages
        if not self.all_pages.get():
            try:
                # Convert 1-based user input to 0-based for marker
                start = int(self.start_page.get()) - 1
                end = int(self.end_page.get()) - 1
                
                if start < 0 or end < start:
                    raise ValueError("Invalid page range")
                
                cmd.extend(["--page_range", f"{start}-{end}"])
            except ValueError as e:
                messagebox.showerror("Invalid Page Range", 
                    "Please enter valid page numbers.\nStart page must be >= 1 and <= End page.")
                return None
        
        return cmd
    
    def validate_page_range(self):
        """Validate page range inputs before starting conversion."""
        if not self.all_pages.get():
            try:
                start = int(self.start_page.get())
                end = int(self.end_page.get())
                if start < 1 or end < start:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Invalid Page Range", 
                    "Please enter valid page numbers.\nStart page must be >= 1 and <= End page.")
                return False
        return True
    
    def start_conversion(self):
        """Start the PDF conversion process for all selected files."""
        # Validate inputs
        if not self.pdf_files:
            messagebox.showwarning("Missing Input", "Please select at least one PDF file.")
            return
        
        if not self.output_path.get():
            messagebox.showwarning("Missing Output", "Please select an output directory.")
            return
        
        # Check all files exist
        missing_files = [f for f in self.pdf_files if not Path(f).exists()]
        if missing_files:
            messagebox.showerror("Files Not Found", 
                f"The following files were not found:\n" + "\n".join(missing_files))
            return
        
        # Validate page range before starting
        if not self.validate_page_range():
            return
        
        # Update UI state
        self.is_running = True
        self.convert_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        
        # Log start
        total = len(self.pdf_files)
        self.log(f"Starting conversion of {total} file{'s' if total > 1 else ''}...\n\n")
        
        # Run in background thread
        thread = threading.Thread(target=self.run_conversion, args=(list(self.pdf_files),), daemon=True)
        thread.start()
    
    def run_conversion(self, pdf_files):
        """Run the conversion subprocess for each PDF file."""
        total = len(pdf_files)
        successful = 0
        failed = 0
        
        try:
            for index, pdf_path in enumerate(pdf_files, 1):
                if not self.is_running:
                    break
                
                # Log which file we're processing
                filename = Path(pdf_path).name
                self.root.after(0, self.log, f"[{index}/{total}] Converting: {filename}\n")
                
                cmd = self.get_marker_command(pdf_path)
                if cmd is None:
                    failed += 1
                    continue
                
                self.root.after(0, self.log, f"$ {' '.join(cmd)}\n\n")
                
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env={**os.environ, "PYTHONUNBUFFERED": "1"}
                )
                
                # Read output line by line
                for line in iter(self.process.stdout.readline, ""):
                    if not self.is_running:
                        break
                    self.root.after(0, self.log, line)
                
                self.process.stdout.close()
                return_code = self.process.wait()
                
                if return_code == 0:
                    successful += 1
                    self.root.after(0, self.log, f"\n✓ {filename} completed successfully!\n\n")
                elif self.is_running:
                    failed += 1
                    self.root.after(0, self.log, f"\n✗ {filename} failed with exit code {return_code}\n\n")
            
            # Final summary
            if self.is_running:
                self.root.after(0, self.log, 
                    f"{'─' * 40}\n"
                    f"Conversion complete: {successful} succeeded, {failed} failed\n"
                )
        
        except FileNotFoundError:
            self.root.after(0, self.log, 
                "\n✗ Error: marker_single not found.\n"
                "Make sure marker-pdf is installed in the .venv:\n"
                "  .venv/bin/pip install marker-pdf\n"
            )
        except Exception as e:
            self.root.after(0, self.log, f"\n✗ Error: {str(e)}\n")
        finally:
            self.root.after(0, self.conversion_finished)
    
    def conversion_finished(self):
        """Reset UI state after conversion ends."""
        self.is_running = False
        self.process = None
        self.convert_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
    
    def cancel_conversion(self):
        """Cancel the running conversion."""
        if self.process and self.is_running:
            self.is_running = False
            self.process.terminate()
            self.log("\n⚠ Conversion cancelled by user.\n")


def main():
    root = tk.Tk()
    
    # Set a nicer theme on macOS/Windows
    if sys.platform == "darwin":
        root.tk.call("tk", "scaling", 1.5)
    
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    
    app = MarkerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

