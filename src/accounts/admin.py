from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, Permission, User

from accounts.models import UserProfile, Area, UserArea
from django.contrib.admin import widgets
from django.urls import resolve

admin.site.unregister(User)


class ProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Perfil de Usuario"
    fk_name = "user"
    exclude = ("role", "state", "confirmation_code")


class CustomUserProfile(UserAdmin):
    inlines = (ProfileInline,)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                    "username",
                    "user_permissions",
                    "first_name",
                    "last_name",
                    "is_active",
                )
            },
        ),
    )
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "userprofile",
    )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserProfile, self).get_inline_instances(request, obj)

    def save_model(self, request, obj, form, change):
        super(CustomUserProfile, self).save_model(request, obj, form, change)


admin.site.register(User, CustomUserProfile)
admin.site.register(Permission)
admin.site.register(Area)
admin.site.register(UserArea)
