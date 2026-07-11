from django.contrib import messages
from django.contrib.auth import login, views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views.generic.edit import FormView

from app.apps.users.forms import AvatarForm, RegisterForm


class LoginView(views.LoginView):
    template_name = "users/login.html"


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(
            self.request,
            self.object,  # type: ignore
            backend="django.contrib.auth.backends.ModelBackend",
        )
        return response

    def get_success_url(self):
        return reverse_lazy("profile")


class ProfileView(LoginRequiredMixin, FormView):
    template_name = "users/profile.html"
    form_class = AvatarForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy("profile")

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Avatar updated.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_user"] = self.request.user
        return context
