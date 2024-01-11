"""Handles all pattern specific data, files and objects"""
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

import pyembroidery
from PIL import Image, ImageFilter

# TODO: `Settings` is passed a couple of times here. It could be better to assign it to the class altogether or figure out if it should be loaded from the file directly
from settings import PREVIEW_FORMATS, Settings
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
    embroidery: pyembroidery.EmbPattern
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
            number = int(latest_pattern(folder=settings.backup_dir, year=year).stem[:3])
        # `sort_files` depends on the name being numeric so it will raise an index error
        # if the latest file is not found, because of a wrong name format or new year
        except IndexError:
            number = 1

        embroidery_obj = pyembroidery.read(str(file))

        pattern = cls(
            original_name=original_name,
            number=number,
            year=year,
            size_kb=size_kb,
            hash=hash,
            flash_drive=settings.flash_drive_name,
            # MYPY: Although we're checking for `EmbPattern`, since it can be `Unknown | None`, we'd have to check for those as well
            embroidery=embroidery_obj,  # type: ignore
        )

        if not pattern.valid_numbers():
            raise ValueError(
                "`pattern.number` and/or `pattern.year` are not within \
            expected ranges."
            )

        # Do nothing for the first pattern of a new year
        pattern.name = pattern.name_from_numbers()
        if pattern.number == 1:
            pass
        else:
            pattern.bump_pattern_number()

        return pattern

    def to_image(self, target_folder: Path, format: str) -> Path:
        """Exports an image preview to a target format and saves it in the previews
        directory. Returns a `Path` object for the new image"""

        try:
            assert format in PREVIEW_FORMATS
        except AssertionError as e:
            raise ValueError(
                f"`{e}` is not a valid format. Must be: {', '.join(PREVIEW_FORMATS)}"
            )

        # Perform setup common to both `png` and `jpg`
        if format == "jpg" or format == "png":
            # Export the `png` image to the speficied folder
            image_path = target_folder / f"{self.name}.png"
            pyembroidery.write_png(
                pattern=self.embroidery,
                # The method raises an exception if the path is not a `str`
                stream=str(image_path),
                settings={"fancy": True},
            )

            # Post-produce the `png` image: smooth
            image = Image.open(image_path)
            smoothed_image = image.filter(ImageFilter.SMOOTH)

            if format == "png":
                smoothed_image.save(image_path)

            elif format == "jpg":
                # Prepare `png` for `jpg` conversion
                # Create a white background for the image
                white_background = Image.new("RGBA", smoothed_image.size, "WHITE")
                white_background.paste(smoothed_image, (0, 0), smoothed_image)
                rgb_image = white_background.convert("RGB")
                # Change the path to end in `jpg`
                image_path.unlink()
                image_path = target_folder / f"{self.name}.jpg"
                # Save an uncompressed `jpg`
                rgb_image.save(image_path, quality=100, subsampling=0)

        elif format == "svg":
            image_path = target_folder / f"{self.name}.svg"
            pyembroidery.write_svg(pattern=self.embroidery, stream=str(image_path))

        return image_path  # type: ignore

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


def export_all_patterns(files_list: list[Path], target_folder: Path, format: str):
    """Exports all patterns in the specified folder to the chosen format.

    Return `True` if the operation is successful."""

    for file in files_list:
        data = get_data(file)
        embroidery_obj = pyembroidery.read(str(file))
        pattern_number = int(data.file_name[:3])

        pattern = Pattern(
            original_name=data.file_name,
            year=data.year_modified,
            size_kb=data.size_kb,
            hash=data.hash,
            flash_drive="?",
            embroidery=embroidery_obj,  # type: ignore
            name=data.file_name,
            number=pattern_number,
        )

        pattern.to_image(target_folder=target_folder, format=format)
    return True
