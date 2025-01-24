from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'id': 'typeEmailX',
            'class': 'form-control form-control-lg',
            'placeholder': 'E-poçtunuzu daxil edin'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'id': 'typePasswordX',
            'class': 'form-control',
            'placeholder': 'Şifrənizi daxil edin'
        })
    )