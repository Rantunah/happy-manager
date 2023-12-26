import hashlib
from pathlib import Path


def hash_file(file_path: Path):
    """Compute the SHA-256 hash of a file."""

    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as file:
        # Read each file in chunks of bytes
        CHUNK_SIZE = 4096
        # Loop through each chunk untill an empty byte string is returned
        for byte_block in iter(lambda: file.read(CHUNK_SIZE), b""):
            sha256_hash.update(byte_block)
        # Convert the final hash value to a hexadecimal string
        return sha256_hash.hexdigest()


def find_duplicates(start_path: Path):
    """Find and group duplicate files based on their SHA-256 hash."""

    hashes = {}
    for file_path in start_path.rglob("*"):
        if file_path.is_file():
            file_hash = hash_file(file_path)
            if file_hash in hashes:
                hashes[file_hash].append(file_path)
            else:
                hashes[file_hash] = [file_path]
    return {hash: paths for hash, paths in hashes.items() if len(paths) > 1}


target_folder = Path("/mnt/d/Codigo/colchoes/scripts_happy/dev/all")

duplicates = find_duplicates(target_folder)

for hash_value, files in duplicates.items():
    print(f"Duplicate files for hash {hash_value}:")
    for file in files:
        print(f" - {file}")
