from django.apps import AppConfig
from django.db.models.signals import pre_save, post_delete


class BackendConfig(AppConfig):
    name = 'backend'

    def ready(self):
        from . import models
        from . import signals

        # Post Save signal to log whenever given models are created or updated.
        pre_save.connect(signals.on_model_pre_save, sender=models.EntryForm, dispatch_uid="Achiness0678")
        pre_save.connect(signals.on_model_pre_save, sender=models.AnalysisForm, dispatch_uid="Destiny6761")
        pre_save.connect(signals.on_model_pre_save, sender=models.CaseFile, dispatch_uid="Poem7526")
        pre_save.connect(signals.on_model_pre_save, sender=models.Identification, dispatch_uid="Quintuple7093")
        pre_save.connect(signals.on_model_pre_save, sender=models.Unit, dispatch_uid="Blustery0696")
        pre_save.connect(signals.on_model_pre_save, sender=models.Research, dispatch_uid="Fox5521")
        pre_save.connect(signals.on_model_pre_save, sender=models.ExternalReport, dispatch_uid="Directory8376")
        pre_save.connect(signals.on_model_pre_save, sender=models.CaseFile, dispatch_uid="Foxtrot593")

        # Post Delete signal to log whenever given models are deleted.
        post_delete.connect(signals.on_model_post_delete, sender=models.EntryForm, dispatch_uid="Unsmooth2010")
        post_delete.connect(signals.on_model_post_delete, sender=models.AnalysisForm, dispatch_uid="Shifting3062")
        post_delete.connect(signals.on_model_post_delete, sender=models.CaseFile, dispatch_uid="Imprecise2870")
        post_delete.connect(signals.on_model_post_delete, sender=models.Identification, dispatch_uid="Bonus6855")
        post_delete.connect(signals.on_model_post_delete, sender=models.Unit, dispatch_uid="Bulginess2883")
        post_delete.connect(signals.on_model_post_delete, sender=models.Research, dispatch_uid="Absence5986")
        post_delete.connect(signals.on_model_post_delete, sender=models.ExternalReport, dispatch_uid="Everyday2929")
        post_delete.connect(signals.on_model_post_delete, sender=models.CaseFile, dispatch_uid="Eagle2894")

        return super().ready()
