from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Subscription role", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Subscription role", {"fields": ("email", "role")} ),)
    list_display = ("email", "first_name", "last_name", "role", "is_active")
    ordering = ("email",)
