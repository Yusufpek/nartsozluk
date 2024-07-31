from django.contrib import admin

from .models import Title, Entry, Author, Vote, Topic, AuthorsFavorites

# Register your models here.


class TitleAdmin(admin.ModelAdmin):
    list_display = ["text", "created_at"]
    list_filter = ["created_at"]


class EntryAdmin(admin.ModelAdmin):
    list_display = ["text", "title", "author"]
    fieldsets = [
        (
            "Informations", {"fields": [
                "title",
                "author"]},
        ),
        ("Text", {"fields": ["text"]}),
    ]
    list_filter = ["created_at", "updated_at"]


admin.site.register(Title, TitleAdmin)
admin.site.register(Entry, EntryAdmin)
admin.site.register(Author)
admin.site.register(Vote)
admin.site.register(Topic)
admin.site.register(AuthorsFavorites)
