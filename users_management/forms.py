from django.contrib.auth.forms import UserChangeForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from django import forms
from users.models import CustomUser
from django.core.exceptions import ValidationError


class UserCreateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['photo', 'username', 'first_name', 'last_name', 'email', 'telephone', 'type_profile']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'type_profile': forms.Select(attrs={'class': 'form-control js-simple-select'}),
        }

    def __init__(self, *args, **kwargs):
        super(UserCreateForm, self).__init__(*args, **kwargs)

        # self.fields['password1'].widget.attrs['class'] = 'form-control'
        # self.fields['password1'].label = 'Mot de passe'
        # self.fields['password2'].widget.attrs['class'] = 'form-control'
        # self.fields['password2'].label = 'Confirmer mot de passe'
        self.fields['username'].label = 'Nom d\'utilisateur'
        self.fields['first_name'].label = 'Prenom'
        self.fields['last_name'].label = 'Nom'
        self.fields['email'].label = 'Email'


class UserEditForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ['photo', 'username', 'first_name', 'last_name', 'email', 'telephone', 'type_profile']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'type_profile': forms.Select(attrs={'class': 'form-control js-simple-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(UserEditForm, self).__init__(*args, **kwargs)

        self.fields['first_name'].label = 'Prenom'
        self.fields['last_name'].label = 'Nom'
        self.fields['email'].label = 'Email'
        url_set_password = f'../{self.user.pk}/set_password'
        self.fields['password'].help_text = ("Vous ne pouvez pas voir le mot de passe de cet utilisateur car il est"
                                             "crypté, mais vous pouvez le changer en utilisant "
                                             '<a href="{}">Ce formulaire</a>.').format(url_set_password)


class UserPasswordForm(SetPasswordForm):

    def __init__(self, *args, **kwargs):
        del kwargs['instance']
        self.user = kwargs.pop('user', None)
        super(UserPasswordForm, self).__init__(self.user, *args, **kwargs)

        self.fields['new_password1'].widget.attrs['class'] = 'form-control'
        self.fields['new_password1'].label = 'Mot de passe'

        self.fields['new_password2'].widget.attrs['class'] = 'form-control'
        self.fields['new_password2'].label = 'Confirmer mot de passe'


class PasswordForm(forms.ModelForm):
    new_password_1 = forms.CharField(
        label='Nouveau mot de passe', widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password_2 = forms.CharField(
        label='Confirmer mot de passe', widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = ['new_password_1']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(PasswordForm, self).__init__(*args, **kwargs)

    def clean(self):
        password_1 = self.cleaned_data['new_password_1']
        password_2 = self.cleaned_data['new_password_2']
        if password_1 != password_2:
            raise ValidationError('Passwords do not match.')
        else:
            if self.user:
                validate_password(password_2, self.user)

        return self.cleaned_data
