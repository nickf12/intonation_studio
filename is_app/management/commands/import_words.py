import os
from django.core.management.base import BaseCommand
from is_app.models import Word, Language
from django.conf import settings


class OpenSubtitleCommand(BaseCommand):
    help = 'Import words from file'
    """
    Built on top of opensutitles.com corpora
    """
    FILENAME_PATTERN = '%s_50k.txt'

    def add_arguments(self, parser):
        parser.add_argument('langs', nargs='+', type=str)

    def handle(self, *args, **options):
        for lang in options['langs']:
            lang_obj = Language.objects.get_or_create(code=lang)
            lang_folder = os.path.join(settings.OS_WORDS_PATH, lang)
            lang_file = os.path.join(lang_folder, self.FILENAME_PATTERN % lang)
            if not os.path.exists(lang_file):
                continue
            with open(lang_file) as fp:
                line = fp.readline()
                cnt = 1
                while line:
                    word, relevance = line.split(' ')
                    Word.objects.get_or_create(
                        word=word,
                        relevance=relevance,
                        languge=lang
                    )
                    line = fp.readline()
                    cnt += 1
