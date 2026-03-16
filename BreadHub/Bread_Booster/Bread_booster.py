#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import psutil
import threading
import time
import os
import json
import signal
from datetime import datetime
import subprocess

# --- Colors and Fonts ---
BREAD_COLOR = "#bb8926"
BG_COLOR = "#2b2b2b"
LOG_BG = "#1e1e1e"
FONT = ("FiraCode Nerd Font Mono", 11)

class BreadBst:
    def __init__(self, root):
        self.root = root
        self.root.title("BreadBst - Performance Optimizer")
        self.root.geometry("950x750")
        self.root.configure(bg=BG_COLOR)
        self.archived_processes = []
        self.closed_apps = []

        # Core attributes
        self.is_boosting = False
        self.processed_pids = {} # Stores pids that have been niced/stopped
        self.config_file = os.path.expanduser("~/.breadbst_config.json")
        self.archived_processes = [] # The new list for protected processes, starts empty

        # GUI
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        self.create_widgets()

        # Load configuration
        self.load_config()
        self.update_process_list()

    # --- Config ---
    def load_config(self):
        """Loads the archived processes list from a config file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.archived_processes = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    def save_config(self):
        """Saves the archived processes list to a config file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.archived_processes, f, indent=2)
        except IOError as e:
            self.log_message(f"Failed to save config: {e}", "ERROR")

    # --- Styles ---
    def configure_styles(self):
        self.style.configure('Title.TLabel', background=BG_COLOR, foreground=BREAD_COLOR, font=("FiraCode Nerd Font Mono", 16, "bold"))
        self.style.configure('SubTitle.TLabel', background=BG_COLOR, foreground=BREAD_COLOR, font=("FiraCode Nerd Font Mono", 12, "italic"))
        self.style.configure('Status.TLabel', background=BG_COLOR, foreground=BREAD_COLOR, font=FONT)
        self.style.configure('Info.TLabel', background=BG_COLOR, foreground="white", font=FONT)
        self.style.configure('Danger.TLabel', background=BG_COLOR, foreground="#FF4444", font=("FiraCode Nerd Font Mono", 11, "bold"))
        self.style.configure('Button.TButton', font=FONT, foreground=BG_COLOR, background=BREAD_COLOR)
        self.style.configure('Warning.TButton', font=FONT, foreground="white", background="#FF4444")
        self.style.configure('License.TLabel', background=BG_COLOR, foreground="white", font=("FiraCode Nerd Font Mono", 8))
        # Custom style for the checkbox
        self.style.configure('TCheckbutton', background=BG_COLOR, foreground='white', font=FONT)

    # --- GUI ---
    def create_widgets(self):
        # Title
        ttk.Label(self.root, text="Bread Booster", style='Title.TLabel').pack(pady=(10,0))
        ttk.Label(self.root, text="v 2.0.0 - Archive Edition", style='SubTitle.TLabel').pack(pady=(0,10))

        # Status frame
        status_frame = tk.Frame(self.root, bg=BG_COLOR)
        status_frame.pack(fill='x', padx=20, pady=5)
        self.status_label = ttk.Label(status_frame, text="Status: Idle", style='Status.TLabel')
        self.status_label.pack(side='left')
        self.processed_label = ttk.Label(status_frame, text="Processed: 0", style='Danger.TLabel')
        self.processed_label.pack(side='right')
        self.mode_label = ttk.Label(status_frame, text="Performance Mode: OFF", style='Status.TLabel')
        self.mode_label.pack(side='right', padx=20)

        # Options Frame
        options_frame = tk.Frame(self.root, bg=BG_COLOR)
        options_frame.pack(pady=5)
        self.aggressive_var = tk.BooleanVar(value=False)
        aggressive_check = ttk.Checkbutton(options_frame, text="Use Aggressive Mode (SIGSTOP - DANGEROUS)",
                                           variable=self.aggressive_var, style='TCheckbutton')
        aggressive_check.pack()

        # Buttons frame
        button_frame = tk.Frame(self.root, bg=BG_COLOR)
        button_frame.pack(pady=10)

        row1 = tk.Frame(button_frame, bg=BG_COLOR)
        row1.pack(side='top', pady=2)
        self.boost_button = ttk.Button(row1, text="Enable Boost", command=self.toggle_boost, style='Button.TButton')
        self.boost_button.pack(side='left', padx=2)
        ttk.Button(row1, text="Refresh List", command=self.update_process_list, style='Button.TButton').pack(side='left', padx=2)

        row2 = tk.Frame(button_frame, bg=BG_COLOR)
        row2.pack(side='top', pady=2)
        ttk.Button(row2, text="Add to Archive", command=self.add_to_archive, style='Button.TButton').pack(side='left', padx=2)
        ttk.Button(row2, text="Remove from Archive", command=self.remove_from_archive, style='Button.TButton').pack(side='left', padx=2)

        # Process List Frame
        list_frame = tk.Frame(self.root, bg=BG_COLOR)
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)

        ttk.Label(list_frame, text="Running Processes:", style='Status.TLabel').pack(anchor='w')

        # Treeview for process list
        self.process_tree = ttk.Treeview(list_frame, columns=('pid', 'name', 'status', 'cpu', 'mem'), show='headings', height=15)
        self.process_tree.pack(fill='both', expand=True, pady=5)

        self.process_tree.heading('pid', text='PID')
        self.process_tree.heading('name', text='Name')
        self.process_tree.heading('status', text='Status')
        self.process_tree.heading('cpu', text='CPU %')
        self.process_tree.heading('mem', text='Memory %')

        self.process_tree.column('pid', width=80)
        self.process_tree.column('name', width=200)
        self.process_tree.column('status', width=120)
        self.process_tree.column('cpu', width=80)
        self.process_tree.column('mem', width=80)

        # Log
        ttk.Label(self.root, text="Activity Log:", style='Status.TLabel').pack(anchor='w', padx=20, pady=(10,5))
        self.log_text = scrolledtext.ScrolledText(self.root, height=8, width=80, bg=LOG_BG, fg=BREAD_COLOR, font=FONT)
        self.log_text.pack(fill='x', padx=20, pady=5)

        # --- License notice bottom-right ---
        license_text = ("BreadBst v2.0.0 by Доктор Bread\n"
                        "Copyright (c) 2026 Доктор Bread - BreadBst. All Rights Reserved.\n"
                        "Proprietary software. Unauthorized use, copying, or distribution is prohibited.")
        self.license_label = ttk.Label(self.root, text=license_text, style='License.TLabel', justify='right')
        self.license_label.pack(side='bottom', anchor='e', padx=10, pady=5)

    # --- Core Logic ---
    def is_archived(self, proc_name):
        """Check if a process name is in the archived list."""
        return any(archived in proc_name.lower() for archived in self.archived_processes)

    def toggle_boost(self):
        """Toggles the performance boost mode."""
        if not self.is_boosting:
            self.start_boost()
        else:
            self.stop_boost()

    def start_boost(self):
        """Starts the performance boost by lowering priority or suspending non-archived processes."""
        self.is_boosting = True
        self.boost_button.config(text="Disable Boost", style='Warning.TButton')
        self.mode_label.config(text="Performance Mode: ON")

        mode = "Aggressive (SIGSTOP)" if self.aggressive_var.get() else "Safe (Nice/IOnice)"
        self.log_message(f"Performance Boost ENABLED. Using {mode} on non-archived processes...", "INFO")

        processed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                if pid == os.getpid(): # Don't process BreadBst itself
                    continue
                if self.is_archived(name):
                    continue
                try:
                    cmdline = proc.cmdline()
                    if cmdline:
                        self.closed_apps.append(cmdline)
                except:
                    pass

                if proc.status() == psutil.STATUS_STOPPED and self.aggressive_var.get():
                    continue

                if self.aggressive_var.get():
                    # --- AGGRESSIVE MODE: SUSPEND ---
                    os.kill(pid, signal.SIGSTOP)
                    self.processed_pids[pid] = {'name': name, 'type': 'stopped'}
                else:
                    # --- SAFE MODE: LOWER PRIORITY ---
                    p = psutil.Process(pid)

                    original_nice = p.nice()

                    original_ionice = p.ionice()

                    try:
                        original_ionice = p.ionice()
                    except:
                        original_ionice = None

                    p.nice(19) # Lowest CPU priority

                    try:
                        p.ionice(psutil.IOPRIO_CLASS_IDLE) # Lowest I/O priority
                    except:
                        pass

                    self.processed_pids[pid] = {
                        'name': name,
                        'type': 'niced',
                        'original_nice': original_nice,
                        'original_ionice': original_ionice
                    }

                processed_count += 1
                self.log_message(f"Processed '{name}' (PID: {pid})", "INFO")

            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                continue

        self.log_message(f"Processed {processed_count} processes.", "SUCCESS")
        self.update_process_list()

    def stop_boost(self):
        """Resumes or restores priority of all processed processes."""
        self.is_boosting = False
        self.boost_button.config(text="Enable Boost", style='Button.TButton')
        self.mode_label.config(text="Performance Mode: OFF")
        self.log_message("Performance Boost DISABLED. Restoring all processes...", "INFO")

        restored_count = 0
        for pid, info in list(self.processed_pids.items()):
            try:
                if info['type'] == 'stopped':
                    # --- RESUME SUSPENDED PROCESS ---
                    os.kill(pid, signal.SIGCONT)
                elif info['type'] == 'niced':
                    # --- RESTORE PRIORITY ---
                    p = psutil.Process(pid)
                    p.nice(info.get('original_nice', 0))
                    # IONice restoration is more complex and can fail, so we wrap it
                    try:
                        p.ionice(info.get('original_ionice', psutil.IOPRIO_CLASS_NONE))
                    except psutil.AccessDenied:
                        self.log_message(f"Could not restore I/O priority for PID {pid}", "WARNING")

                restored_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                continue
            del self.processed_pids[pid]

        self.log_message(f"Restored {restored_count} processes.", "SUCCESS")
        self.update_process_list()

    def update_process_list(self):
        """Refreshes the process tree view."""
        # Clear existing items
        for i in self.process_tree.get_children():
            self.process_tree.delete(i)

        # Populate with current processes
        processes_to_show = []
        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                processes_to_show.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by CPU usage
        processes_to_show.sort(key=lambda p: p['cpu_percent'] or 0, reverse=True)

        for pinfo in processes_to_show[:100]: # Show top 100 processes
            pid = pinfo['pid']
            name = pinfo['name']
            status = "Running"

            if pid in self.processed_pids:
                status = "Niced" if self.processed_pids[pid]['type'] == 'niced' else "Suspended"
            elif self.is_archived(name):
                status = "Archived"

            cpu = f"{pinfo['cpu_percent']:.1f}" if pinfo['cpu_percent'] is not None else "N/A"
            mem = f"{pinfo['memory_percent']:.1f}" if pinfo['memory_percent'] is not None else "N/A"

            self.process_tree.insert('', 'end', values=(pid, name, status, cpu, mem))

        self.processed_label.config(text=f"Processed: {len(self.processed_pids)}")

    # --- Configuration Management ---
    def add_to_archive(self):
        """Opens a dialog to add a process to the archive list."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Process to Archive")
        dialog.geometry("400x120")
        dialog.configure(bg=BG_COLOR)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Enter process name to protect (e.g., 'discord'):", style='Status.TLabel').pack(pady=(10,5))
        entry = ttk.Entry(dialog, width=40, font=FONT)
        entry.pack(pady=5)
        entry.focus_set()

        def add():
            proc_name = entry.get().strip()
            if not proc_name:
                messagebox.showerror("Error", "Process name cannot be empty.", parent=dialog)
                return
            if proc_name.lower() in [p.lower() for p in self.archived_processes]:
                messagebox.showerror("Error", f"'{proc_name}' is already in the archive.", parent=dialog)
                return

            self.archived_processes.append(proc_name)
            self.save_config()
            self.log_message(f"Added '{proc_name}' to archive.", "INFO")
            self.update_process_list()
            messagebox.showinfo("Success", f"'{proc_name}' added to archive.", parent=dialog)
            dialog.destroy()

        button_frame = tk.Frame(dialog, bg=BG_COLOR)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Add", command=add, style='Button.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, style='Warning.TButton').pack(side='left', padx=5)

    def remove_from_archive(self):
        """Opens a dialog to remove a process from the archive list."""
        if not self.archived_processes:
            messagebox.showinfo("Info", "The archive is already empty.", parent=self.root)
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Remove Process from Archive")
        dialog.geometry("400x150")
        dialog.configure(bg=BG_COLOR)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Select a process to unarchive:", style='Status.TLabel').pack(pady=(10,5))

        listbox = tk.Listbox(dialog, bg=LOG_BG, fg=BREAD_COLOR, font=FONT, selectmode=tk.SINGLE)
        listbox.pack(fill='both', expand=True, padx=20, pady=5)
        for proc in self.archived_processes:
            listbox.insert(tk.END, proc)

        def remove():
            selection = listbox.curselection()
            if not selection:
                messagebox.showerror("Error", "Please select a process to remove.", parent=dialog)
                return

            proc_name = listbox.get(selection[0])
            self.archived_processes.remove(proc_name)
            self.save_config()
            self.log_message(f"Removed '{proc_name}' from archive.", "INFO")
            self.update_process_list()
            messagebox.showinfo("Success", f"'{proc_name}' removed from archive.", parent=dialog)
            dialog.destroy()

        button_frame = tk.Frame(dialog, bg=BG_COLOR)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Remove", command=remove, style='Warning.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, style='Button.TButton').pack(side='left', padx=5)

    # --- Logging ---
    def log_message(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        self.root.after(0, self._update_log, log_entry)

    def _update_log(self, entry):
        self.log_text.insert(tk.END, entry)
        self.log_text.see(tk.END)

    # --- Cleanup on Exit ---
    def on_closing(self):
        """Ensures all processes are restored before exiting."""
        if self.is_boosting:
            self.stop_boost()
        self.root.destroy()

# --- Main ---
if __name__ == "__main__":
    root = tk.Tk()
    app = BreadBst(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
