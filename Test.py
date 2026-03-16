#!/usr/bin/env python3
from pathlib import Path
import time

downloads = Path.home() / "Downloads"

# Wait a moment to ensure Bread Analyzer is running
time.sleep(2)

# Create a new suspicious file
fake_file = downloads / "obvious_threat.exe"
fake_file.write_text("This is a harmless dummy file that should trigger Bread Analyzer!")

print(f"Fake suspicious file created: {fake_file}")
