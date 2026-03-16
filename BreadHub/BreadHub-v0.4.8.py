import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import sys
import json
from datetime import datetime

# --- Colors and Fonts ---
BREAD_COLOR = "#bb8926"
BG_COLOR = "#2b2b2b"
LOG_BG = "#1e1e1e"
FONT = ("FiraCode Nerd Font Mono", 11)

class BreadHub:
    def __init__(self, root):
        self.root = root
        self.root.title("BreadHub - Script Manager")
        self.root.geometry("700x500")
        self.root.configure(bg=BG_COLOR)

        # Configuration
        self.config_file = os.path.expanduser("~/.breadhub_config.json")
        self.scripts = self.load_config()

        # GUI
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        self.create_widgets()

        self.update_script_list()

    # --- Configuration ---
    def load_config(self):
        """Loads script paths from the config file."""
        default_scripts = {
            "BreadAv": "BreadAv-v0.9.9.py",
            "BreadPm": "BreadPm.py"
        }
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return default_scripts

    def save_config(self):
        """Saves the current script paths to the config file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.scripts, f, indent=2)
        except IOError as e:
            messagebox.showerror("Error", f"Could not save configuration: {e}")

    # --- Styles ---
    def configure_styles(self):
        self.style.configure('Title.TLabel', background=BG_COLOR, foreground=BREAD_COLOR, font=("FiraCode Nerd Font Mono", 16, "bold"))
        self.style.configure('SubTitle.TLabel', background=BG_COLOR, foreground=BREAD_COLOR, font=("FiraCode Nerd Font Mono", 12, "italic"))
        self.style.configure('Status.TLabel', background=BG_COLOR, foreground=BREAD_COLOR, font=FONT)
        self.style.configure('Button.TButton', font=FONT, foreground=BG_COLOR, background=BREAD_COLOR)
        self.style.configure('Warning.TButton', font=FONT, foreground="white", background="#FF4444")
        self.style.configure('License.TLabel', background=BG_COLOR, foreground="white", font=("FiraCode Nerd Font Mono", 8))

    # --- GUI ---
    def create_widgets(self):
        # Title
        ttk.Label(self.root, text="Bread Hub", style='Title.TLabel').pack(pady=(10,0))
        ttk.Label(self.root, text="v 1.0.0 by Доктор Bread", style='SubTitle.TLabel').pack(pady=(0,10))

        # Main Frame
        main_frame = tk.Frame(self.root, bg=BG_COLOR)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Script List Frame
        list_frame = tk.Frame(main_frame, bg=BG_COLOR)
        list_frame.pack(fill='both', expand=True)

        ttk.Label(list_frame, text="Available Scripts:", style='Status.TLabel').pack(anchor='w')

        # Listbox with Scrollbar
        list_container = tk.Frame(list_frame, bg=BG_COLOR)
        list_container.pack(fill='both', expand=True, pady=5)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side='right', fill='y')

        self.script_listbox = tk.Listbox(list_container, bg=LOG_BG, fg=BREAD_COLOR, font=FONT, yscrollcommand=scrollbar.set, selectmode=tk.SINGLE)
        self.script_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.script_listbox.yview)

        # Details Frame
        self.details_frame = tk.Frame(main_frame, bg=BG_COLOR)
        self.details_frame.pack(fill='x', pady=10)
        self.details_label = ttk.Label(self.details_frame, text="Select a script to see its path.", style='Status.TLabel')
        self.details_label.pack(side='left', expand=True)

        # Buttons Frame
        button_frame = tk.Frame(main_frame, bg=BG_COLOR)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(button_frame, text="Launch", command=self.launch_script, style='Button.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Set Path", command=self.set_script_path, style='Button.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Remove", command=self.remove_script, style='Warning.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Add New", command=self.add_new_script, style='Button.TButton').pack(side='left', padx=5)

        # --- License notice bottom-right ---
        license_text = ("BreadHub v1.0.0 by Доктор Bread\n"
                        "Copyright (c) 2026 Доктор Bread - BreadHub. All Rights Reserved.\n"
                        "Proprietary software. Unauthorized use, copying, or distribution is prohibited.")
        self.license_label = ttk.Label(self.root, text=license_text, style='License.TLabel', justify='right')
        self.license_label.pack(side='bottom', anchor='e', padx=10, pady=5)

    # --- Script Management ---
    def update_script_list(self):
        """Refreshes the listbox with the current script names."""
        self.script_listbox.delete(0, tk.END)
        for name in self.scripts:
            self.script_listbox.insert(tk.END, name)
        self.details_label.config(text="Select a script to see its path.")

    def get_selected_script_name(self):
        """Returns the name of the currently selected script."""
        selection = self.script_listbox.curselection()
        if not selection:
            return None
        return self.script_listbox.get(selection[0])

    def launch_script(self):
        """Launches the selected script in a new process."""
        script_name = self.get_selected_script_name()
        if not script_name:
            messagebox.showwarning("No Selection", "Please select a script to launch.")
            return

        script_path = self.scripts.get(script_name)
        if not script_path or not os.path.exists(script_path):
            messagebox.showerror("File Not Found", f"The script for '{script_name}' was not found at:\n{script_path}\n\nPlease set the correct path.")
            return

        try:
            # Use the same Python interpreter that is running BreadHub
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch '{script_name}':\n{e}")

    def set_script_path(self):
        """Opens a dialog to set the path for the selected script."""
        script_name = self.get_selected_script_name()
        if not script_name:
            messagebox.showwarning("No Selection", "Please select a script to change its path.")
            return

        current_path = self.scripts.get(script_name, "")
        file_path = filedialog.askopenfilename(
            title=f"Select path for {script_name}",
            initialfile=current_path,
            filetypes=[("Python Scripts", "*.py"), ("All Files", "*.*")]
        )
        if file_path:
            self.scripts[script_name] = file_path
            self.save_config()
            self.details_label.config(text=f"Path for '{script_name}' set to: {file_path}")
            messagebox.showinfo("Success", f"Path for '{script_name}' has been updated.")

    def remove_script(self):
        """Removes the selected script from the list."""
        script_name = self.get_selected_script_name()
        if not script_name:
            messagebox.showwarning("No Selection", "Please select a script to remove.")
            return

        if messagebox.askyesno("Confirm Remove", f"Are you sure you want to remove '{script_name}' from the list?"):
            del self.scripts[script_name]
            self.save_config()
            self.update_script_list()

    def add_new_script(self):
        """Adds a new script to the list."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Script")
        dialog.geometry("400x250")
        dialog.configure(bg=BG_COLOR)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Script Name:", style='Status.TLabel').pack(pady=(10,5))
        name_entry = ttk.Entry(dialog, width=40, font=FONT)
        name_entry.pack(pady=5)
        name_entry.focus_set()

        ttk.Label(dialog, text="Script Path:", style='Status.TLabel').pack(pady=(10,5))
        path_entry = ttk.Entry(dialog, width=40, font=FONT)
        path_entry.pack(pady=5)

        def browse_path():
            path = filedialog.askopenfilename(title="Select Script File", filetypes=[("Python Scripts", "*.py"), ("All Files", "*.*")])
            if path:
                path_entry.delete(0, tk.END)
                path_entry.insert(0, path)

        browse_button = ttk.Button(dialog, text="Browse...", command=browse_path, style='Button.TButton')
        browse_button.pack(pady=5)

        def add_script():
            name = name_entry.get().strip()
            path = path_entry.get().strip()
            if not name or not path:
                messagebox.showerror("Error", "Both name and path must be provided.", parent=dialog)
                return
            if name in self.scripts:
                messagebox.showerror("Error", f"A script named '{name}' already exists.", parent=dialog)
                return
            if not os.path.exists(path):
                messagebox.showerror("Error", f"The file at '{path}' does not exist.", parent=dialog)
                return

            self.scripts[name] = path
            self.save_config()
            self.update_script_list()
            messagebox.showinfo("Success", f"Script '{name}' added successfully.", parent=dialog)
            dialog.destroy()

        button_frame = tk.Frame(dialog, bg=BG_COLOR)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Add", command=add_script, style='Button.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, style='Warning.TButton').pack(side='left', padx=5)

    def on_listbox_select(self, event):
        """Updates the details label when a script is selected."""
        script_name = self.get_selected_script_name()
        if script_name:
            script_path = self.scripts.get(script_name, "Path not set.")
            self.details_label.config(text=f"Path for '{script_name}': {script_path}")
        else:
            self.details_label.config(text="Select a script to see its path.")

# --- Main ---
if __name__ == "__main__":
    root = tk.Tk()
    app = BreadHub(root)
    root.mainloop()
