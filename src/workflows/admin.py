from django.contrib import admin

from .models import Form


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "flow",
        "content_type",
        "object_id",
        "form_closed",
        "cancelled",
    )
    search_fields = ("object_id",)
