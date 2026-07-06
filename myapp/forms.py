from django import forms
from .models import BoardType


class UploadZipForm(forms.Form):
    title = forms.CharField(max_length=180, label='Project title')
    board_type = forms.ModelChoiceField(queryset=BoardType.objects.all(), label='Board type')
    zip_file = forms.FileField(label='ZIP file (code + circuit diagram)')


class DownloadRequestForm(forms.Form):
    phone_number = forms.CharField(max_length=30, required=False, label='Phone number')
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False, label='Message for admin')


class DownloadCodeForm(forms.Form):
    access_code = forms.CharField(max_length=32, label='Download code')
