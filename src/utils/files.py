"""Generic file system operations, such as listing files, folders or
coppying them."""

import datetime
import shutil
from pathlib import Path
from typing import NamedTuple

from utils.hashes import hash_file


class FileCopyError(Exception):
    """Raised when one or more files could not be copied and provides access to a list
    of those files."""

    def __init__(self, message, failed_files):
        super().__init__(message)
        self.falied_files = failed_files


class FileData(NamedTuple):
    """Object that encapsulates data from a file."""

    file_name: str
    size_kb: int | float
    hash: str
    year_modified: int


def list_files_extension(folder: Path, extension: str) -> list[Path]:
    """Returns a list of all the files in the current folder, filtered by extension."""

    return [file for file in folder.glob(f"*.{extension}")]


def copy_files(files: list[Path], target_dir: Path) -> bool:
    """Copies all files in the file list to a target directory. Returns `True` if all
    files were coppied successfully or a list of all the files that didn't.
    """

    # Loop through all the files and copy them to the target directory
    failed = []
    for file in files:
        new_file = Path(shutil.copy2(file, target_dir))
        # Append any files that couldn't be coppied to a list
        if new_file.exists():
            continue
        else:
            failed.append(file.name)

    # If any file couldn't be saved, raise a custom exception
    if failed:
        raise FileCopyError(
            f"The following {len(failed)} files could not be copied: {failed}",
            failed_files=failed,
        )
    else:
        return True


def rename_file(file: Path, new_name: str) -> Path:
    """Renames an existing files and returns the new file's `Path` object"""

    return file.rename(file.with_stem(new_name))


# TODO: Not completely accurate because of how `round` handles `float`
def convert_bytes(
    size_in_bytes, target_unit: str | None = None, suffix=False
) -> int | float | str:
    """
    Converts bytes to other size units.

    Can take an optional `target_unit` for direct conversion.\n
    If `suffix` is set `True`, a formatted strting will be returned instead of a number.
    """

    # If the unit is invalid raise an error with the correct units
    size_units = ["B", "KB", "MB", "GB", "TB", "PB"]
    if target_unit and target_unit.upper() not in size_units:
        raise ValueError(f"Invalid size unit. Must be: {', '.join(size_units)}")

    # Automatically determine the unit if not provided
    if not target_unit:
        for unit in size_units:
            if size_in_bytes < 1024:
                break
            size_in_bytes /= 1024
    else:
        unit_index = size_units.index(target_unit.upper())
        size_in_bytes /= 1024**unit_index
        unit = size_units[unit_index]

    # Round and format the result
    if size_in_bytes % 1:
        size_in_bytes = round(size_in_bytes, 2)
    else:
        size_in_bytes = int(size_in_bytes)
    return f"{size_in_bytes} {unit}" if suffix else size_in_bytes  # type: ignore


def get_data(file: Path) -> FileData:
    """Returns a `NamedTuple` object with some data from a file.

    .. code-block:: python
        (
            "file_name": str,
            "size_kb": int | float,
            "hash": str,
            "year_modified": int
        )
    """

    name = file.stem
    # Initialize file statistics object to get the size and date
    file_stats = file.stat()
    # Convert the size from `bytes` to `kilobites`
    # MYPY: Result will never be a `str` here
    size_kilobytes: int | float = convert_bytes(file_stats.st_size, "kb")  # type:ignore
    file_hash = hash_file(file)
    # `st_ctime` is a timestamp so it needs to be converted to a date
    modified_date = datetime.datetime.fromtimestamp(file_stats.st_mtime).date()
    year = modified_date.year

    return FileData(
        file_name=name,
        size_kb=size_kilobytes,
        hash=file_hash,
        year_modified=year,
    )


# TODO: Extension is hardcoded here but should be moved into `config.toml` in case other extensions are ever supported
def wipe_directory(dir: Path, extension: str = "dst") -> None:
    """Erase all the files of a specified extension in a directory"""

    for file in dir.glob(f"*.{extension}"):
        file.unlink()


def is_appendable(file: Path) -> bool:
    """Check if it's possible to append data to a file."""

    try:
        target_file = open(str(file), "a")
    except PermissionError:
        return False
    else:
        target_file.close()

    return True
