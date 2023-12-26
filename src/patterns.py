"""Handles all pattern specific data, files and objects"""
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# TODO: `Settings` is passed a couple of times here. It could be better to assign it to the class altogether or figure out if it should be loaded from the file directly
from settings import Settings
from utils.files import FileData, get_data, list_files_extension

# TODO: The file format is hardcoded here as there is currently no need to expand to "dsg". Consider moving this to `config.toml`
FORMAT = "dst"


@dataclass
class Pattern:
    name: str
    original_name: str
    number: int
    year: int
    size_kb: int | float
    hash: str
    flash_drive: str

    @classmethod
    def from_file(cls, file: Path, settings: Settings):
        data: FileData = get_data(file)

        original_name = data.file_name
        year = data.year_modified
        size_kb = data.size_kb
        hash = data.hash
        # Get the number from the `latest_pattern` in the backups folder if the query is
        # successful
        try:
            number = int(latest_pattern(settings.backup_dir.parent).stem[:3])
        # `sort_files` depends on the name being numeric so it will raise an index error
        # if the latest file is not found, because of a wrong name format
        except IndexError:
            number = 0
        name = str(number).zfill(3) + str(year)

        pattern = cls(
            name=name,
            original_name=original_name,
            number=number,
            year=year,
            size_kb=size_kb,
            hash=hash,
            flash_drive=settings.flash_drive_name,
        )

        pattern.bump_pattern_number()

        return pattern

    def bump_pattern_number(self) -> None:
        """Bumps `Pattern.number` by one digit and updates the `Pattern.name`."""

        self.number += 1
        self.name = str(self.number).zfill(3) + str(self.year)

    def to_csv_log(self, settings: Settings) -> bool:
        """Manages a csv log of the inserted files and returns whsether creation or update
        was succsessful or not.\n
        The log is stored in the parent of the backups directory."""

        csv_updates = settings.backup_dir.parent / "updates.csv"
        # Context manager creates the file, so the check must happen before that
        csv_exists = csv_updates.exists()
        # Open the file to write the headders it it's new, otherwise, append data
        try:
            with open(
                csv_updates, mode="a" if csv_exists else "w", newline=""
            ) as csv_file:
                writer = csv.writer(csv_file)
                # Wrtite the headders if the file is new
                if not csv_exists:
                    headers = [
                        "name",
                        "original_name",
                        "size_kb",
                        "hash",
                        "flash_drive",
                    ]
                    writer.writerow(headers)

                row_data = [
                    self.name,
                    self.original_name,
                    self.size_kb,
                    self.hash,
                    self.flash_drive,
                ]
                writer.writerow(row_data)
                return True

        except OSError:
            return False


def sort_key(file: Path, key: Literal["year", "number"]) -> tuple[int, int]:
    """Extracts the year and number from the file name for sorting.
    `key` defines wich one of the name's elements the file will be sorted by."""

    base_name = file.stem
    number = int(base_name[:3])
    year = int(base_name[3:])

    if key == "year":
        return year, number
    elif key == "number":
        return number, year
    else:
        raise ValueError("`key` must be either 'year' or 'number'.")


def sort_files(
    files: list[Path], key: Literal["year", "number"], reverse: bool
) -> list:
    """Returns the files list sorted by a specified key (`year` or `number`) and
    direction."""

    # `sorted` `key` only accepts a `Callable`, so a `lambda` is used as a wrapper for
    # `sort_key`
    return sorted(files, key=lambda file: sort_key(file, key), reverse=reverse)


def latest_pattern(folder: Path, year: int | None = None) -> Path:
    """Returns the `Path` of the most recent pattern in the specified folder.
    if `year` is specified, retruns the the latest file from that year."""

    files_list = list_files_extension(folder, extension=FORMAT)
    # Filter the list of files by the year in their names if `year` is specified
    if year:
        filtered_list = [file for file in files_list if int(file.stem[3:]) == year]
        files_list = filtered_list
    # Return only the first element of the list
    return sort_files(files_list, key="year", reverse=True)[0]


def list_present_years(dir: Path) -> set[int]:
    """Returns a `set` with the years that are currently present in the specified path"""

    years = set()
    for file in list_files_extension(dir, extension=FORMAT):
        years.add(int(file.stem[3:]))
    return years
