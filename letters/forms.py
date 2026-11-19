"""Forms for authentication, the letter creator and protected letters."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import LetterPhoto, LetterTheme, BackgroundMusic, LoveLetter, User
from .validators import validate_image_size


TEXT_INPUT = "input input--soft"
SELECT_INPUT = "input input--soft select"
TEXTAREA = "input input--soft textarea"


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": TEXT_INPUT, "placeholder": "you@example.com", "autocomplete": "email"}),
    )
    display_name = forms.CharField(
        required=False,
        max_length=60,
        widget=forms.TextInput(attrs={"class": TEXT_INPUT, "placeholder": "How should we call you?"}),
    )

    class Meta:
        model = User
        fields = ("username", "display_name", "email", "password1", "password2")
        widgets = {
            "username": forms.TextInput(
                attrs={"class": TEXT_INPUT, "placeholder": "your-username", "autocomplete": "username"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {"class": TEXT_INPUT, "placeholder": "At least 8 characters", "autocomplete": "new-password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": TEXT_INPUT, "placeholder": "Repeat your password", "autocomplete": "new-password"}
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": TEXT_INPUT, "placeholder": "Username", "autocomplete": "username"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": TEXT_INPUT, "placeholder": "Password", "autocomplete": "current-password"}
        )


class LoveLetterForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        max_length=128,
        widget=forms.PasswordInput(
            attrs={"class": TEXT_INPUT, "placeholder": "Optional secret password", "autocomplete": "new-password"}
        ),
        help_text="Leave blank for an open letter. Adding a password hides the words until it is entered.",
    )
    password_confirm = forms.CharField(
        required=False,
        max_length=128,
        widget=forms.PasswordInput(
            attrs={"class": TEXT_INPUT, "placeholder": "Repeat the password", "autocomplete": "new-password"}
        ),
    )
    clear_password = forms.BooleanField(required=False, label="Remove the existing password")
    remove_music = forms.BooleanField(required=False, label="Remove uploaded music")

    class Meta:
        model = LoveLetter
        fields = [
            "title", "recipient_name", "sender_name", "message", "closing_note",
            "occasion", "special_date", "theme", "font_style", "backdrop",
            "animation", "music", "music_file", "music_url", "is_public",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": TEXT_INPUT, "placeholder": "A letter for you"}),
            "recipient_name": forms.TextInput(attrs={"class": TEXT_INPUT, "placeholder": "Their name"}),
            "sender_name": forms.TextInput(attrs={"class": TEXT_INPUT, "placeholder": "Your name"}),
            "message": forms.Textarea(
                attrs={"class": TEXTAREA, "rows": 12, "placeholder": "My dearest…\n\nWrite the words you have been carrying in your heart."}
            ),
            "closing_note": forms.TextInput(attrs={"class": TEXT_INPUT, "placeholder": "You will always be special to me."}),
            "occasion": forms.Select(attrs={"class": SELECT_INPUT}),
            "special_date": forms.DateInput(attrs={"class": TEXT_INPUT, "type": "date"}),
            "theme": forms.Select(attrs={"class": SELECT_INPUT}),
            "font_style": forms.Select(attrs={"class": SELECT_INPUT}),
            "backdrop": forms.Select(attrs={"class": SELECT_INPUT}),
            "animation": forms.Select(attrs={"class": SELECT_INPUT}),
            "music": forms.Select(attrs={"class": SELECT_INPUT}),
            "music_file": forms.ClearableFileInput(attrs={"class": "file-input", "accept": "audio/*"}),
            "music_url": forms.URLInput(attrs={"class": TEXT_INPUT, "placeholder": "https://example.com/song.mp3"}),
            "is_public": forms.CheckboxInput(attrs={"class": "checkbox"}),
        }
        labels = {
            "is_public": "Show in the public gallery of love",
            "font_style": "Letter typography",
            "backdrop": "Background atmosphere",
            "animation": "Falling particles",
            "music": "Music from the library",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["theme"].queryset = LetterTheme.objects.filter(is_active=True)
        self.fields["music"].queryset = BackgroundMusic.objects.filter(is_active=True)
        self.fields["theme"].empty_label = "Choose a theme"
        self.fields["music"].empty_label = "No music (quiet letter)"
        self.fields["occasion"].choices = LoveLetter.Occasion.choices
        self.fields["closing_note"].required = False
        if not self.instance.pk:
            first = LetterTheme.objects.filter(is_active=True).first()
            if first:
                self.fields["theme"].initial = first
            self.fields["message"].initial = (
                "My dearest,\n\n"
                "There are a thousand little reasons why you matter to me, and I wanted to put a few of them somewhere you could keep.\n\n"
                "Thank you for every laugh, every quiet moment, and every ordinary day you make feel extraordinary.\n\n"
                "I love you — today, tomorrow, and in every version of forever."
            )

    def clean_message(self):
        message = self.cleaned_data.get("message", "").strip()
        if len(message) < 10:
            raise ValidationError("A few more words, please — your letter needs at least 10 characters.")
        if len(message) > 8000:
            raise ValidationError("Please keep your letter under 8,000 characters.")
        return message

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm = cleaned.get("password_confirm")
        if password or confirm:
            if password != confirm:
                self.add_error("password_confirm", "The two passwords do not match.")
            elif len(password) < 4:
                self.add_error("password", "Use at least 4 characters for the letter password.")
        return cleaned

    def save(self, commit=True):
        letter = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            letter.set_access_password(password)
        elif self.cleaned_data.get("clear_password"):
            letter.access_password = ""
        if self.cleaned_data.get("remove_music") and letter.music_file:
            letter.music_file.delete(save=False)
            letter.music_file = ""
        if commit:
            letter.save()
            self.save_m2m()
        return letter


class LetterPhotoForm(forms.ModelForm):
    class Meta:
        model = LetterPhoto
        fields = ["image", "caption", "order"]
        widgets = {
            "caption": forms.TextInput(
                attrs={"class": TEXT_INPUT, "placeholder": "A little caption…", "maxlength": 140}
            ),
        }

    def clean_image(self):
        image = self.cleaned_data["image"]
        validate_image_size(image)
        return image


class LetterPasswordForm(forms.Form):
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(
            attrs={
                "class": TEXT_INPUT,
                "placeholder": "The secret password",
                "autocomplete": "off",
                "autofocus": True,
            }
        ),
        label="Secret password",
    )


class LetterSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        max_length=80,
        widget=forms.TextInput(
            attrs={"class": TEXT_INPUT, "placeholder": "Search by name or title…", "aria-label": "Search letters"}
        ),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All letters"), ("published", "Published"), ("draft", "Drafts")],
        widget=forms.Select(attrs={"class": SELECT_INPUT, "aria-label": "Filter by status"}),
    )
