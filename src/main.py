# Import modules required for logging first
import getpass

from utils.logs import setup_file_logger

username = getpass.getuser()
system_logger = setup_file_logger(name="System", path="system.log")

from pathlib import Path
from tkinter import filedialog

import patterns
import utils.files as files
import utils.hashes as hashes
from settings import Settings

# Setup username fetching and loggers

# Initialize settings or load them from file
settings = Settings.from_file()

# Set logging level to `INFO` or `DEBUG` according to `settings`
system_logger.setLevel("DEBUG" if settings.logging_debug is True else "INFO")


def main():
    # TODO: There is no way to check if the drive letter matches the preset drive name.
    # Force the user to pick a flash drive
    settings.flash_drive_dir = Path(filedialog.askdirectory(title="Select Flash Drive"))
    new_file = Path(
        filedialog.askopenfilename(
            title="Select New Pattern File",
            filetypes=[("Data Stitch Tajima file", "*.dst")],
        )
    )

    pattern = patterns.Pattern.from_file(new_file, settings)

    duplicate_hashes: dict | bool = hashes.is_present(
        new_file, target_dir=settings.backup_dir, extension=patterns.FORMAT
    )
    if duplicate_hashes:
        # Get the first value in the first keys, {key: {key: value}}
        duplicate = duplicate_hashes[next(iter(duplicate_hashes))].get(
            next(iter(duplicate_hashes[next(iter(duplicate_hashes))]))
        )[0]
        system_logger.warning(
            f"({username}) `{pattern.original_name}.{patterns.FORMAT}` has already been processed. Matches `{duplicate}`."
        )
    else:
        # Reset the count if there is no pattern in the list with the year
        if pattern.year not in patterns.list_present_years(settings.backup_dir):
            pattern.number = 0
            pattern.bump_pattern_number()
        else:
            # Get the latest pattern in the list from that year
            latest_pattern = patterns.latest_pattern(settings.backup_dir, pattern.year)
            # Assign the correct number to the pattern, based on the new name
            pattern.number = int(latest_pattern.stem[:3])
            pattern.bump_pattern_number()

        # Rename and Copy the file to the backups folder
        renamed_file = files.rename_file(new_file, new_name=pattern.name)

        # If the file is backed up successfuly, copy it to the flash drive
        if files.copy_files([renamed_file], target_dir=settings.backup_dir):
            # Delete all the files in the flash drive to ensure proper sorting
            files.wipe_directory(settings.flash_drive_dir)
            # Sort the files in the backup folder and copy them to the flash drive
            files.copy_files(
                files=patterns.sort_files(
                    files.list_files_extension(
                        settings.backup_dir, extension=patterns.FORMAT
                    ),
                    key=settings.sorting_key,
                    reverse=settings.sorting_reverse,
                ),
                target_dir=settings.flash_drive_dir,
            )
            # export an image of the new pattern to the previews folder
            pattern.to_image(settings.preview_dir, format=settings.preview_format)

            # write the transaction to the csv log
            if not pattern.to_csv_log(settings):
                system_logger.error(
                    f"({username}) CSV record for `{pattern.name}.{patterns.FORMAT}` could not be "
                    "updated because the file was not accessible."
                )
            system_logger.info(
                f"({username}) Pattern `{pattern.original_name}.{patterns.FORMAT}` was processed successfully. Listed as `{pattern.name}.{patterns.FORMAT}`"
            )


if __name__ == "__main__":
    main()
