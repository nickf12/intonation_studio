import os
import django
from is_app.models import Language, Word

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "is_project.settings")
django.setup()


class WordImporter:
    def run(lang):
        """
        lang is a tuple (language code, language name)
        """
        language = Language.objects.get_or_create(
            code=lang[0],
            name=lang[1]
        )