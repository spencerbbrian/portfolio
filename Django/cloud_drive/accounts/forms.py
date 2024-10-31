from django import forms
from .models import UploadedFile, Folder

class UploadFileForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ['file']

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name']    


class MoveFileForm(forms.Form):
    folder = forms.ModelChoiceField(queryset=Folder.objects.none(), empty_label="Select a folder")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['folder'].queryset = Folder.objects.filter(user=user)
