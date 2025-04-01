from django import forms

class PublicLinkForm(forms.Form):
    public_key = forms.CharField(
        label='Публичная ссылка на Яндекс.Диск',
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Введите публичную ссылку'})
    )