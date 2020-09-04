from django.db import models


class Language(models.Model):
    code = models.CharField(
        max_length=10,
        unique=True,
    )
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )


class Word(models.Model):
    word = models.CharField(max_length=1023, unique=True)
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE
    )
    count_char = models.IntegerField(blank=True, null=True)
    count_vowels = models.IntegerField(blank=True, null=True)
    relevance = models.IntegerField(blank=True, null=True)

    def save(self):
        pass


class WordVideo(models.Model):
    word = models.ForeignKey(
        Language,
        on_delete=models.CASCADE
    )
    link_code = models.CharField(max_length=1023, blank=True, null=True)
    title = models.CharField(max_length=1023, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)
