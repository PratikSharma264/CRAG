from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


class RegisterForm(UserCreationForm):
    """Username and password (typed twice, so a typo can't lock someone out)."""

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"

        self.fields["username"].help_text = ""
        self.fields["username"].widget.attrs.update({"autocomplete": "username", "autofocus": True})

        self.fields["password1"].label = "Password"
        self.fields["password1"].help_text = ""
        self.fields["password1"].widget.attrs["autocomplete"] = "new-password"

        self.fields["password2"].label = "Confirm password"
        self.fields["password2"].help_text = ""
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"
