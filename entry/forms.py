from django import forms
from django.core.exceptions import ValidationError
from django_ckeditor_5.widgets import CKEditor5Widget

from app.utils import content_is_empty, format_entry_urls


class EntryForm(forms.Form):
    entry_content = forms.CharField(
        label='entry content',
        widget=CKEditor5Widget(attrs={"class": "django_ckeditor_5"}),)

    def __init__(self, *args, **kwargs):
        super(EntryForm, self).__init__(*args, **kwargs)
        self.fields["content"].required = False
        self.fields["content"].label = "content"

    def clean(self):  # avoid empty entries
        content = self.cleaned_data.get('content')
        raw_content = content
        if content:
            if content_is_empty(content):
                raise ValidationError("entry content can not be empty")
            else:
                self.cleaned_data['content'] = format_entry_urls(raw_content)
        return self.cleaned_data
