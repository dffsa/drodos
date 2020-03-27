from django import forms
from sitepr.models import User, Group


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    biography = forms.CharField(label='Biography', max_length=500)

    class Meta:
        model = User
        help_texts = {
            'username': None,
        }
        fields = [
            'username',
            'password',
            'email',
            'biography'
        ]


class GroupForm(forms.ModelForm):
    name = forms.CharField(empty_value=True)

    class Meta:
        model = Group
        fields = [
            'name',
            'description',
        ]