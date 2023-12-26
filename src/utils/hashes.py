"""Simple file hash tools for collision checking."""

import hashlib
from pathlib import Path


def hash_file(file_path: Path):
    """Compute the md5 hash of a file."""

    # md5 is insecure but good enough for this use case. It should help aleviate
    # hashing bottlenecks that other algorithms might produce
    md5_hash = hashlib.md5(usedforsecurity=False)
    with file_path.open("rb") as file:
        # Read each file in chunks of bytes
        CHUNK_SIZE = 4096
        # Loop through each chunk untill an empty byte string is returned
        for byte_block in iter(lambda: file.read(CHUNK_SIZE), b""):
            md5_hash.update(byte_block)
        # Convert the final hash value to a hexadecimal string
        return md5_hash.hexdigest()


def is_duplicate(*args: Path) -> bool:
    """Compares the hash of any number of files and returns a `bool` based on their
    duplicity.\n
    Best used when comparing 2 files."""

    # Sets can only have unique values
    hashes = set()
    for file in args:
        hashes.add(hash_file(file))
    # If `hashes` has less items than targets, there are duplicates among them
    if len(hashes) < len(args):
        return True
    else:
        return False


def is_present(*args: Path, target_dir: Path, extension: str):
    """Gets the hashes for all the files in the target folder and checks if the files
    in `args` are already there.

    Returns a `False` if the file is not present or a `tuple` mapping the new file to
    it's hash and duplicate files:

    .. code-block:: python
        ["new_file_name", {"hash": ["duplicate1", "duplicate2"]}], [...]

    """

    hashes = {}
    # Non-recursively loop through a filtered list of files in the target folder
    for file in target_dir.glob(f"*.{extension}"):
        file_hash = hash_file(file)
        file_name = file.name
        hashes[file_name] = file_hash

    duplicates = {}
    for new_file in args:
        new_file_hash = hash_file(new_file)
        # Check if the file's hash is already present in `hashes`
        duplicates_list = []
        if new_file_hash in hashes.values():
            # Get a list of the files that match that hash
            duplicate = [file for file, hash in hashes.items() if hash == new_file_hash]
            duplicates_list = duplicate
            # Map the duplicates list to `new_file_hash` and the file that's being checked
            duplicates[new_file.name] = {new_file_hash: duplicates_list}

    if duplicates:
        return duplicates
    else:
        return False


def find_all_duplicates(start_path: Path):
    """Find and group duplicate files based on their hash."""

    hashes = {}
    for file_path in start_path.rglob("*"):
        if file_path.is_file():
            file_hash = hash_file(file_path)
            if file_hash in hashes:
                hashes[file_hash].append(file_path)
            else:
                hashes[file_hash] = [file_path]
    return {hash: paths for hash, paths in hashes.items() if len(paths) > 1}
