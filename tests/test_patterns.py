import random
from pathlib import Path

import pyembroidery
import pytest
from utils.files import FileData, list_files_extension

from src.patterns import FORMAT, Pattern, latest_pattern
from src.settings import Settings


# TODO: Test will fail if `FORMAT` is ever removed from `patterns.py`
def create_test_files(tmp_path, filenames: list):
    """Populate a directory with empty files from a list of file names"""

    for filename in filenames:
        file_path: Path = tmp_path / f"{filename}.{FORMAT}"
        file_path.touch()


@pytest.fixture
def mock_file_tree(tmp_path):
    """Create a temporary directory with empty files from a list of file names"""

    filenames = [
        "0012020",
        "0022020",
        "0032021",
        "0042021",
        "0052022",
        "0062022",
        "0072023",
        "0082023",
        "0092024",
        "0102024",
        "TestName1",  # invalid filename
        "TESTName2",  # invalid filename
        "NameTest3",  # invalid filename
        "NAMETEST4",  # invalid filename
        "NaMeTeSt5",  # invalid filename
    ]
    # Shuffle the file list to ensure out of order file creation.
    random.shuffle(filenames)
    create_test_files(tmp_path, filenames)
    return tmp_path


# Depends on the value set for `Settings.REASONABLE_YEAR`, testing for `1997`
@pytest.mark.parametrize(
    "name, original_name, number, year, size_kb, hash, flash_drive, expected",
    [
        ("0012020", "TestPattern1", 1, 2020, 150, "hash1", "HAPPY9", True),
        ("0002020", "TestPattern2", 0, 2020, 150, "hash2", "HAPPY9", ValueError),
        ("0242020", "TestPattern3", 24, 2020, 150, "hash3", "HAPPY9", True),
        ("0252025", "TestPattern4", 25, 2025, 150, "hash4", "HAPPY9", ValueError),
        ("9992024", "TestPattern5", 999, 2024, 150, "hash5", "HAPPY9", True),
        ("0002024", "TestPattern6", 1000, 2024, 150, "hash6", "HAPPY9", ValueError),
        ("0021997", "TestPattern7", 2, 1997, 150, "hash7", "HAPPY9", True),
        ("0021996", "TestPattern8", 2, 1996, 150, "hash8", "HAPPY9", ValueError),
    ],
)
def test_valid_numbers(
    name,
    original_name,
    number,
    year,
    size_kb,
    hash,
    flash_drive,
    expected,
):
    pattern = Pattern(
        name=name,
        original_name=original_name,
        number=number,
        year=year,
        size_kb=size_kb,
        hash=hash,
        flash_drive=flash_drive,
        embroidery=pyembroidery.EmbPattern(),  # Empty instance
    )

    # Check if `expected` is a `class` of sublcass `Exception` and not an instance.
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            pattern.valid_numbers()
    # If no exception is raised, assert `expected` as normal
    else:
        assert pattern.valid_numbers() == expected


@pytest.mark.parametrize(
    "original_name, number, year, size_kb, hash, flash_drive, expected",
    [
        ("TestPattern1", 1, 2020, 150, "hash1", "HAPPY9", "0012020"),
        ("TestPattern2", 0, 2020, 150, "hash2", "HAPPY9", "0002020"),  # invalid
        ("TestPattern3", 24, 2020, 150, "hash3", "HAPPY9", "0242020"),
        ("TestPattern4", 25, 2025, 150, "hash4", "HAPPY9", "0252025"),  # invalid
        ("TestPattern5", 999, 2024, 150, "hash5", "HAPPY9", "9992024"),
        ("TestPattern6", 1000, 2024, 150, "hash6", "HAPPY9", "10002024"),  # invalid
        ("TestPattern7", 2, 1997, 150, "hash7", "HAPPY9", "0021997"),
        ("TestPattern8", 2, 1996, 150, "hash8", "HAPPY9", "0021996"),  # invalid
    ],
)
def test_name_from_numbers(
    original_name,
    number,
    year,
    size_kb,
    hash,
    flash_drive,
    expected,
):
    pattern = Pattern(
        original_name=original_name,
        number=number,
        year=year,
        size_kb=size_kb,
        hash=hash,
        flash_drive=flash_drive,
        embroidery=pyembroidery.EmbPattern(),  # Empty instance
    )
    pattern.name = pattern.name_from_numbers()
    assert pattern.name == expected


@pytest.mark.parametrize(
    "original_name, number, year, size_kb, hash, flash_drive, expected",
    [
        ("TestPattern1", 1, 2020, 150, "hash1", "HAPPY9", 2),
        ("TestPattern2", 0, 2020, 150, "hash2", "HAPPY9", 1),
        ("TestPattern3", 24, 2023, 150, "hash3", "HAPPY9", 25),
        ("TestPattern7", 256, 1997, 150, "hash7", "HAPPY9", 257),
    ],
)
def test_bump_pattern_number(
    original_name, number, year, size_kb, hash, flash_drive, expected
):
    pattern = Pattern(
        original_name=original_name,
        number=number,
        year=year,
        size_kb=size_kb,
        hash=hash,
        flash_drive=flash_drive,
        embroidery=pyembroidery.EmbPattern(),  # Empty instance
    )

    pattern.name_from_numbers()
    pattern.bump_pattern_number()

    assert pattern.number == expected


def test_latest_pattern(mock_file_tree):
    pattern = latest_pattern(mock_file_tree)
    assert pattern.name == "0102024.dst"


def list_present_years(mock_file_tree):
    years = list_present_years(mock_file_tree)
    assert years == {2020, 2021, 2022, 2023, 2024}


@pytest.mark.parametrize(
    "file_data, valid_numbers",
    [
        (
            FileData(
                file_name="TestName1", size_kb=123, hash="abc123", year_modified=1997
            ),
            True,
        ),
        (
            FileData(
                file_name="TestName2", size_kb=456, hash="def456", year_modified=2024
            ),
            True,
        ),
        (
            FileData(
                file_name="NameTest3", size_kb=789, hash="ghi789", year_modified=1990
            ),
            False,
        ),
        (
            FileData(
                file_name="NAMETEST4", size_kb=120, hash="jkl120", year_modified=2050
            ),
            False,
        ),
        (
            FileData(
                file_name="NaMeTeSt5", size_kb=231, hash="mno120", year_modified=2022
            ),
            True,
        ),
    ],
)
def test_from_file(monkeypatch, file_data, mock_file_tree, valid_numbers):
    # Patch `file.utils.get_data` in `src.patterns`'s namespace
    monkeypatch.setattr("src.patterns.get_data", lambda mock_get_data: file_data)

    settings = Settings.from_file()

    # Catch an expected `ValueError` from intentional failing parameters
    try:
        pattern = Pattern.from_file(
            file=(mock_file_tree / f"{file_data.file_name}.dst"), settings=settings
        )
        # If somehow a failing parameter test does not raise the exception, fail the test
        if not valid_numbers:
            pytest.fail("ValueError expected but not raised.")

        # Check if object is well built
        assert pattern.original_name == file_data.file_name
        assert pattern.year == file_data.year_modified
        assert pattern.size_kb == file_data.size_kb
        assert pattern.hash == file_data.hash
        assert pattern.flash_drive == settings.flash_drive_name
        assert isinstance(pattern.embroidery, pyembroidery.EmbPattern)

        # Check if the numbers are within expected parameters
        assert pattern.valid_numbers() == valid_numbers

        # Check whether the new pattern collides with any pattern on the backup already
        file_list = [
            file.stem for file in list_files_extension(settings.backup_dir, FORMAT)
        ]
        assert pattern.name not in file_list

    except ValueError:
        # If somehow a passing parameter test raises the exception, fail the test
        if valid_numbers:
            pytest.fail("ValueError not expected but raised.")


# These parameters depend on real files, required for testing the export
@pytest.mark.parametrize(
    "file_name, format, successful",
    [
        ("0152020", "jpg", True),
        # TODO: `svg` and `png` export is supported but the application is hardcoded for `jpg`
        ("0032021", "png", True),
        ("0052022", "svg", True),
        ("0072023", "webp", False),
    ],
)
def test_to_image(monkeypatch, mock_file_tree, file_name, format, successful):
    settings = Settings.from_file()
    # Setup a temporary dir for the images
    mock_preview_dir = mock_file_tree / "tmp_images"
    mock_preview_dir.mkdir()

    pattern = Pattern.from_file(
        file=(settings.backup_dir / f"{file_name}.dst"), settings=settings
    )

    # Patch `pattern` and `settings` with the correct parameter and folder for the test
    # TODO: Safer than direct assignment, in case getters and setters are implemented
    monkeypatch.setattr(pattern, "name", file_name)
    monkeypatch.setattr(settings, "preview_dir", mock_preview_dir)

    # Catch an intentional `ValueError` from intentional failing parameters
    try:
        settings.preview_format = format
        if not successful:
            # If somehow a failing parameter test does not raise the exception,
            # fail the test
            pytest.fail("ValueError expected but not raised.")

        image = pattern.to_image(
            target_folder=settings.preview_dir, format=settings.preview_format
        )
        assert image is not None
        assert isinstance(image, Path)
        assert image.exists()
        # Don't account for the `.` in the suffix for the assertion
        assert image.suffix[1:] == format
    except ValueError:
        # If somehow a passing parameter test raises the exception, fail the test
        if successful:
            pytest.fail("ValueError not expected but raised.")
