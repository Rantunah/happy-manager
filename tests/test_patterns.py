import random
from pathlib import Path

import pytest

from src.patterns import FORMAT, Pattern, latest_pattern


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
    name, original_name, number, year, size_kb, hash, flash_drive, expected
):
    pattern = Pattern(
        name=name,
        original_name=original_name,
        number=number,
        year=year,
        size_kb=size_kb,
        hash=hash,
        flash_drive=flash_drive,
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
    original_name, number, year, size_kb, hash, flash_drive, expected
):
    pattern = Pattern(
        original_name=original_name,
        number=number,
        year=year,
        size_kb=size_kb,
        hash=hash,
        flash_drive=flash_drive,
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
