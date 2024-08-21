from django import forms
from django.core.exceptions import ValidationError
from django_ckeditor_5.widgets import CKEditor5Widget

from entry.models import Entry
from .models import Author, Topic, Title
from .utils import format_entry_urls, content_is_empty


class TitleForm(forms.Form):
    title = forms.CharField(max_length=100, label='title (max 100 character)')
    topic = forms.ChoiceField()
    entry_content = forms.CharField(
        label='first entry content',
        widget=CKEditor5Widget(attrs={"class": "django_ckeditor_5"}),)

    def __init__(self, *args, **kwargs):
        super(TitleForm, self).__init__(*args, **kwargs)
        self.fields['topic'] = forms.ModelChoiceField(
            label='topic',
            queryset=Topic.objects.all())
        self.fields['entry_content'].required = False

    def clean(self):
        text = self.cleaned_data.get('title')
        entry_content = self.cleaned_data.get('entry_content')
        entry_content = entry_content.split('<p>')[1].split('</p>')[0]
        if Title.objects.filter(text=text).exists():
            raise ValidationError("this title already added")
        elif entry_content:
            if content_is_empty(entry_content):
                raise ValidationError("entry content can not be empty")
            else:
                self.cleaned_data['entry_content'] = format_entry_urls(
                    entry_content)
        return self.cleaned_data


class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ("content",)
        widgets = {
            "content": CKEditor5Widget(attrs={"class": "django_ckeditor_5"}),
        }

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


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['random_entry_count', 'title_entry_count', 'profile_image']


class ReportForm(forms.Form):
    text = forms.CharField(
        max_length=500,
        label='report description',
        widget=forms.Textarea)


class AINewTitleForm(forms.Form):
    title_count = forms.IntegerField(min_value=1, max_value=10)
    entry_per_title_count = forms.IntegerField(min_value=1, max_value=10)


class AINewEntryForm(forms.Form):
    title_id = forms.IntegerField(min_value=1)
    entry_count = forms.IntegerField(min_value=1, max_value=20)

    def clean(self):
        id = self.cleaned_data.get('title_id')
        title = Title.objects.filter(pk=id).first()
        if not title:
            raise ValidationError("incorrect entry id")
        return self.cleaned_data


class AINewEntriesLikeAnEntry(forms.Form):
    entry_id = forms.IntegerField(min_value=1)
    title_id = forms.IntegerField(min_value=1)
    entry_count = forms.IntegerField(min_value=1, max_value=20)

    def clean(self):
        id = self.cleaned_data.get('entry_id')
        entry = Entry.objects.filter(pk=id).first()
        if not entry:
            raise ValidationError("incorrect entry id")
        else:
            title_id = self.cleaned_data.get('title_id')
            title = Title.objects.filter(pk=title_id).first()
            if not title:
                raise ValidationError("incorrect title id")
        return self.cleaned_data
