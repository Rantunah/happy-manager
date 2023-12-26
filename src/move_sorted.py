import os
import shutil
from pathlib import Path


def sort_key(filename):
    """Extracts the year and number from the file name for sorting."""
    base_name = Path(filename).stem
    number = int(base_name[:3])
    year = int(base_name[3:])
    return year, number


SOURCE = Path(
    "\\\\192.168.1.2\\Documentos\\AA J. J. Louro\\Colchões\\Bordados\\Happy\\HAPPY2"
)
TARGET = Path("F:\\")

files = os.listdir(SOURCE)

sorted_files = sorted(files, key=sort_key, reverse=True)

for file_name in sorted_files:
    source_path = SOURCE / file_name
    destination_path = TARGET / file_name
    shutil.copy2(source_path, destination_path)
    print(f"Copied {file_name} to {TARGET}")

print("All files copied successfully.")
