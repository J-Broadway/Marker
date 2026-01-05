#!/usr/bin/env python3
"""
Marker PDF to Markdown Converter GUI
Double-click to run or: python marker.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox, simpledialog
import subprocess
import threading
import os
import sys
import shutil
import json
import urllib.request
import urllib.parse
import re
from pathlib import Path


class ToolTip:
    """Simple tooltip that appears on hover with a delay."""
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay  # milliseconds
        self.tipwindow = None
        self.scheduled_id = None
        widget.bind("<Enter>", self.schedule_show)
        widget.bind("<Leave>", self.hide)
    
    def schedule_show(self, event=None):
        self.hide()  # Cancel any existing tooltip
        self.scheduled_id = self.widget.after(self.delay, self.show)
    
    def show(self, event=None):
        if self.tipwindow:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        # Set background to match tooltip for square appearance
        tw.configure(background="#000000")
        # Frame with border for square corners
        frame = tk.Frame(tw, background="#ffffe0", bd=1, relief=tk.FLAT)
        frame.pack(padx=1, pady=1)
        label = tk.Label(
            frame, text=self.text, justify=tk.LEFT,
            background="#ffffe0", foreground="#000000",
            font=("TkDefaultFont", 10),
            padx=6, pady=4
        )
        label.pack()
    
    def hide(self, event=None):
        if self.scheduled_id:
            self.widget.after_cancel(self.scheduled_id)
            self.scheduled_id = None
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


class MarkerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Marker PDF Converter")
        self.root.geometry("750x750")
        self.root.minsize(650, 650)
        
        self.process = None
        self.is_running = False
        self.pdf_files = []  # List of selected PDF files
        self.output_names = {}  # Maps file path to custom output name
        
        # For inline editing
        self.edit_entry = None
        self.editing_item = None
        
        # Favorites storage
        self.favorites_file = Path(__file__).parent / ".marker_favorites.json"
        self.all_favorites = self.load_favorites()
        
        # Separate output and input favorites
        self.favorites = self.all_favorites.get("output", [])
        self.input_favorites = self.all_favorites.get("input", [])
        
        # Add default Downloads folder to input favorites if empty
        downloads_folder = str(Path.home() / "Downloads")
        if not self.input_favorites and Path(downloads_folder).exists():
            self.input_favorites.append(downloads_folder)
        
        self.setup_ui()
    
    def load_favorites(self):
        """Load favorites from JSON file."""
        try:
            if self.favorites_file.exists():
                with open(self.favorites_file, 'r') as f:
                    data = json.load(f)
                    # Handle legacy format (list instead of dict)
                    if isinstance(data, list):
                        return {"output": data, "input": []}
                    return data
        except Exception:
            pass
        return {"output": [], "input": []}
    
    def save_favorites(self):
        """Save favorites to JSON file."""
        try:
            data = {"output": self.favorites, "input": self.input_favorites}
            with open(self.favorites_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save favorites: {e}")
    
    def setup_ui(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- PDF File Selection ---
        file_frame = ttk.LabelFrame(main_frame, text="Input PDFs", padding="5")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Treeview table to show selected files
        tree_container = ttk.Frame(file_frame)
        tree_container.pack(fill=tk.X, expand=True)
        
        # Create Treeview with columns
        self.pdf_tree = ttk.Treeview(
            tree_container,
            columns=("name", "output_name"),
            show="headings",
            height=4,
            selectmode="extended"
        )
        
        # Define column headings
        self.pdf_tree.heading("name", text="Name")
        self.pdf_tree.heading("output_name", text="Output Name")
        
        # Define column widths
        self.pdf_tree.column("name", width=300, minwidth=150)
        self.pdf_tree.column("output_name", width=300, minwidth=150)
        
        self.pdf_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.pdf_tree.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.pdf_tree.config(yscrollcommand=scrollbar.set)
        
        # Bind double-click for inline editing
        self.pdf_tree.bind("<Double-1>", self.on_double_click)
        
        # Buttons for file management - Row 1
        btn_container = ttk.Frame(file_frame)
        btn_container.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(btn_container, text="Add Files...", command=self.browse_pdf).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_container, text="Add URL...", command=self.add_url).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_container, text="Remove Selected", command=self.remove_selected_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_container, text="Clear All", command=self.clear_files).pack(side=tk.LEFT)
        
        # Hint label
        ttk.Label(btn_container, text="Double-click Output Name to edit", foreground="gray").pack(side=tk.RIGHT)
        
        # Input favorites row - Row 2
        fav_input_row = ttk.Frame(file_frame)
        fav_input_row.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(fav_input_row, text="Quick open:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.input_fav_var = tk.StringVar(value="")
        self.input_fav_combo = ttk.Combobox(
            fav_input_row,
            textvariable=self.input_fav_var,
            state="readonly",
            width=30
        )
        self.input_fav_combo.pack(side=tk.LEFT, padx=(0, 5))
        self.input_fav_combo.bind("<<ComboboxSelected>>", self.on_input_favorite_selected)
        self.update_input_favorites_combo()
        ToolTip(self.input_fav_combo, "Select folder and open file browser", delay=500)
        
        ttk.Button(fav_input_row, text="★ Add", command=self.add_input_favorite).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(fav_input_row, text="Remove", command=self.remove_input_favorite).pack(side=tk.LEFT)
        
        # --- Output Directory Selection ---
        output_frame = ttk.LabelFrame(main_frame, text="Output Directory", padding="5")
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Directory entry row
        dir_row = ttk.Frame(output_frame)
        dir_row.pack(fill=tk.X)
        
        self.output_path = tk.StringVar()
        output_entry = ttk.Entry(dir_row, textvariable=self.output_path)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(dir_row, text="Browse...", command=self.browse_output).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(dir_row, text="Open", command=self.open_output_directory).pack(side=tk.LEFT)
        
        # Favorites row
        fav_row = ttk.Frame(output_frame)
        fav_row.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(fav_row, text="Favorites:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.favorites_var = tk.StringVar()
        self.favorites_combo = ttk.Combobox(
            fav_row, 
            textvariable=self.favorites_var,
            state="readonly",
            width=40
        )
        self.favorites_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.favorites_combo.bind("<<ComboboxSelected>>", self.on_favorite_selected)
        self.update_favorites_combo()
        
        ttk.Button(fav_row, text="Add to Favorites", command=self.add_to_favorites).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(fav_row, text="Remove", command=self.remove_from_favorites).pack(side=tk.LEFT)
        
        # Checkboxes row
        checkbox_row = ttk.Frame(output_frame)
        checkbox_row.pack(fill=tk.X, pady=(5, 0))
        
        self.create_project_folder = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            checkbox_row,
            text="Create Project Folder",
            variable=self.create_project_folder
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        # PDF handling dropdown
        ttk.Label(checkbox_row, text="PDF:").pack(side=tk.LEFT, padx=(0, 5))
        self.pdf_action = tk.StringVar(value="Move PDF")
        self.pdf_action_combo = ttk.Combobox(
            checkbox_row,
            textvariable=self.pdf_action,
            values=["Move PDF", "Copy PDF", "Symbolic Link", "Symbolic Backlink", "Do Nothing"],
            state="readonly",
            width=16
        )
        self.pdf_action_combo.pack(side=tk.LEFT)
        
        # Tooltip for PDF action dropdown
        pdf_action_help = (
            "Move PDF: Move and rename PDF to output folder\n"
            "Copy PDF: Copy PDF to output folder (keeps original)\n"
            "Symbolic Link: Create symlink in output pointing to original\n"
            "Symbolic Backlink: Move PDF to output, symlink back to original location\n"
            "Do Nothing: Leave PDF in place, only create marker output"
        )
        ToolTip(self.pdf_action_combo, pdf_action_help)
        
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
    
    def update_favorites_combo(self):
        """Update the favorites combobox with current favorites."""
        display_names = [Path(f).name for f in self.favorites]
        self.favorites_combo['values'] = display_names
        if not display_names:
            self.favorites_var.set("")
    
    def on_favorite_selected(self, event=None):
        """Handle favorite selection from combobox."""
        idx = self.favorites_combo.current()
        if idx >= 0 and idx < len(self.favorites):
            self.output_path.set(self.favorites[idx])
    
    def add_to_favorites(self):
        """Add current output directory to favorites."""
        path = self.output_path.get().strip()
        if not path:
            messagebox.showwarning("No Directory", "Please enter an output directory first.")
            return
        if path in self.favorites:
            messagebox.showinfo("Already Exists", "This directory is already in favorites.")
            return
        self.favorites.append(path)
        self.save_favorites()
        self.update_favorites_combo()
    
    def remove_from_favorites(self):
        """Remove selected favorite from list."""
        idx = self.favorites_combo.current()
        if idx >= 0 and idx < len(self.favorites):
            del self.favorites[idx]
            self.save_favorites()
            self.update_favorites_combo()
    
    def update_input_favorites_combo(self):
        """Update the input favorites combobox."""
        display_names = [Path(f).name for f in self.input_favorites]
        self.input_fav_combo['values'] = display_names
        if display_names:
            self.input_fav_combo.current(0)
            self.input_fav_var.set(display_names[0])
    
    def on_input_favorite_selected(self, event=None):
        """Handle input favorite selection - immediately opens file browser."""
        self.browse_pdf()
    
    def get_input_start_directory(self):
        """Get the starting directory for the file browser."""
        idx = self.input_fav_combo.current()
        if idx >= 0 and idx < len(self.input_favorites):
            path = self.input_favorites[idx]
            if Path(path).exists():
                return path
        # Fallback to Downloads or home
        downloads = Path.home() / "Downloads"
        return str(downloads) if downloads.exists() else str(Path.home())
    
    def add_input_favorite(self):
        """Add a directory to input favorites."""
        directory = filedialog.askdirectory(title="Select Folder to Add to Favorites")
        if directory:
            if directory not in self.input_favorites:
                self.input_favorites.append(directory)
                self.save_favorites()
                self.update_input_favorites_combo()
                # Select the newly added favorite
                self.input_fav_combo.current(len(self.input_favorites) - 1)
            else:
                messagebox.showinfo("Already Exists", "This directory is already in favorites.")
    
    def remove_input_favorite(self):
        """Remove selected input favorite."""
        idx = self.input_fav_combo.current()
        if idx >= 0 and idx < len(self.input_favorites):
            del self.input_favorites[idx]
            self.save_favorites()
            self.update_input_favorites_combo()
        else:
            messagebox.showwarning("No Selection", "Please select a favorite to remove.")
    
    def open_output_directory(self):
        """Open the output directory in the system file manager."""
        path = self.output_path.get().strip()
        if not path:
            messagebox.showwarning("No Directory", "Please enter an output directory first.")
            return
        if not Path(path).exists():
            messagebox.showwarning("Directory Not Found", f"Directory does not exist:\n{path}")
            return
        
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", path])
            elif sys.platform == "win32":
                subprocess.run(["explorer", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open directory: {e}")
    
    def on_double_click(self, event):
        """Handle double-click on treeview for inline editing."""
        # Identify the region clicked
        region = self.pdf_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        
        # Get column and item
        column = self.pdf_tree.identify_column(event.x)
        item = self.pdf_tree.identify_row(event.y)
        
        if not item:
            return
        
        # Only allow editing the "Output Name" column (#2)
        if column != "#2":
            return
        
        # Get the bounding box of the cell
        bbox = self.pdf_tree.bbox(item, column)
        if not bbox:
            return
        
        # Destroy any existing edit entry
        self.cancel_edit()
        
        # Get current value (strip .pdf for editing)
        values = self.pdf_tree.item(item, "values")
        current_output_name = values[1] if len(values) > 1 else ""
        if current_output_name.lower().endswith(".pdf"):
            current_output_name = current_output_name[:-4]
        
        # Create entry widget for editing (use tk.Entry for full style control)
        self.edit_entry = tk.Entry(
            self.pdf_tree,
            background="#e0e0e0",         # Light grey background
            foreground="#000000",          # Black text
            insertbackground="#000000",    # Black cursor
            selectbackground="#0078d7",
            selectforeground="#ffffff",
            relief=tk.FLAT
        )
        self.edit_entry.insert(0, current_output_name)
        self.edit_entry.select_range(0, tk.END)
        
        # Position the entry over the cell
        self.edit_entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        self.edit_entry.focus_set()
        
        self.editing_item = item
        
        # Bind events for saving/canceling
        self.edit_entry.bind("<Return>", self.save_edit)
        self.edit_entry.bind("<Escape>", lambda e: self.cancel_edit())
        self.edit_entry.bind("<FocusOut>", self.save_edit)
    
    def save_edit(self, event=None):
        """Save the edited output name."""
        if not self.edit_entry or not self.editing_item:
            return
        
        new_value = self.edit_entry.get().strip()
        item = self.editing_item
        
        # Normalize: remove .pdf extension if user added it
        if new_value.lower().endswith(".pdf"):
            new_value = new_value[:-4].strip()
        
        # Get the file path from tag
        tags = self.pdf_tree.item(item, "tags")
        if tags:
            file_path = tags[0]
            self.output_names[file_path] = new_value
        
        # Update treeview - display with .pdf extension if name is provided
        values = list(self.pdf_tree.item(item, "values"))
        values[1] = f"{new_value}.pdf" if new_value else ""
        self.pdf_tree.item(item, values=values)
        
        self.cancel_edit()
    
    def cancel_edit(self):
        """Cancel inline editing."""
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None
        self.editing_item = None
    
    def get_filename_from_path_or_url(self, path_or_url):
        """Extract a clean filename (without extension) from a path or URL."""
        if path_or_url.startswith(('http://', 'https://')):
            # Parse URL to get filename
            parsed = urllib.parse.urlparse(path_or_url)
            filename = Path(urllib.parse.unquote(parsed.path)).name
        else:
            filename = Path(path_or_url).name
        
        # Remove .pdf extension
        if filename.lower().endswith('.pdf'):
            filename = filename[:-4]
        
        return filename
    
    def add_pdf_to_list(self, file_path, display_name=None):
        """Add a PDF file to the list with auto-filled output name."""
        if file_path in self.pdf_files:
            return False
        
        self.pdf_files.append(file_path)
        
        # Auto-fill output name with the filename
        base_name = self.get_filename_from_path_or_url(display_name or file_path)
        self.output_names[file_path] = base_name
        
        # Insert into treeview with file path as tag
        display = display_name if display_name else Path(file_path).name
        self.pdf_tree.insert(
            "",
            tk.END,
            values=(display, f"{base_name}.pdf"),
            tags=(file_path,)
        )
        return True
    
    def browse_pdf(self):
        """Open file dialog to select multiple PDFs."""
        start_dir = self.get_input_start_directory()
        filenames = filedialog.askopenfilenames(
            title="Select PDF Files",
            initialdir=start_dir,
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if filenames:
            for filename in filenames:
                self.add_pdf_to_list(filename)
            # Auto-set output directory to same as first PDF location
            if not self.output_path.get() and self.pdf_files:
                self.output_path.set(str(Path(self.pdf_files[0]).parent))
    
    def add_url(self):
        """Prompt user for a PDF URL and download it."""
        url = simpledialog.askstring(
            "Add PDF from URL",
            "Enter the URL of a PDF file:",
            parent=self.root
        )
        
        if not url:
            return
        
        url = url.strip()
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            messagebox.showerror("Invalid URL", "URL must start with http:// or https://")
            return
        
        # Check if it looks like a PDF
        parsed = urllib.parse.urlparse(url)
        path_lower = parsed.path.lower()
        if not path_lower.endswith('.pdf'):
            result = messagebox.askyesno(
                "Not a PDF?",
                "The URL doesn't end with .pdf. Continue anyway?"
            )
            if not result:
                return
        
        # Download in background
        self.log(f"Downloading: {url}\n")
        thread = threading.Thread(target=self.download_pdf, args=(url,), daemon=True)
        thread.start()
    
    def download_pdf(self, url):
        """Download a PDF from URL in background thread."""
        try:
            # Get filename from URL
            parsed = urllib.parse.urlparse(url)
            filename = Path(urllib.parse.unquote(parsed.path)).name
            if not filename or not filename.lower().endswith('.pdf'):
                filename = "downloaded.pdf"
            
            # Use the user's Downloads folder
            download_dir = Path.home() / "Downloads"
            if not download_dir.exists():
                download_dir.mkdir(parents=True, exist_ok=True)
            
            # Make filename unique if it already exists
            dest_path = download_dir / filename
            counter = 1
            while dest_path.exists():
                stem = Path(filename).stem
                dest_path = download_dir / f"{stem}_{counter}.pdf"
                counter += 1
            
            # Download with progress
            self.root.after(0, self.log, f"Saving to: {dest_path}\n")
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as response:
                total_size = response.headers.get('Content-Length')
                if total_size:
                    total_size = int(total_size)
                
                with open(dest_path, 'wb') as f:
                    downloaded = 0
                    chunk_size = 8192
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            pct = (downloaded / total_size) * 100
                            self.root.after(0, self.update_download_progress, pct)
            
            self.root.after(0, self.log, f"\n✓ Download complete!\n\n")
            
            # Add to list on main thread
            display_name = Path(urllib.parse.unquote(parsed.path)).name
            self.root.after(0, self.add_pdf_to_list, str(dest_path), display_name)
            
        except Exception as e:
            self.root.after(0, self.log, f"\n✗ Download failed: {e}\n\n")
    
    def update_download_progress(self, pct):
        """Update download progress in log (overwrites last line)."""
        # Simple progress update
        pass  # Could add a progress bar here
    
    def remove_selected_files(self):
        """Remove selected files from the list."""
        selected = self.pdf_tree.selection()
        for item in selected:
            tags = self.pdf_tree.item(item, "tags")
            if tags:
                file_path = tags[0]
                if file_path in self.pdf_files:
                    self.pdf_files.remove(file_path)
                if file_path in self.output_names:
                    del self.output_names[file_path]
            self.pdf_tree.delete(item)
    
    def clear_files(self):
        """Clear all files, output directory, and log."""
        # Clear treeview
        for item in self.pdf_tree.get_children():
            self.pdf_tree.delete(item)
        self.pdf_files.clear()
        self.output_names.clear()
        
        # Clear output path
        self.output_path.set("")
        
        # Clear log
        self.clear_log()
    
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
    
    def get_final_name(self, pdf_path):
        """Get the final output name for a PDF (without extension)."""
        custom_name = self.output_names.get(pdf_path, "").strip()
        if custom_name:
            # Remove .pdf extension if user accidentally added it
            if custom_name.lower().endswith(".pdf"):
                custom_name = custom_name[:-4]
            return custom_name
        else:
            # Use original filename without extension
            return Path(pdf_path).stem
    
    def get_marker_command(self, pdf_path, output_dir):
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
        
        cmd = [marker_cmd, pdf_path, "--output_dir", output_dir]
        
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
        
        # Capture current settings for the thread
        settings = {
            'pdf_files': list(self.pdf_files),
            'output_names': dict(self.output_names),
            'create_project_folder': self.create_project_folder.get(),
            'pdf_action': self.pdf_action.get(),  # "Move PDF", "Copy PDF", or "Do Nothing"
            'base_output_dir': self.output_path.get()
        }
        
        # Run in background thread
        thread = threading.Thread(target=self.run_conversion, args=(settings,), daemon=True)
        thread.start()
    
    def run_conversion(self, settings):
        """Run the conversion subprocess for each PDF file."""
        pdf_files = settings['pdf_files']
        total = len(pdf_files)
        successful = 0
        failed = 0
        
        try:
            for index, pdf_path in enumerate(pdf_files, 1):
                if not self.is_running:
                    break
                
                # Determine final name
                final_name = self.get_final_name(pdf_path)
                original_filename = Path(pdf_path).name
                
                # Log which file we're processing
                self.root.after(0, self.log, f"[{index}/{total}] Converting: {original_filename}\n")
                if final_name != Path(pdf_path).stem:
                    self.root.after(0, self.log, f"    → Output name: {final_name}\n")
                
                # Determine output directory
                base_output = settings['base_output_dir']
                if settings['create_project_folder']:
                    project_folder = Path(base_output) / final_name
                    marker_output_dir = str(project_folder)
                else:
                    project_folder = Path(base_output)
                    marker_output_dir = str(project_folder)
                
                # Create project folder if needed
                try:
                    project_folder.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self.root.after(0, self.log, f"\n✗ Failed to create folder: {e}\n\n")
                    failed += 1
                    continue
                
                # Determine the PDF path to use for marker based on pdf_action
                current_pdf_path = pdf_path
                pdf_action = settings['pdf_action']
                new_pdf_path = project_folder / f"{final_name}.pdf"
                
                try:
                    if pdf_action == "Move PDF" and Path(pdf_path) != new_pdf_path:
                        self.root.after(0, self.log, f"    Moving PDF to: {new_pdf_path}\n")
                        shutil.move(pdf_path, new_pdf_path)
                        current_pdf_path = str(new_pdf_path)
                    
                    elif pdf_action == "Copy PDF" and Path(pdf_path) != new_pdf_path:
                        self.root.after(0, self.log, f"    Copying PDF to: {new_pdf_path}\n")
                        shutil.copy2(pdf_path, new_pdf_path)
                        current_pdf_path = str(new_pdf_path)
                    
                    elif pdf_action == "Symbolic Link" and Path(pdf_path) != new_pdf_path:
                        # Create symlink in output folder pointing to original
                        self.root.after(0, self.log, f"    Creating symlink: {new_pdf_path} → {pdf_path}\n")
                        if new_pdf_path.exists():
                            new_pdf_path.unlink()
                        new_pdf_path.symlink_to(Path(pdf_path).resolve())
                        current_pdf_path = str(new_pdf_path)
                    
                    elif pdf_action == "Symbolic Backlink" and Path(pdf_path) != new_pdf_path:
                        # Move PDF to output, then symlink back to original location
                        original_path = Path(pdf_path)
                        self.root.after(0, self.log, f"    Moving PDF to: {new_pdf_path}\n")
                        shutil.move(pdf_path, new_pdf_path)
                        self.root.after(0, self.log, f"    Creating backlink: {original_path} → {new_pdf_path}\n")
                        original_path.symlink_to(new_pdf_path.resolve())
                        current_pdf_path = str(new_pdf_path)
                    
                    # "Do Nothing" - leave current_pdf_path as is
                    
                except Exception as e:
                    self.root.after(0, self.log, f"\n✗ Failed to handle PDF ({pdf_action}): {e}\n\n")
                    failed += 1
                    continue
                
                cmd = self.get_marker_command(current_pdf_path, marker_output_dir)
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
                    
                    # Rename marker output folder to append _marker_output
                    marker_created_folder = Path(marker_output_dir) / final_name
                    marker_renamed_folder = Path(marker_output_dir) / f"{final_name}_marker_output"
                    if marker_created_folder.exists() and marker_created_folder.is_dir():
                        try:
                            marker_created_folder.rename(marker_renamed_folder)
                            self.root.after(0, self.log, f"    Renamed output folder to: {final_name}_marker_output\n")
                        except Exception as e:
                            self.root.after(0, self.log, f"    Warning: Could not rename output folder: {e}\n")
                    
                    self.root.after(0, self.log, f"\n✓ {final_name} completed successfully!\n\n")
                elif self.is_running:
                    failed += 1
                    self.root.after(0, self.log, f"\n✗ {final_name} failed with exit code {return_code}\n\n")
            
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
