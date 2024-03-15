from io import BytesIO
from pathlib import Path

import pytest

from src.settings import FILENAME, SCHEMA, Settings


@pytest.fixture
def mock_config_file(monkeypatch):
    """Mocks a `config.toml` in binary format to replace the real file access"""

    mock_config_contents = b"""
[flash_drive]
dir = 'G:/'
name = 'HAPPY7'

[backup]
dir = 'W:/Folder/Sub_folder/BackupFolder'

[preview]
dir = 'W:/Folder/Sub_folder/PreviewFolder'
format = 'svg'

[sorting]
key = 'number'
reverse = false

[logging]
debug = true
"""

    written_data = {}

    class MockBytesIO(BytesIO):
        """Simulates opening and closing a file in `"xb"` mode"""

        def __init__(self, mock_file, mode, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.mock_file = mock_file
            # TODO: Figure out why the typechecker complains here
            self.mode = mode  # type:ignore

        def close(self):
            if self.mode == "xb" and self.mock_file in written_data:
                raise FileExistsError(f"File {self.mock_file} already exists.")
            written_data[self.mock_file] = self.getvalue()
            super().close()

    def mock_open(mock_file, mode="rb", *args, **kwargs):
        if mock_file == FILENAME and "b" in mode:
            if "w" in mode or "x" in mode:
                # Return a writable BytesIO object for 'wb' mode
                return MockBytesIO(mock_file, mode)
            else:
                # Return a readable BytesIO object for 'rb' mode
                return BytesIO(mock_config_contents)
        else:
            return open(mock_file, mode, *args, **kwargs)

    # Replace built-in `open` with the mock version
    monkeypatch.setattr("builtins.open", mock_open)

    # Return written_data for other testing purposes
    return written_data


@pytest.mark.usefixtures("mock_config_file")
def test_create_file(tmp_path, mock_config_file):
    Settings.create_file()

    assert Path.exists(Path(FILENAME))
    assert b"?" in mock_config_file[FILENAME]


def test_to_dict():
    # Mock minimal `Settings` object
    settings = Settings()
    settings.flash_drive_dir = Path("Z:\\")
    settings.flash_drive_name = "HAPPY9"
    settings.backup_dir = Path("X:\\Folder2\\Sub_folder2\\BackupFolder2")
    settings.preview_dir = Path("X:\\Folder2\\Sub_folder2\\PreviewFolder2")
    settings.preview_format = "jpg"
    settings.sorting_key = "year"
    settings.sorting_reverse = False
    settings.logging_debug = False

    settings_dict = settings.to_dict()

    # Test if `settings_dict` matches SCHEMA including the order of the keys
    assert isinstance(settings_dict, dict)

    for key in SCHEMA:
        assert key in settings_dict.keys()
        for index, item in enumerate(SCHEMA[key]):
            assert list(settings_dict[key].keys())[index] == SCHEMA[key][index]


@pytest.mark.usefixtures("mock_config_file")
def test_from_file():
    settings = Settings.from_file()

    assert settings.flash_drive_dir == Path("G:\\")
    assert settings.flash_drive_name == "HAPPY7"
    assert settings.backup_dir == Path("W:\\Folder\\Sub_folder\\BackupFolder")
    assert settings.preview_dir == Path("W:\\Folder\\Sub_folder\\PreviewFolder")
    assert settings.preview_format == "svg"
    assert settings.sorting_key == "number"
    assert settings.sorting_reverse is False
    assert settings.logging_debug is True
