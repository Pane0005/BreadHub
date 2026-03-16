#!/usr/bin/env python3
from pathlib import Path

# Path to Downloads folder
downloads = Path.home() / "Downloads"

# Create a fake suspicious file
fake_file = downloads / "malware.exe"
fake_file.write_text("This is a harmless dummy file meant to trigger Bread Analyzer.")

print(f"Fake suspicious file created: {fake_file}")
