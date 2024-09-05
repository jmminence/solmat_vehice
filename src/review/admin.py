from django.contrib import admin

from review.models import BlindCarbonCopy, MailList, Recipient, RecipientMail, Grouper, AnalysisGrouper


admin.site.register(RecipientMail)
admin.site.register(Grouper)
admin.site.register(AnalysisGrouper)
admin.site.register(BlindCarbonCopy)


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return self.model.items.get_queryset()


@admin.register(MailList)
class MailListAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return self.model.items.get_queryset()
