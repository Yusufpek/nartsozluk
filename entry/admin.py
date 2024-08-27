from django.contrib import admin

from .models import Entry


class EntryAdmin(admin.ModelAdmin):
    list_display = ["content", "title", "author_id"]
    fieldsets = [
        (
            "Informations", {"fields": [
                "title",
                "author"]},
        ),
        ("Text", {"fields": ["content"]}),
    ]
    list_filter = ["created_at", "updated_at"]


admin.site.register(Entry, EntryAdmin)
