import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import psutil
import threading
import time
import os
import hashlib
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import queue
import subprocess

# --- Colors and Fonts ---
BREAD_COLOR = "#bb8926"
BG_COLOR = "#2b2b2b"
LOG_BG = "#1e1e1e"
FONT = ("FiraCode Nerd Font Mono", 11)

class BreadDefender:
    def __init__(self, root):
        self.root = root
        self.root.title("Bread Defender - Arch Linux Protection")
        self.root.geometry("900x700")
        self.root.configure(bg=BG_COLOR)

        # Threat queue
        self.threat_queue = queue.Queue()
        self.quarantine_dir = os.path.expanduser("~/.bread_defender_quarantine")
        os.makedirs(self.quarantine_dir, exist_ok=True)

        # Security lists
        self.whitelist_file = os.path.expanduser("~/.bread_defender_whitelist.json")
        self.blacklist_file = os.path.expanduser("~/.bread_defender_blacklist.json")
        self.whitelist = self.load_json_file(self.whitelist_file, [])
        self.blacklist = self.load_json_file(self.blacklist_file, [])

        # Detection settings
        self.suspicious_file_extensions = ['.exe', '.scr', '.bat', '.cmd', '.com', '.pif', '.vbs', '.js', '.jar']
        self.suspicious_network_ports = [4444, 5555, 6666, 7777, 8888, 9999, 31337, 12345]
        self.monitored_paths = ['/home', '/tmp', '/var/tmp']
        self.auto_quarantine = True
        self.monitoring = True
        self.real_time_protection = True
        self.observer = None

        # GUI
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        self.create_widgets()

        # Background services
        self.start_system_monitoring()
        self.start_network_monitoring()
        self.process_threat_queue()

        # Start performance stats
        self.update_performance_stats()

    # --- JSON helpers ---
    def load_json_file(self, file_path, default):
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return default

    def save_json_file(self, file_path, data):
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.log_message(f"Failed to save {file_path}: {e}", "ERROR")

    # --- Styles ---
    def configure_styles(self):
        self.style.configure('Title.TLabel', background=BG_COLOR, foreground=BREAD_COLOR, font=("FiraCode Nerd Font Mono", 16, "bold"))
        self.style.configure('SubTitle.TLabel', background=BG_COLOR, foreground=BREAD_COLOR, font=("FiraCode Nerd Font Mono", 12, "italic"))
        self.style.configure('Status.TLabel', background=BG_COLOR, foreground=BREAD_COLOR, font=FONT)
        self.style.configure('Danger.TLabel', background=BG_COLOR, foreground="#FF4444", font=("FiraCode Nerd Font Mono", 11, "bold"))
        self.style.configure('Button.TButton', font=FONT, foreground=BG_COLOR, background=BREAD_COLOR)
        self.style.configure('Warning.TButton', font=FONT, foreground="white", background="#FF4444")

    # --- GUI ---
    def create_widgets(self):
        # Title
        ttk.Label(self.root, text="Bread Defender", style='Title.TLabel').pack(pady=(10,0))
        ttk.Label(self.root, text="v 0.9.8 by Доктор Bread", style='SubTitle.TLabel').pack(pady=(0,10))

        # Status frame
        status_frame = tk.Frame(self.root, bg=BG_COLOR)
        status_frame.pack(fill='x', padx=20, pady=5)
        self.status_label = ttk.Label(status_frame, text="Status: Active", style='Status.TLabel')
        self.status_label.pack(side='left')
        self.threat_label = ttk.Label(status_frame, text="Threats Found: 0", style='Danger.TLabel')
        self.threat_label.pack(side='right')
        self.protection_label = ttk.Label(status_frame, text="Real-time: ON", style='Status.TLabel')
        self.protection_label.pack(side='right', padx=20)

        # Buttons frame
        button_frame = tk.Frame(self.root, bg=BG_COLOR)
        button_frame.pack(pady=10)

        row1 = tk.Frame(button_frame, bg=BG_COLOR)
        row1.pack(side='top', pady=2)
        ttk.Button(row1, text="Scan File", command=self.scan_file, style='Button.TButton').pack(side='left', padx=2)
        ttk.Button(row1, text="Scan System", command=self.scan_system, style='Button.TButton').pack(side='left', padx=2)
        ttk.Button(row1, text="Deep Scan", command=self.deep_scan, style='Button.TButton').pack(side='left', padx=2)
        ttk.Button(row1, text="Network Scan", command=self.network_scan, style='Button.TButton').pack(side='left', padx=2)

        row2 = tk.Frame(button_frame, bg=BG_COLOR)
        row2.pack(side='top', pady=2)
        ttk.Button(row2, text="Toggle Monitor", command=self.toggle_monitoring, style='Button.TButton').pack(side='left', padx=2)
        ttk.Button(row2, text="Real-time", command=self.toggle_realtime, style='Button.TButton').pack(side='left', padx=2)
        ttk.Button(row2, text="Auto Quarantine", command=self.toggle_auto_quarantine, style='Button.TButton').pack(side='left', padx=2)
        ttk.Button(row2, text="Clean Temp", command=self.cleanup_temp, style='Button.TButton').pack(side='left', padx=2)

        row3 = tk.Frame(button_frame, bg=BG_COLOR)
        row3.pack(side='top', pady=2)
        ttk.Button(row3, text="View Quarantine", command=self.view_quarantine, style='Button.TButton').pack(side='left', padx=2)
        ttk.Button(row3, text="Manage Whitelist", command=self.manage_whitelist, style='Button.TButton').pack(side='left', padx=2)
        ttk.Button(row3, text="Security Report", command=self.generate_report, style='Button.TButton').pack(side='left', padx=2)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill='x', padx=20, pady=5)

        # Log
        ttk.Label(self.root, text="Security Log:", style='Status.TLabel').pack(anchor='w', padx=20, pady=(10,5))
        self.log_text = scrolledtext.ScrolledText(self.root, height=12, width=80, bg=LOG_BG, fg=BREAD_COLOR, font=FONT)
        self.log_text.pack(fill='both', expand=True, padx=20, pady=5)

        # --- Performance Frame ---
        perf_frame = tk.Frame(self.root, bg=BG_COLOR)
        perf_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(perf_frame, text="CPU Usage:", style='Status.TLabel').grid(row=0, column=0, sticky='w')
        self.cpu_label = ttk.Label(perf_frame, text="0%", style='Status.TLabel')
        self.cpu_label.grid(row=0, column=1, sticky='w', padx=5)

        ttk.Label(perf_frame, text="RAM Usage:", style='Status.TLabel').grid(row=1, column=0, sticky='w')
        self.ram_label = ttk.Label(perf_frame, text="0%", style='Status.TLabel')
        self.ram_label.grid(row=1, column=1, sticky='w', padx=5)

        ttk.Label(perf_frame, text="GPU Usage:", style='Status.TLabel').grid(row=2, column=0, sticky='w')
        self.gpu_label = ttk.Label(perf_frame, text="N/A", style='Status.TLabel')
        self.gpu_label.grid(row=2, column=1, sticky='w', padx=5)

        ttk.Label(perf_frame, text="CPU Temp:", style='Status.TLabel').grid(row=0, column=2, sticky='w', padx=20)
        self.cpu_temp_label = ttk.Label(perf_frame, text="N/A", style='Status.TLabel')
        self.cpu_temp_label.grid(row=0, column=3, sticky='w', padx=5)

        ttk.Label(perf_frame, text="GPU Temp:", style='Status.TLabel').grid(row=1, column=2, sticky='w', padx=20)
        self.gpu_temp_label = ttk.Label(perf_frame, text="N/A", style='Status.TLabel')
        self.gpu_temp_label.grid(row=1, column=3, sticky='w', padx=5)

    # --- Logging ---
    def log_message(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        self.root.after(0, self._update_log, log_entry)
        if level == "THREAT":
            self.root.after(0, self._update_threat_count)

    def _update_log(self, entry):
        self.log_text.insert(tk.END, entry)
        self.log_text.see(tk.END)

    def _update_threat_count(self):
        current = int(self.threat_label.cget('text').split(': ')[1])
        self.threat_label.config(text=f"Threats Found: {current + 1}")

    # --- Threat queue ---
    def process_threat_queue(self):
        def worker():
            while True:
                try:
                    threat = self.threat_queue.get()
                    if threat:
                        self.log_message(f"Threat detected: {threat}", "THREAT")
                        if self.auto_quarantine and os.path.exists(threat):
                            self.quarantine_file(threat)
                    self.threat_queue.task_done()
                except Exception as e:
                    self.log_message(f"Threat queue error: {e}", "ERROR")
                time.sleep(0.1)
        threading.Thread(target=worker, daemon=True).start()

    # --- Quarantine ---
    def quarantine_file(self, file_path):
        try:
            base = os.path.basename(file_path)
            target = os.path.join(self.quarantine_dir, base)
            os.rename(file_path, target)
            self.log_message(f"File quarantined: {target}", "INFO")
        except Exception as e:
            self.log_message(f"Failed to quarantine {file_path}: {e}", "ERROR")

    # --- File scanning ---
    def scan_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        self.progress.start()
        threading.Thread(target=self._scan_file_thread, args=(file_path,), daemon=True).start()

    def _scan_file_thread(self, file_path):
        try:
            self.log_message(f"Scanning file: {file_path}")
            threats_found = 0
            ext = os.path.splitext(file_path)[1].lower()
            if ext in self.suspicious_file_extensions:
                self.threat_queue.put(file_path)
                threats_found += 1
            if os.access(file_path, os.X_OK) and any(temp in file_path for temp in ['/tmp','/var/tmp']):
                self.threat_queue.put(file_path)
                threats_found += 1
            size = os.path.getsize(file_path)
            if size > 50*1024*1024:
                self.log_message(f"LARGE FILE ALERT: {file_path} ({size/1024/1024:.1f} MB)", "WARNING")
            if threats_found == 0:
                self.log_message(f"File scan complete: {file_path}. No threats detected.")
        finally:
            self.progress.stop()

    # --- System scan ---
    def scan_system(self):
        self.progress.start()
        threading.Thread(target=self._scan_system_thread, daemon=True).start()

    def _scan_system_thread(self):
        try:
            self.log_message("Starting system scan...")
            for proc in psutil.process_iter(['pid','name']):
                try:
                    name = proc.info['name'].lower()
                    if any(bad in name for bad in ['malware','virus','trojan']):
                        self.threat_queue.put(f"{name} (PID {proc.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            self.log_message("System scan complete.")
        finally:
            self.progress.stop()

    # --- Placeholder functions ---
    def deep_scan(self): self.log_message("Deep scan not implemented yet", "INFO")
    def network_scan(self): self.log_message("Network scan not implemented yet", "INFO")
    def toggle_monitoring(self): self.monitoring = not self.monitoring; self.log_message(f"Monitoring {'enabled' if self.monitoring else 'disabled'}")
    def toggle_realtime(self): self.real_time_protection = not self.real_time_protection; self.protection_label.config(text=f"Real-time: {'ON' if self.real_time_protection else 'OFF'}")
    def toggle_auto_quarantine(self): self.auto_quarantine = not self.auto_quarantine; self.log_message(f"Auto Quarantine {'enabled' if self.auto_quarantine else 'disabled'}")
    def cleanup_temp(self): self.log_message("Temp cleanup not implemented yet", "INFO")
    def view_quarantine(self): self.log_message("View Quarantine not implemented yet", "INFO")
    def manage_whitelist(self): self.log_message("Manage Whitelist not implemented yet", "INFO")
    def generate_report(self): self.log_message("Security Report not implemented yet", "INFO")

    # --- Background monitoring ---
    def start_system_monitoring(self):
        if not self.monitoring:
            return
        class MonitorHandler(FileSystemEventHandler):
            def __init__(self, app):
                self.app = app
            def on_created(self, event):
                if not event.is_directory:
                    self.app.log_message(f"New file detected: {event.src_path}")
                    self.app.threat_queue.put(event.src_path)
        self.observer = Observer()
        handler = MonitorHandler(self)
        for path in self.monitored_paths:
            if os.path.exists(path):
                self.observer.schedule(handler, path, recursive=True)
        self.observer.start()
        self.log_message("Real-time system monitoring started")

    def start_network_monitoring(self):
        def monitor():
            while True:
                conns = psutil.net_connections()
                for conn in conns:
                    if conn.laddr and conn.laddr.port in self.suspicious_network_ports:
                        self.threat_queue.put(f"Suspicious connection on port {conn.laddr.port}")
                time.sleep(5)
        threading.Thread(target=monitor, daemon=True).start()

    # --- Performance stats ---
    def update_performance_stats(self):
        cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_label.config(text=f"{cpu_percent}%")
        self.cpu_label.config(foreground=self.get_color(cpu_percent))
        mem = psutil.virtual_memory()
        ram_percent = mem.percent
        self.ram_label.config(text=f"{ram_percent}%")
        self.ram_label.config(foreground=self.get_color(ram_percent))
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                cpu_temp = max([t.current for t in temps['coretemp']])
                self.cpu_temp_label.config(text=f"{cpu_temp}°C")
                self.cpu_temp_label.config(foreground=self.get_color(cpu_temp, temp=True))
            else:
                self.cpu_temp_label.config(text="N/A")
        except Exception:
            self.cpu_temp_label.config(text="N/A")
        try:
            gpu_info = subprocess.check_output(['nvidia-smi','--query-gpu=utilization.gpu,temperature.gpu','--format=csv,noheader,nounits'])
            gpu_util, gpu_temp = gpu_info.decode().strip().split(',')
            gpu_util = int(gpu_util)
            gpu_temp = int(gpu_temp)
            self.gpu_label.config(text=f"{gpu_util}%")
            self.gpu_label.config(foreground=self.get_color(gpu_util))
            self.gpu_temp_label.config(text=f"{gpu_temp}°C")
            self.gpu_temp_label.config(foreground=self.get_color(gpu_temp, temp=True))
        except Exception:
            self.gpu_label.config(text="N/A")
            self.gpu_temp_label.config(text="N/A")
        self.root.after(2000, self.update_performance_stats)

    def get_color(self, value, temp=False):
        if temp:
            if value < 60: return "green"
            elif value < 80: return "orange"
            else: return "red"
        else:
            if value < 50: return "green"
            elif value < 80: return "orange"
            else: return "red"

# --- Splash Screen ---
class SplashScreen:
    def __init__(self, root, duration=3):
        self.root = root
        self.duration = duration
        self.root.overrideredirect(True)
        self.root.geometry("500x300+500+200")
        self.root.configure(bg=BREAD_COLOR)
        label = tk.Label(root, text="Bread Defender", font=("FiraCode Nerd Font Mono", 24, "bold"), bg=BREAD_COLOR, fg=BG_COLOR)
        label.pack(expand=True)
        self.progress = ttk.Progressbar(root, mode='indeterminate', length=300)
        self.progress.pack(pady=20)
        self.progress.start(10)
        root.after(duration*1000, self.destroy)

    def destroy(self):
        self.progress.stop()
        self.root.destroy()

# --- Main ---
if __name__ == "__main__":
    splash_root = tk.Tk()
    splash = SplashScreen(splash_root, 3)
    splash_root.mainloop()
    root = tk.Tk()
    app = BreadDefender(root)
    root.mainloop()
