from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from app.apps.users.models import User


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Аватар", {"fields": ("avatar",)}),)  # type: ignore


admin.site.register(User, CustomUserAdmin)
