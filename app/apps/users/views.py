from django.contrib.auth import views
from django.urls import reverse_lazy
from django.views.generic import CreateView

from app.apps.users.forms import RegisterForm


class LoginView(views.LoginView):
    template_name = "users/login.html"


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("login")
