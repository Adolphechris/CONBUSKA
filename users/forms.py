from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django import forms
from .models import CustomUser


class CustomAuthForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                 'placeholder': 'Mot de passe'}))


class CustomUserCreationForm(UserCreationForm):
    pic = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control'}))
    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'photo']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class CustomUserChangeForm(forms.ModelForm):
    # photo = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control'}))
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'photo', 'telephone', 'type_profile']


class UserEditProfileForm(UserChangeForm):
    password = None

    class Meta:
        model = CustomUser
        fields = ['photo', 'username', 'first_name', 'last_name', 'email', 'telephone']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(UserEditProfileForm, self).__init__(*args, **kwargs)

        self.fields['username'].label = 'Nom d\'utilisateur'
        self.fields['first_name'].label = 'Prenom'
        self.fields['last_name'].label = 'Nom'
        self.fields['email'].label = 'Email'
