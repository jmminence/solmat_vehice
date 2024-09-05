from django.contrib import admin
from lab.models import Cassette, Slide, UnitDifference


@admin.register(Slide)
class CustomSlide(admin.ModelAdmin):
    list_display = (
        "id",
        "parent_case",
        "parent_identification",
        "parent_unit",
        "correlative",
        "stain",
        "build_at",
        "released_at",
    )
    ordering = ["-id"]
    search_fields = (
        "unit__identification__entryform__no_caso",
        "unit__identification__cage",
    )


@admin.register(Cassette)
class CustomCassette(admin.ModelAdmin):
    list_display = (
        "id",
        "parent_case",
        "parent_identification",
        "parent_unit",
        "correlative",
        "build_at",
        "processed_at",
    )
    ordering = ["-id"]
    search_fields = (
        "unit__identification__entryform__no_caso",
        "unit__identification__cage",
    )


@admin.register(UnitDifference)
class CustomUnitDifference(admin.ModelAdmin):
    list_display = (
        "id",
        "difference",
        "organ",
        "unit",
        "created_at",
        "status_changed_at",
    )
    ordering = ["-id"]
    search_fields = ("unit__identification__entryform__no_caso",)
