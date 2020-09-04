from django.contrib import admin

# Register your models here.
from .models import Language, Word, WordVideo


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    pass


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    pass


@admin.register(WordVideo)
class WordVideoAdmin(admin.ModelAdmin):
    pass
