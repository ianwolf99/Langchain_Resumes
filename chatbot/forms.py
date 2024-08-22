# forms.py
from django import forms
class RegistrationForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100)
    email = forms.EmailField(label='Email')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    role_choices = [
        ('HR', 'HR'),
        ('Recruiter', 'Recruiter'),
    ]
    role = forms.ChoiceField(label='Role', choices=role_choices)
class ChatForm(forms.Form):
    input_text = forms.CharField(widget=forms.Textarea(attrs={'rows': 7}), label='')


class ResumeUploadForm(forms.Form):
    resume = forms.FileField(label="Upload your resume", widget=forms.ClearableFileInput(attrs={'accept': '.pdf'}))

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    password_confirm = forms.CharField(widget=forms.PasswordInput(), label='Confirm Password')

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password != password_confirm:
            raise forms.ValidationError('Passwords do not match')
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username and password:
            self.user = authenticate(username=username, password=password)
            if self.user is None:
                raise forms.ValidationError('Invalid username or password')
        return self.cleaned_data

    def get_user(self):
        return getattr(self, 'user', None)
