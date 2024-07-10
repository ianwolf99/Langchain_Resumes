# forms.py
from django import forms

class ChatForm(forms.Form):
    input_text = forms.CharField(widget=forms.Textarea(attrs={'rows': 7}), label='')
