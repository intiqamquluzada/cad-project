from django import forms
from django.core.exceptions import ValidationError


class FileGetForm(forms.Form):
    file1 = forms.FileField(label="Məlumatları təmin edən excel faylını daxil edin: ", required=True,
                            widget=forms.ClearableFileInput(attrs={'id': '1'}),
                            )

    def clean_file1(self):
        file1 = self.cleaned_data.get('file1')
        if not file1:
            raise ValidationError("Fayl 1 seçilməlidir.")
        return file1

    def __init__(self, *args, **kwargs):
        super(FileGetForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'hidden'
