from django import forms
from .models import *
import django.contrib.auth.forms as authforms
from mdeditor.fields import MDTextField

class ModelCustomForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''

    def get_model(self):
        return self.__class__.Meta.model


class LoginForm(authforms.AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['placeholder'] = field.label

class ContentForm(ModelCustomForm):

    tags = forms.MultipleChoiceField()
    content = MDTextField()

    class Meta:
        model = Content
        fields = ('tags', 'title', 'caption', 'content',)
        widgets = {
            'tags': forms.SelectMultiple(attrs = {
                'label': 'タグを選択',
                'placeholder': 'タイトルを入力',
            }),
            'title': forms.TextInput(attrs = {
                'label': 'Title',
                'placeholder': 'タイトルを入力'
            }),
            'caption': forms.Textarea(attrs = {
                'label': 'Caption',
                'placeholder': 'キャプションを入力',
                'class': 'materialize-textarea',
            }),
        }
        js = ('ckeditor.js',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tags = []
        for tag in Tag.objects.all():
            tags.append((tag.id, tag.name))
        
        self.fields['tags'].choices = tags

    


class TagForm(ModelCustomForm):

    class Meta:
        model = Tag
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs = {
                'label': 'Tag',
                'placeholder': 'タグ名を入力'
            }),
        }

