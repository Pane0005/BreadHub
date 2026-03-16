import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import os
import base64
from cryptography.fernet import Fernet

# --- Colors and Fonts ---
BREAD_COLOR = "#bb8926"
BG_COLOR = "#2b2b2b"
LOG_BG = "#1e1e1e"
FONT = ("FiraCode Nerd Font Mono", 11)

class BreadEncrypt:
    def __init__(self, root):
        self.root = root
        self.root.title("BreadEncrypt - BreadScript Console")
        self.root.geometry("700x500")
        self.root.configure(bg=BG_COLOR)

        # Core attributes
        self.key_file = os.path.expanduser("~/.breadencrypt_key")
        self.key = self.load_or_create_key()
        self.cipher = Fernet(self.key)

        # GUI
        self.create_widgets()

    # --- Key Management ---
    def load_or_create_key(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            return key

    # --- GUI ---
    def create_widgets(self):
        # Title
        ttk.Label(self.root, text="BreadEncrypt Console", font=("FiraCode Nerd Font Mono", 16, "bold"), foreground=BREAD_COLOR, background=BG_COLOR).pack(pady=(10,5))
        ttk.Label(self.root, text="Type BreadScript commands below", font=("FiraCode Nerd Font Mono", 11, "italic"), foreground=BREAD_COLOR, background=BG_COLOR).pack(pady=(0,10))

        # Console Output
        self.log_text = scrolledtext.ScrolledText(self.root, height=15, width=80, bg=LOG_BG, fg=BREAD_COLOR, font=FONT)
        self.log_text.pack(fill='both', expand=True, padx=10, pady=5)

        # Command Entry
        entry_frame = tk.Frame(self.root, bg=BG_COLOR)
        entry_frame.pack(fill='x', padx=10, pady=5)
        self.command_entry = ttk.Entry(entry_frame, font=FONT)
        self.command_entry.pack(side='left', fill='x', expand=True)
        self.command_entry.bind("<Return>", self.execute_command)

        ttk.Button(entry_frame, text="Run", command=self.execute_command, style='Button.TButton').pack(side='left', padx=5)

        # Style for buttons
        style = ttk.Style()
        style.configure('Button.TButton', font=FONT, foreground=BG_COLOR, background=BREAD_COLOR)

        self.log("Welcome to BreadEncrypt v.0.1.4 by Доктор Bread! ")

    # --- Logging ---
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    # --- Command Parsing ---
    def execute_command(self, event=None):
        cmd_line = self.command_entry.get().strip()
        self.command_entry.delete(0, tk.END)
        if not cmd_line:
            return
        self.log(f"> {cmd_line}")

        parts = cmd_line.split()
        cmd = parts[0].lower()
        args = parts[1:]

        try:
            if cmd == "/help":
                self.log("BreadScript Commands:\n"
                         "/toast <file>     - Encrypt a file\n"
                         "/slice <file>     - Decrypt a file\n"
                         "/butter keygen    - Generate a new key\n"
                         "/jam <string>     - Encrypt a string\n"
                         "/spread <file>    - Copy and encrypt a file")
            elif cmd == "/toast":
                if not args: self.log("Usage: /toast <file>"); return
                self.encrypt_file(args[0])
            elif cmd == "/slice":
                if not args: self.log("Usage: /slice <file>"); return
                self.decrypt_file(args[0])
            elif cmd == "/butter":
                if args and args[0] == "keygen":
                    self.generate_new_key()
                else:
                    self.log("Usage: /butter keygen")
            elif cmd == "/jam":
                if not args: self.log("Usage: /jam <string>"); return
                self.encrypt_string(" ".join(args))
            elif cmd == "/spread":
                if not args: self.log("Usage: /spread <file>"); return
                self.copy_and_encrypt(args[0])
            else:
                self.log(f"Unknown command: {cmd}. Type /help for commands.")
        except Exception as e:
            self.log(f"Error: {e}")

    # --- Command Implementations ---
    def encrypt_file(self, path):
        if not os.path.exists(path):
            self.log(f"File not found: {path}")
            return
        with open(path, "rb") as f:
            data = f.read()
        enc = self.cipher.encrypt(data)
        out_path = path + ".bread"
        with open(out_path, "wb") as f:
            f.write(enc)
        self.log(f"File encrypted: {out_path}")

    def decrypt_file(self, path):
        if not os.path.exists(path):
            self.log(f"File not found: {path}")
            return
        with open(path, "rb") as f:
            data = f.read()
        dec = self.cipher.decrypt(data)
        out_path = path.replace(".bread","") if path.endswith(".bread") else path + ".dec"
        with open(out_path, "wb") as f:
            f.write(dec)
        self.log(f"File decrypted: {out_path}")

    def generate_new_key(self):
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        with open(self.key_file, "wb") as f:
            f.write(self.key)
        self.log("New encryption key generated and saved!")

    def encrypt_string(self, text):
        enc = self.cipher.encrypt(text.encode())
        self.log(f"Encrypted string: {enc.decode()}")

    def copy_and_encrypt(self, path):
        if not os.path.exists(path):
            self.log(f"File not found: {path}")
            return
        with open(path, "rb") as f:
            data = f.read()
        enc = self.cipher.encrypt(data)
        out_path = path + ".breadcopy"
        with open(out_path, "wb") as f:
            f.write(enc)
        self.log(f"File copied and encrypted: {out_path}")

# --- Main ---
if __name__ == "__main__":
    root = tk.Tk()
    app = BreadEncrypt(root)
    # Mostra subito la scritta all’apertura
    app.log("Type /help for commands...")
    root.mainloop()
