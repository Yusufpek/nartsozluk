from django.contrib import admin

from .models import Title, Vote, Topic, AuthorsFavorites

# Register your models here.


class TitleAdmin(admin.ModelAdmin):
    list_display = ["text", "created_at"]
    list_filter = ["created_at"]


admin.site.register(Title, TitleAdmin)
admin.site.register(Vote)
admin.site.register(Topic)
admin.site.register(AuthorsFavorites)
