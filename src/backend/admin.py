from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.forms import Textarea, TextInput

from backend.models import *

admin.site.register(Fixative)
admin.site.register(Organ)
admin.site.register(Responsible)
admin.site.register(EmailCcTo)
admin.site.register(Research)
admin.site.register(Specie)
admin.site.register(Currency)

class CustomerCenterInline(admin.TabularInline):
    model = Customer.center.through
    extra = 1

@admin.register(Customer)
class CustomCustomer(admin.ModelAdmin):
    inlines = [CustomerCenterInline]
    list_display = ("name", "company", "corporate_name", "country", "type_customer", "rut")

@admin.register(Center)
class CustomCenter(admin.ModelAdmin):
    list_display = ("name","company_name","latitude","longitude","country","region","location")

@admin.register(AnalysisForm)
class CustomAnalysisForm(admin.ModelAdmin):
    list_display = ("id", "entryform", "exam", "stain", "patologo", "status")
    ordering = ["-entryform__no_caso"]
    search_fields = ("entryform__no_caso", "exam__name")


@admin.register(EntryForm)
class CustomEntryForm(admin.ModelAdmin):
    list_display = ("id", "no_caso", "customer", "created_at", "sampled_at")
    ordering = ["-no_caso"]
    search_fields = ("no_caso",)


@admin.register(SampleExams)
class CustomSampleExam(admin.ModelAdmin):
    list_display = ("id", "sample", "exam", "organ", "stain", "unit_organ")
    search_fields = ("sample__entryform__no_caso", "exam__name")


@admin.register(Exam)
class CustomExam(admin.ModelAdmin):
    list_display = ("name", "service", "stain")

    def get_form(self, request, obj=None, **kwargs):
        form = super(CustomExam, self).get_form(request, obj, **kwargs)
        field = form.base_fields["stain"]
        field.widget.can_delete_related = False
        return form


@admin.register(EmailTemplate)
class CustomEmail(admin.ModelAdmin):
    list_display = ("name", "body")
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 3, "cols": 50})},
        models.CharField: {"widget": TextInput()},
    }



@admin.register(Stain)
class CustomStain(admin.ModelAdmin):
    list_display = ("name", "abbreviation", "description")



@admin.register(Preinvoice)
class CustomPreinvoice(admin.ModelAdmin):
    list_display = ("number", "customer", "date", "amount")
    search_fields = ("number", "customer__name")



@admin.register(AnalysisPreinvoice)
class CustomAnalysisPreinvoice(admin.ModelAdmin):
    list_display = ("id", "preinvoice", "analysis")
    search_fields = ("preinvoice__folio", "analysis__entryform__no_caso", "analysis__exam__name")


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'action_time'
    list_filter = [
        'user',
        'content_type',
        'action_flag'
    ]

    search_fields = [
        'object_repr',
        'change_message'
    ]

    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_repr',
        'object_id',
        'action_flag'
    ]
