from pathlib import Path
from tkinter import filedialog

import patterns
import utils.files as files
import utils.hashes as hashes
from settings import Settings

# Initialize settings or load them from file
settings = Settings.from_file()


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

    if not hashes.is_present(
        new_file, target_dir=settings.backup_dir, extension=patterns.FORMAT
    ):
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

            # write the transaction to the csv log
            pattern.to_csv_log(settings)


if __name__ == "__main__":
    main()
