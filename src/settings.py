"""Handles the creation, validation and update of the application's settings."""

import re
from pathlib import Path
from tkinter import filedialog
from typing import Literal

import tomli_w
import tomllib
import wmi

# Name of the settings file
FILENAME = "config.toml"

# Settings structure.
SCHEMA = {
    "flash_drive": ["dir", "name"],
    "backup": ["dir"],
    "preview": ["dir", "format"],
    "sorting": ["key", "reverse"],
}

# TODO: Implement image export logic
# Image formats for quilting program export
PREVIEW_FORMATS = ["jpg", "png", "svg"]

# Sorting keys for the flash drive sorting algorithm
SORTING_KEYS = ["number", "year"]


class Settings:
    def __init__(self) -> None:
        # Must match `SCHEMA`. Order is also important
        self._flash_drive_dir: Path
        self._flash_drive_name: str
        self._backup_dir: Path
        self._preview_dir: Path
        self._preview_format: str
        # TODO: `sorting_key` should be it's own type to reduce duplicate code
        self._sorting_key: Literal["number", "year"]
        self._sorting_reverse: bool

    @property
    def flash_drive_dir(self) -> Path:
        return self._flash_drive_dir

    @flash_drive_dir.setter
    def flash_drive_dir(self, dir: Path):
        if not isinstance(dir, Path):
            raise ValueError("`flash_dir` must be a Path object")
        self._flash_drive_dir = dir

    @property
    def flash_drive_name(self) -> str:
        return self._flash_drive_name

    @flash_drive_name.setter
    def flash_drive_name(self, name: str):
        regex = r"^HAPPY\d+$"
        if not re.match(regex, name):
            raise ValueError("`flash_name` must be follow the pattern `HAPPY1`.")
        self._flash_drive_name = name

    @property
    def backup_dir(self) -> Path:
        return self._backup_dir

    @backup_dir.setter
    def backup_dir(self, dir: Path):
        if not isinstance(dir, Path):
            raise ValueError("`backup_dir` must be a Path object")
        self._backup_dir = dir

    @property
    def preview_format(self) -> str:
        return self._preview_format

    @preview_format.setter
    def preview_format(self, format: str):
        if format not in PREVIEW_FORMATS:
            raise ValueError(
                f"`preview_format` must be one of these: {', '.join(PREVIEW_FORMATS)}"
            )
        self._preview_format = format

    @property
    def preview_dir(self) -> Path:
        return self._preview_dir

    @preview_dir.setter
    def preview_dir(self, dir: Path):
        if not isinstance(dir, Path):
            raise ValueError("`preview_dir` must be a Path object")
        self._preview_dir = dir

    @property
    def sorting_key(self) -> Literal["number", "year"]:
        return self._sorting_key

    @sorting_key.setter
    def sorting_key(self, key: Literal["number", "year"]):
        if key not in SORTING_KEYS:
            raise ValueError(
                f"`sorting` must be one of these: {', '.join(SORTING_KEYS)}"
            )
        self._sorting_key = key

    @property
    def sorting_reverse(self) -> bool:
        return self._sorting_reverse

    @sorting_reverse.setter
    def sorting_reverse(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError("`sorting_reverse` must be either `True` of `False`")
        self._sorting_reverse = value

    @staticmethod
    def create_file():
        """Creates an empty settings file if there is none at the current directory."""

        try:
            # Create a `dict` based on `SCHEMA` with dummy values
            # `toml` doesn't support `None` so `"_"` is used instead
            # TODO Comprehensions are faster, but maybe readability here is more important
            placeholder_settings = {
                key: {value: "_" for value in values} for key, values in SCHEMA.items()
            }
            with open(FILENAME, "xb") as settings_file:
                tomli_w.dump(placeholder_settings, settings_file)
        except FileExistsError:
            pass

    @staticmethod
    def load_file():
        """Returns a dictionary with the settings loaded from the `TOML` file"""
        with open(FILENAME, "rb") as settings_file:
            settings = tomllib.load(settings_file)
            return settings

    # TODO: This method validates an empty settings file. There should be validation for a file that's already been set.
    @staticmethod
    def validate_file():
        """Validates the schema for the loaded `TOML` settings and truncates
        the file if the schema is not valid.
        """

        try:
            settings = Settings.load_file()
            # TODO Comprehensions are faster, but readability here might be more important
            settings_schema = {
                key: list(value.keys()) for key, value in settings.items()
            }
            match settings_schema == SCHEMA:
                case True:
                    pass
                case False:
                    raise KeyError("Settings file is invalid.")
        # Check that the file exists and delete it if the schema is not valid
        except (KeyError, FileNotFoundError):
            if Path(FILENAME).is_file():
                Path(FILENAME).unlink()
            # Create a new file and validate the schema
            Settings.create_file()
            Settings.validate_file()

    @classmethod
    def from_file(cls):
        """Facotry method to create a `Settings` instance from the `TOML` file.

        Launches a wizard to help the user choose the right settings if the settings
        cannot be set with the values loaded from the file
        """

        cls.validate_file()
        settings_dict = cls.load_file()
        settings = cls()

        try:
            # Try to populate the class attributes with the loaded settings
            # It should fail the first time a file is loaded, because of ´"_"´ set when
            # the file is first created
            # TODO: The second `get` is not type checked correctly
            settings.flash_drive_dir = Path(
                settings_dict.get("flash_drive", {}).get("dir")
            )
            settings.flash_drive_name = settings_dict.get("flash_drive", {}).get("name")
            settings.backup_dir = Path(settings_dict.get("backup", {}).get("dir"))
            settings.preview_dir = Path(settings_dict.get("preview", {}).get("dir"))
            settings.preview_format = settings_dict.get("preview", {}).get("format")
            settings.sorting_key = settings_dict.get("sorting", {}).get("key")
            settings.sorting_reverse = settings_dict.get("sorting", {}).get("reverse")
        except ValueError:
            # TODO: The configuration wizard will remain a part of this module for the POC, but it should be moved to a GUI module.
            # Launch a small wizard to help the user choose the correct values

            # Pick the flash drive folder where the files are stored
            settings.flash_drive_dir = Path(
                filedialog.askdirectory(title="Flash Drive folder")
            )
            # Get the drive name from the given folder and set it

            # Format the drive letter for `wmi` consumption
            drive_letter = str(settings.flash_drive_dir)[0].upper() + ":"

            # Get the name from the drive letter
            for drive in wmi.WMI().Win32_LogicalDisk():
                if drive.DeviceID == drive_letter:
                    settings.flash_drive_name = drive.VolumeName
                    break

            # Pick the backup directory and create a new directory with the chosen
            # flash drive's name
            settings.backup_dir = (
                Path(filedialog.askdirectory(title="Backup folder"))
                / f"{settings.flash_drive_name}"
            )
            if settings.backup_dir and settings.backup_dir.exists():
                settings.backup_dir.mkdir(parents=True, exist_ok=True)

            # Pick preview image directory
            settings.preview_dir = Path(
                filedialog.askdirectory(title="Preview Images folder")
            )

            # Pick image preview format
            # TODO: Make the image format selectable (hardcoded for POC)
            settings.preview_format = "jpg"

            # Pick the key for the sorting algorithm
            # TODO: Make sorting key selectable (hardcoded for POC)
            settings.sorting_key = "year"

            # TODO: Make sorting direction selectable (hardcoded for POC)
            settings.sorting_reverse = True

            settings.update_file()

        return settings

    def to_dict(self) -> dict:
        """Packs all `Settings` attributes into a `dict` that matches the schema."""

        # Loop through `SCHEMA` and build a `dict` with the correct structure
        settings_dict = {}
        for section, keys in SCHEMA.items():
            # Loop through each key in `SCHEMA`'s section
            settings_dict[section] = {}
            for key in keys:
                # Get the attribute's value from the name
                attr_name = f"_{section}_{key}"
                attr_value = getattr(self, attr_name)
                # `Path` is not `TOML` serializable, it should be converted to `str`
                if isinstance(attr_value, Path):
                    attr_value = str(attr_value)
                settings_dict[section][key] = attr_value
        return settings_dict

    def update_file(self) -> None:
        """Truncates the settings `TOML` with the values from the current `Settings`
        instance."""

        settings = self.to_dict()
        with open(FILENAME, "wb") as settings_file:
            tomli_w.dump(settings, settings_file)
