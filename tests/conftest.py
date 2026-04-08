# tests/conftest.py

import os
import pytest


def pytest_configure():
    """Автоматически настраиваем Django при запуске тестов"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    # если у тебя settings в другом месте → поменяй путь
    # например: "FirstSiteEnglish.settings" или "config.settings.local"

    import django

    django.setup()
