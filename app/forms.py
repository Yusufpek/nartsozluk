from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import Author, Topic, Title, Entry


class SignupForm(UserCreationForm):
    email = forms.EmailField(max_length=200, help_text='Required')

    class Meta:
        model = Author
        fields = ['username', 'email', 'password1', 'password2']

    def clean(self):
        email = self.cleaned_data.get('email')
        if Author.objects.filter(email=email).exists():
            raise ValidationError("this email using for different account")
        return self.cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class TitleForm(forms.Form):
    text = forms.CharField(max_length=50)
    topic = forms.ChoiceField()
    entry_content = forms.CharField(widget=CKEditor5Widget())

    def __init__(self, *args, **kwargs):
        super(TitleForm, self).__init__(*args, **kwargs)
        self.fields['topic'] = forms.ModelChoiceField(
            queryset=Topic.objects.all())

    def clean(self):
        text = self.cleaned_data.get('text')
        if Title.objects.filter(text__contains=text).exists():
            raise ValidationError("this title already added")
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
