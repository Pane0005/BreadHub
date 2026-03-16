#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import json
import os
import hashlib
import secrets
import string
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime
import pyperclip

# --- Colors and Fonts ---
BREAD_COLOR = "#bb8926"
BG_COLOR = "#2b2b2b"
LOG_BG = "#1e1e1e"
FONT = ("FiraCode Nerd Font Mono", 11)

class BreadPM:
    def __init__(self, root):
        self.root = root
        self.root.title("BreadPM - Password Manager")
        self.root.geometry("800x700")
        self.root.configure(bg=BG_COLOR)

        # Core attributes
        self.data_file = os.path.expanduser("~/.breadpm_vault.json")
        self.master_password_hash = None
        self.vault = {}
        self.is_unlocked = False

        # GUI
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        self.create_login_screen()

    # --- Styles ---
    def configure_styles(self):
        self.style.configure('Title.TLabel', background=BG_COLOR, foreground=BREAD_COLOR, font=("FiraCode Nerd Font Mono", 16, "bold"))
        self.style.configure('SubTitle.TLabel', background=BG_COLOR, foreground=BREAD_COLOR, font=("FiraCode Nerd Font Mono", 12, "italic"))
        self.style.configure('Status.TLabel', background=BG_COLOR, foreground=BREAD_COLOR, font=FONT)
        self.style.configure('Danger.TLabel', background=BG_COLOR, foreground="#FF4444", font=("FiraCode Nerd Font Mono", 11, "bold"))
        self.style.configure('Button.TButton', font=FONT, foreground=BG_COLOR, background=BREAD_COLOR)
        self.style.configure('Warning.TButton', font=FONT, foreground="white", background="#FF4444")
        self.style.configure('License.TLabel', background=BG_COLOR, foreground="white", font=("FiraCode Nerd Font Mono", 8))

    # --- Login Screen ---
    def create_login_screen(self):
        self.clear_window()

        login_frame = tk.Frame(self.root, bg=BG_COLOR)
        login_frame.pack(expand=True)

        ttk.Label(login_frame, text="Bread Password Manager", style='Title.TLabel').pack(pady=(0, 20))
        ttk.Label(login_frame, text="v 1.0.0 by Доктор Bread", style='SubTitle.TLabel').pack(pady=(0, 40))

        ttk.Label(login_frame, text="Master Password:", style='Status.TLabel').pack()
        self.master_password_entry = ttk.Entry(login_frame, show="*", width=30, font=FONT)
        self.master_password_entry.pack(pady=10)
        self.master_password_entry.bind('<Return>', lambda event: self.unlock_vault())

        button_frame = tk.Frame(login_frame, bg=BG_COLOR)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="Unlock", command=self.unlock_vault, style='Button.TButton').pack(side='left', padx=5)
        if os.path.exists(self.data_file):
            ttk.Button(button_frame, text="Create New Vault", command=self.create_new_vault_prompt, style='Warning.TButton').pack(side='left', padx=5)
        else:
            ttk.Button(button_frame, text="Create New Vault", command=self.create_new_vault_prompt, style='Button.TButton').pack(side='left', padx=5)

        self.login_status_label = ttk.Label(login_frame, text="", style='Status.TLabel')
        self.login_status_label.pack(pady=10)

        # --- License notice bottom-right ---
        license_text = ("BreadPM v1.0.0 by Доктор Bread\n"
                        "Copyright (c) 2026 Доктор Bread - BreadPM. All Rights Reserved.\n"
                        "Proprietary software. Unauthorized use, copying, or distribution is prohibited.")
        self.license_label = ttk.Label(self.root, text=license_text, style='License.TLabel', justify='right')
        self.license_label.pack(side='bottom', anchor='e', padx=10, pady=5)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def create_new_vault_prompt(self):
        if os.path.exists(self.data_file):
            if not messagebox.askyesno("Overwrite?", "A vault already exists. Are you sure you want to create a new one? This will delete the old one."):
                return

        self.clear_window()
        create_frame = tk.Frame(self.root, bg=BG_COLOR)
        create_frame.pack(expand=True)

        ttk.Label(create_frame, text="Create New Vault", style='Title.TLabel').pack(pady=(0, 20))

        ttk.Label(create_frame, text="Set Master Password:", style='Status.TLabel').pack()
        self.new_pass_entry1 = ttk.Entry(create_frame, show="*", width=30, font=FONT)
        self.new_pass_entry1.pack(pady=5)

        ttk.Label(create_frame, text="Confirm Master Password:", style='Status.TLabel').pack()
        self.new_pass_entry2 = ttk.Entry(create_frame, show="*", width=30, font=FONT)
        self.new_pass_entry2.pack(pady=5)
        self.new_pass_entry2.bind('<Return>', lambda event: self.create_new_vault())

        button_frame = tk.Frame(create_frame, bg=BG_COLOR)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Create", command=self.create_new_vault, style='Button.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Back", command=self.create_login_screen, style='Button.TButton').pack(side='left', padx=5)

        self.create_status_label = ttk.Label(create_frame, text="", style='Danger.TLabel')
        self.create_status_label.pack(pady=10)

    def create_new_vault(self):
        pw1 = self.new_pass_entry1.get()
        pw2 = self.new_pass_entry2.get()
        if not pw1 or not pw2:
            self.create_status_label.config(text="Passwords cannot be empty.")
            return
        if pw1 != pw2:
            self.create_status_label.config(text="Passwords do not match.")
            return

        self.master_password_hash = hashlib.sha256(pw1.encode()).hexdigest()
        self.cipher_suite = self._create_cipher_suite(pw1)
        self.vault = {}
        self.save_vault()
        self.is_unlocked = True
        self.create_main_screen()

    def unlock_vault(self):
        master_password = self.master_password_entry.get()
        if not master_password:
            self.login_status_label.config(text="Please enter the master password.", foreground="red")
            return

        if not os.path.exists(self.data_file):
            self.login_status_label.config(text="No vault found. Create a new one.", foreground="orange")
            return

        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.master_password_hash = data.get('master_password_hash')
                if not self.master_password_hash or hashlib.sha256(master_password.encode()).hexdigest() != self.master_password_hash:
                    self.login_status_label.config(text="Incorrect master password.", foreground="red")
                    return

            self.cipher_suite = self._create_cipher_suite(master_password)
            encrypted_vault = data.get('vault')
            if encrypted_vault:
                decrypted_vault_bytes = self.cipher_suite.decrypt(encrypted_vault.encode())
                self.vault = json.loads(decrypted_vault_bytes.decode())
            else:
                self.vault = {}

            self.is_unlocked = True
            self.create_main_screen()
        except Exception as e:
            self.login_status_label.config(text=f"Failed to unlock vault: {e}", foreground="red")

    def _create_cipher_suite(self, password: str) -> Fernet:
        password_bytes = password.encode()
        salt = b'breadsalt_' # In a real app, use a unique, random salt per vault
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return Fernet(key)

    def save_vault(self):
        if not self.is_unlocked:
            return
        try:
            vault_json = json.dumps(self.vault)
            encrypted_vault = self.cipher_suite.encrypt(vault_json.encode())
            data_to_save = {
                'master_password_hash': self.master_password_hash,
                'vault': encrypted_vault.decode()
            }
            with open(self.data_file, 'w') as f:
                json.dump(data_to_save, f, indent=2)
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save vault: {e}")

    # --- Main Screen ---
    def create_main_screen(self):
        self.clear_window()

        # Title
        ttk.Label(self.root, text="Bread Password Manager", style='Title.TLabel').pack(pady=(10,0))
        ttk.Label(self.root, text="v 1..0.0 by Доктор Bread", style='SubTitle.TLabel').pack(pady=(0,10))

        # Frame principale
        main_frame = tk.Frame(self.root, bg=BG_COLOR)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Lista account
        self.account_listbox = tk.Listbox(main_frame, bg=LOG_BG, fg=BREAD_COLOR, font=FONT, height=15, width=50)
        self.account_listbox.pack(side='left', fill='both', expand=True, padx=(0,10))
        self.account_listbox.bind('<<ListboxSelect>>', self.display_selected_entry)

        # Scrollbar
        scrollbar = tk.Scrollbar(main_frame)
        scrollbar.pack(side='left', fill='y')
        self.account_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.account_listbox.yview)

        # Detail / actions frame
        detail_frame = tk.Frame(main_frame, bg=BG_COLOR)
        detail_frame.pack(side='left', fill='both', expand=True)

        ttk.Label(detail_frame, text="Account:", style='Status.TLabel').pack(anchor='w')
        self.account_entry = ttk.Entry(detail_frame, width=30, font=FONT)
        self.account_entry.pack(pady=5)

        ttk.Label(detail_frame, text="Username / Email:", style='Status.TLabel').pack(anchor='w')
        self.username_entry = ttk.Entry(detail_frame, width=30, font=FONT)
        self.username_entry.pack(pady=5)

        ttk.Label(detail_frame, text="Password:", style='Status.TLabel').pack(anchor='w')
        self.password_entry = ttk.Entry(detail_frame, width=30, font=FONT)
        self.password_entry.pack(pady=5)

        ttk.Button(detail_frame, text="Generate Random Password", command=self.generate_password, style='Button.TButton').pack(pady=5)
        ttk.Button(detail_frame, text="Add / Update Entry", command=self.add_or_update_entry, style='Button.TButton').pack(pady=5)
        ttk.Button(detail_frame, text="Delete Entry", command=self.delete_entry, style='Warning.TButton').pack(pady=5)
        ttk.Button(detail_frame, text="Copy Password", command=self.copy_password_to_clipboard, style='Button.TButton').pack(pady=5)
        ttk.Button(detail_frame, text="Logout", command=self.logout, style='Button.TButton').pack(pady=20)

        # Log / status
        self.status_label = ttk.Label(self.root, text="", style='Status.TLabel')
        self.status_label.pack(pady=5)

        self.refresh_account_list()

    # --- Vault Operations ---
    def refresh_account_list(self):
        self.account_listbox.delete(0, tk.END)
        for account in sorted(self.vault.keys()):
            self.account_listbox.insert(tk.END, account)

    def display_selected_entry(self, event=None):
        selection = self.account_listbox.curselection()
        if selection:
            account = self.account_listbox.get(selection[0])
            entry = self.vault.get(account, {})
            self.account_entry.delete(0, tk.END)
            self.account_entry.insert(0, account)
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, entry.get('username',''))
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, entry.get('password',''))

    def add_or_update_entry(self):
        account = self.account_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not account or not password:
            self.status_label.config(text="Account and Password cannot be empty.", foreground="red")
            return
        self.vault[account] = {'username': username, 'password': password}
        self.save_vault()
        self.refresh_account_list()
        self.status_label.config(text=f"Entry for '{account}' saved.", foreground=BREAD_COLOR)

    def delete_entry(self):
        account = self.account_entry.get().strip()
        if account in self.vault:
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{account}'?"):
                del self.vault[account]
                self.save_vault()
                self.refresh_account_list()
                self.account_entry.delete(0, tk.END)
                self.username_entry.delete(0, tk.END)
                self.password_entry.delete(0, tk.END)
                self.status_label.config(text=f"Entry '{account}' deleted.", foreground="orange")
        else:
            self.status_label.config(text="No such entry to delete.", foreground="red")

    def copy_password_to_clipboard(self):
        account = self.account_entry.get().strip()
        entry = self.vault.get(account)
        if entry and 'password' in entry:
            pyperclip.copy(entry['password'])
            self.status_label.config(text="Password copied to clipboard.", foreground=BREAD_COLOR)
        else:
            self.status_label.config(text="No password found to copy.", foreground="red")

    def generate_password(self, length=16):
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, password)
        self.status_label.config(text="Random password generated.", foreground=BREAD_COLOR)

    def logout(self):
        self.is_unlocked = False
        self.vault = {}
        self.master_password_hash = None
        self.create_login_screen()

# --- Main ---
if __name__ == "__main__":
    root = tk.Tk()
    app = BreadPM(root)
    root.mainloop()
