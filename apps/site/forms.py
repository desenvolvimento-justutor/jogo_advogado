from django.forms import CheckboxInput

from allauth.account.forms import LoginForm as AllauthLoginForm
from allauth.account.forms import SignupForm as AllauthSignupForm


class BootstrapFieldsMixin:
    """Aplica classes Bootstrap aos widgets do formulário."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            widget = field.widget

            if isinstance(widget, CheckboxInput):
                css_class = "form-check-input"
            else:
                css_class = "form-control"

            classes = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{classes} {css_class}".strip()


class LoginForm(BootstrapFieldsMixin, AllauthLoginForm):
    pass


class SignupForm(BootstrapFieldsMixin, AllauthSignupForm):
    pass