from pathlib import Path

from src.main import settings


class TestSettings:
    def test_all_settings_set(self):
        """Tests wether all settings fields are set and aren't placeholder data"""
        settings_attributes = vars(settings)

        for attribute in settings_attributes:
            value = settings_attributes[attribute]
            if isinstance(value, bool):
                continue
            assert value != "?"
            assert value != "_"
            assert value != ""
            assert value != 0

    def test_settings_types(self):
        """Tests wether all attributes types match the correct type"""

        assert isinstance(settings.flash_drive_dir, Path)
        assert isinstance(settings.flash_drive_name, str)
        assert isinstance(settings.backup_dir, Path)
        assert isinstance(settings.preview_dir, Path)
        assert isinstance(settings.preview_format, str)
        assert isinstance(settings.sorting_key, str)
        assert isinstance(settings.sorting_reverse, bool)
        assert isinstance(settings.logging_debug, bool)
