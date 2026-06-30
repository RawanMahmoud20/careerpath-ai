from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

User = get_user_model()

# Shared CSS class so fields match the site's existing styling
_INPUT = "form-control"


class RegisterForm(forms.ModelForm):
    """Sign-up form for the custom User model."""

    password = forms.CharField(
        min_length=8,
        label="Password",
        widget=forms.PasswordInput(attrs={"class": _INPUT, "placeholder": "••••••••"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"class": _INPUT, "placeholder": "••••••••"}),
    )

    class Meta:
        model = User
        fields = ["full_name", "email"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": _INPUT, "placeholder": "Sarah Anderson"}),
            "email": forms.EmailInput(attrs={"class": _INPUT, "placeholder": "you@example.com"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class EmailLoginForm(AuthenticationForm):
    """Login form: relabels the 'username' field as Email."""

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": _INPUT, "placeholder": "you@example.com", "autofocus": True}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": _INPUT, "placeholder": "••••••••"}),
    )
