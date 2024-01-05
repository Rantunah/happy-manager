"""Handles all pattern specific data, files and objects"""
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

# TODO: `Settings` is passed a couple of times here. It could be better to assign it to the class altogether or figure out if it should be loaded from the file directly
from settings import Settings
from utils.files import FileData, get_data, list_files_extension

# TODO: The file format is hardcoded here as there is currently no need to expand to "dsg". Consider moving this to `config.toml`
FORMAT = "dst"


@dataclass
class Pattern:
    original_name: str
    number: int
    year: int
    size_kb: int | float
    hash: str
    flash_drive: str
    # `name` has a default value to allow the factory to build the object without
    # knowing it
    name: str = "?"

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
            number = 1

        pattern = cls(
            original_name=original_name,
            number=number,
            year=year,
            size_kb=size_kb,
            hash=hash,
            flash_drive=settings.flash_drive_name,
        )

        if not pattern.valid_numbers():
            raise ValueError(
                "`pattern.number` and/or `pattern.year` are not within \
            expected ranges."
            )

        # Do nothing for the first pattern of a new year
        pattern.name_from_numbers()
        if pattern.number == 1:
            pass
        else:
            pattern.bump_pattern_number()

        return pattern

    def valid_numbers(self) -> bool:
        """Checks if all the values for `number` and `year `fall within the expected
        range."""

        if not isinstance(self.number, int) or self.number not in range(1, 1000):
            raise ValueError("`self.number` must be an integer between `1` and `999`")

        # Check that the year is not larger than the present year or smaller than a
        # reasonable number
        year_today = datetime.now().date().year
        REASONABLE_YEAR = 1997
        if self.year > year_today or self.year < REASONABLE_YEAR:
            raise ValueError(
                f"`self.year` must be an integer between `{year_today}` and \
                `{REASONABLE_YEAR}`"
            )
        return True

    def name_from_numbers(self) -> str:
        """Returns a `str` object from the `number` padded to 3 digits, concatenated
        to the `year`."""
        return str(self.number).zfill(3) + str(self.year)

    def bump_pattern_number(self) -> None:
        """Bumps `Pattern.number` by one digit and updates the `Pattern.name`."""

        self.number += 1
        self.name = self.name_from_numbers()

    def to_csv_log(self, settings: Settings) -> bool:
        """Manages a csv log of the inserted files and returns whether creation or update
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

    # Serialize the filename into the correct number types
    base_name = file.stem
    try:
        number = int(base_name[:3])
        year = int(base_name[3:])
    # Set the numbers to `None` if the values are not compatible with `int`
    except ValueError as e:
        if str(e).startswith("invalid literal for int()"):
            pass
        number = None
        year = None

    if year and number:
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

    # Filters out all the files which names are alphanumeric (only numbers allowed)
    files = [
        file for file in files if file.stem[:3].isdigit() and file.stem[3:].isdigit()
    ]

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
