from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q

from backend.models import AnalysisForm, Customer, EntryForm, Exam
from accounts.models import UserArea
from datetime import datetime


class AnalysisManager(models.Manager):
    """
    Custom Manager for Case, where it mainly filters all :model:`backend.Entryform`
    according to it's current :model:`workflows.Form` state. Alongside some helper
    functions.
    """

    def get_queryset(self, user=None):
        queryset = (
            super()
            .get_queryset()
            .filter(
                forms__form_closed=0,
                forms__cancelled=0,
                manual_closing_date__isnull=True,
                exam__pathologists_assignment=True,
                pre_report_started=True,
                pre_report_ended=True,
            )
            .order_by("entryform__created_at")
            .exclude(process_status="Anulado")
        )

        if user is not None and user.userprofile.profile_id not in (1, 2):
            pathologists = User.objects.filter(
                Q(userprofile__profile_id__in=(4, 5))
                | Q(userprofile__is_pathologist=True)
            )

            assigned_areas = UserArea.objects.filter(user=user, role=0)
            pks = [user.id]

            for user_area in assigned_areas:
                users = (
                    UserArea.objects.filter(area=user_area.area)
                    .exclude(user=user)
                    .values_list("user", flat=True)
                )
                pks.extend(users)

            pathologists = pathologists.filter(pk__in=pks)

            return queryset.filter(patologo_id__in=pathologists)

        return queryset

    def waiting(self, user):
        """
        Returns all :model:`backend.AnalysisForm` which a Pathologist
        has finished studying but hasn't being reviewed yet.
        """
        return (
            self.get_queryset(user)
            .filter(
                Q(stages__isnull=True) | Q(stages__state=0),
            )
            .select_related("entryform", "exam", "stain")
        )

    def stage(self, state_index, user):
        """
        Returns all :model:`backend.AnalysisForm` according to it's
        :model:`review.Stage`.STATE index.
        """

        return (
            self.get_queryset(user)
            .filter(stages__state=state_index)
            .select_related("entryform", "exam", "stain")
        )


class GrouperManager(models.Manager):
    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
        )

        return queryset

    def waiting(self):
        """
        Returns all :model:`review.Grouper` which a Pathologist
        has finished studying but hasn't being reviewed yet.
        """
        return (
            self.get_queryset()
            .filter(
                Q(stages__isnull=True) | Q(stages__state=0),
            )
            .select_related("entryform")
        )

    def stage(self, state_index):
        """
        Returns all :model:`review.Grouper` according to it's
        :model:`review.Stage`.STATE index.
        """

        return (
            self.get_queryset()
            .filter(stages__state=state_index)
            .select_related("entryform")
        )


class UndeletedManager(models.Manager):
    """Custom manager for models with deleted_at fields.
    It's main purpouse is to scope the queryset to all
    instances that haven't been deleted.
    """

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Analysis(AnalysisForm):
    """
    Proxy class for :model:`backend.AnalysisForm`, it's used in the Review app to filter
    AnalysisForm according to their status, and order them by priorities,
    without touching the other app's implementation.
    """

    objects = AnalysisManager()

    @property
    def email_subject(self):
        """Returns a string of key data for an email's subject"""
        subject = []
        case = self.entryform

        if case.customer:
            subject.append(case.customer.name)
        
        if self.entryform.company_center != None:
            subject.append(self.entryform.company_center.center.name)
        elif self.entryform.company_laboratory != None:
            subject.append(self.entryform.company_laboratory)
            

        subject.append(self.exam.name)

        return "/".join(subject)

    def set_report_code(self):
        """Stores a report code following the format VHC-00000-000"""
        case = str(self.entryform.no_caso[1:]).zfill(5)
        service = str(self.exam_id).zfill(3)
        self.report_code = f"VHC-{case}-{service}"
        self.save()

    def get_recipients(self):
        """Returns a dictionary containing all emails from self's MailLists, separated by To and CC."""
        to = []
        cc = []

        for mails in self.analysisrecipient_set.all():
            mail = mails.recipient.email
            if mails.is_main:
                to.append(mail)
            else:
                cc.append(mail)
        return {"to": to, "cc": cc}

    def get_sendable_file(self):
        """Returns self's :model:`review.File` which is available to be send."""
        return FinalReport.objects.filter(analysis=self).order_by("created_at")

    def get_basename(self, index_text, date):
        """Returns filename without extension"""
        return f"{self.entryform.no_caso}_{self.exam.abbreviation}{index_text}_{date}"

    def get_template_context(self):
        """Returns a dictionary detailing specific data for templating."""
        return {
            "center": self.entryform.company_center.center.name if self.entryform.company_center != None else (self.entryform.company_laboratory if self.entryform.company_laboratory != None else ''),
            "customer": self.entryform.customer.name,
            "exam": self.exam.name
        }

    def get_pathologist(self):
        """Returns a list with all pathologists (User) assigned to the Analysis."""
        assigned_areas = UserArea.objects.filter(user=self.patologo).values_list("area", flat=True)
        area_leads = UserArea.objects.filter(area__in=assigned_areas, role=0).exclude(user=self.patologo)
        users = User.objects.filter(pk__in=area_leads.values_list("user", flat=True))
        emails = users.values_list("email", flat=True)
        return [self.patologo.email, *emails]

    def attach_external_reports(self, external_reports):
        """Attaches external reports to grouped Analysis."""
        for report in external_reports:
            self.external_reports.add(report)

    def close(self):
        form = self.forms.get()
        form.form_closed = True
        form.closed_at = datetime.now()
        form.save()

        self.manual_closing_date = datetime.now()
        self.save()

    class Meta:
        proxy = True
        permissions = (("send_email", "Can send an email"),)


class Grouper(models.Model):
    """
    Allows multiple :model:`backend.AnalysisForm` to be grouped to be delivered under one email as one
    document.
    """
    name = models.CharField(max_length=90, null=True, blank=True)

    entryform = models.ForeignKey(EntryForm, models.CASCADE)
    analysis = models.ManyToManyField(Analysis, related_name="groups", through="AnalysisGrouper")
    subclass = models.CharField(max_length=30, null=True, blank=True, verbose_name="subclase")
    subclass_abbreviation = models.CharField(max_length=5, null=True, blank=True)

    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = GrouperManager()

    @property
    def email_subject(self):
        """Returns a string of key data for an email's subject"""
        subject = []
        case = self.entryform

        if case.customer:
            subject.append(case.customer.name)

        if self.entryform.company_center != None:
            subject.append(self.entryform.company_center.center.name)
        elif self.entryform.company_laboratory != None:
            subject.append(self.entryform.company_laboratory)

        return "/".join(subject)

    @property
    def title(self):
        """Returns the grouper's service abbreviation"""
        if self.subclass_abbreviation:
            return self.subclass_abbreviation

        exam_pks = self.analysis.all().values_list("exam_id", flat=True)
        abbreviation = Exam.objects.filter(id__in=exam_pks).values_list("abbreviation", flat=True)
        abbreviation_text = "-".join(abbreviation)

        return abbreviation_text


    def get_recipients(self):
        """Returns a dictionary containing all emails from self's MailLists, separated by To and CC."""
        to = []
        cc = []

        for mails in self.analysisrecipient_set.all():
            mail = mails.recipient.email
            if mails.is_main:
                to.append(mail)
            else:
                cc.append(mail)
        return {"to": to, "cc": cc}

    def get_sendable_file(self):
        """Returns self's :model:`review.File` which is available to be send."""
        return FinalReport.objects.filter(grouper=self).order_by("created_at")

    def get_basename(self, index_text, date):
        """Returns filename without extension"""
        if self.subclass_abbreviation:
            return f"{self.entryform.no_caso}_{self.subclass_abbreviation}{index_text}_{date}"

        exam_pks = self.analysis.all().values_list("exam_id", flat=True)
        abbreviation = Exam.objects.filter(id__in=exam_pks).values_list("abbreviation", flat=True)
        abbreviation_text = "-".join(abbreviation)

        return f"{self.entryform.no_caso}_{abbreviation_text}{index_text}_{date}"

    def get_template_context(self):
        """Returns a dictionary detailing specific data for templating."""
        exam = []
        for analysis in self.analysis.all():
            exam.append(analysis.exam.name)

        return {
            "center": self.entryform.company_center.center.name if self.entryform.company_center != None else (self.entryform.company_laboratory if self.entryform.company_laboratory != None else ''),
            
            "customer": self.entryform.customer.name,
            "exam": ", ".join(exam)
        }

    def get_pathologist(self):
        """Returns a list with all pathologists (User) assigned to the Analysis."""
        emails = []
        pathologist = self.analysis.all().values_list("patologo", flat=True)
        user = User.objects.filter(pk__in=pathologist)
        areas = UserArea.objects.filter(user__in=user).values_list("area", flat=True)
        leads = UserArea.objects.filter(area__in=areas, role=0).exclude(user__in=user).values_list("user", flat=True)
        users = User.objects.filter(pk__in=[*pathologist, *leads])
        return users.values_list("email", flat=True)

    def close(self):
        closed_date = datetime.now()
        for analysis in self.analysis.all():
            analysis.close()
        self.closed_at = closed_date
        self.save()

    def attach_external_reports(self, external_reports):
        """Attaches external reports to grouped Analysis."""
        for analysis in self.analysis.all():
            for report in external_reports:
                analysis.external_reports.add(report)

    def __str__(self):
        if self.name:
            return str(self.name)
        return f"{self.entryform} - {self.id}"


class Stage(models.Model):
    """
    Details a single stage in which an :model:`review.Analysis` is currently at.
    """

    STATES = (
        (0, "ESPERA"),
        (1, "FORMATO"),
        (2, "REVISION"),
        (3, "ENVIO"),
        (4, "FINALIZADO"),
    )

    analysis = models.ForeignKey(
        AnalysisForm, on_delete=models.CASCADE, related_name="stages", null=True
    )
    grouper = models.ForeignKey(
        Grouper, on_delete=models.CASCADE, related_name="stages", null=True
    )
    state = models.CharField(max_length=1, choices=STATES, default=0)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="review_stages", null=True
    )
    created_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Logbook.objects.create(stage=self, state=self.state, user=self.created_by)


class Logbook(models.Model):
    """
    Stores detailed information relate to a :model:`review.Stage` changes.
    """

    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name="logbooks")

    state = models.CharField(max_length=1, choices=Stage.STATES)

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="logbooks", null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class File(models.Model):
    """Stores a single file path in the database alognside it's related :model:`review.Stage`"""

    path = models.FileField("reviews")
    analysis = models.ForeignKey(
        Analysis, on_delete=models.CASCADE, related_name="files", null=True
    )
    grouper = models.ForeignKey(
        Grouper, on_delete=models.CASCADE, related_name="files", null=True
    )
    state = models.CharField(max_length=1, choices=Stage.STATES)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="files", null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Recipient(models.Model):
    """
    Stores a single resource which will receive an email with :model:`review.File` for it's related
    :model:`review.Analysis` whenever this it's moved to a :model:`review.Stage` finished.
    """

    objects = UndeletedManager()
    items = models.Manager()

    email = models.EmailField()
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, verbose_name="Desactivado")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name


class MailList(models.Model):
    """
    Allows grouping multiple :model:`review.Recipient` under the same :model:`backend.Customer`
    """

    objects = UndeletedManager()
    items = models.Manager()

    name = models.CharField(max_length=255)
    customer = models.ForeignKey(
        to=Customer, on_delete=models.CASCADE, related_name="mailing_lists"
    )
    recipients = models.ManyToManyField(
        to=Recipient, related_name="mailing_lists", through="RecipientMail"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, verbose_name="Desactivado")

    @property
    def recipients_email(self):
        """Returns a list of email for all Recipients."""
        to = []
        cc = []

        for entry in RecipientMail.objects.filter(mail_list=self, is_main=True):
            to.append(entry.recipient.email)

        for entry in RecipientMail.objects.filter(mail_list=self, is_main=False):
            cc.append(entry.recipient.email)

        return {"to": to, "cc": cc}

    def __str__(self):
        return self.name


class RecipientMail(models.Model):
    recipient = models.ForeignKey(
        Recipient, on_delete=models.CASCADE, related_name="mail_lists"
    )
    mail_list = models.ForeignKey(
        MailList, on_delete=models.CASCADE, related_name="recipients_emails"
    )
    is_main = models.BooleanField(default=False)

    class Meta:
        db_table = "review_recipient_mail"

    def __str__(self):
        return f"{self.mail_list.name} {self.recipient.first_name}"


class AnalysisRecipient(models.Model):
    """
    A :model:`review.Analysis` may contain multiple :model:`review.Recipient` and vice-versa thus this model works
    as a middle-man to join them.
    """

    analysis = models.ForeignKey(to=Analysis, on_delete=models.CASCADE, null=True)
    grouper = models.ForeignKey(to=Grouper, on_delete=models.CASCADE, null=True)
    recipient = models.ForeignKey(to=Recipient, on_delete=models.CASCADE)
    is_main = models.BooleanField(
        verbose_name="Is primary recipient (TO)", default=True
    )


class FinalReport(models.Model):
    """
    Stores a final report file for a :model:`review.Analysis`
    """
    path = models.FileField("reports")
    analysis = models.ForeignKey(
        Analysis, on_delete=models.CASCADE, related_name="final_reports", null=True
    )
    grouper = models.ForeignKey(
        Grouper, on_delete=models.CASCADE, related_name="final_reports", null=True
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="reports_uploaded", null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Attachment(models.Model):
    """
    Stores an attachment for the final email send to a :model:`review.Analysis` client.
    """
    path = models.FileField("attachments")
    analysis = models.ForeignKey(
        Analysis, on_delete=models.CASCADE, related_name="final_attachments", null=True
    )
    grouper = models.ForeignKey(
        Grouper, on_delete=models.CASCADE, related_name="final_attachments", null=True
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="final_attachments_uploaded", null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class AnalysisGrouper(models.Model):
    """
    Intermediary model between :model:`backend.AnalysisForm` and :model:`review.Grouper`.
    """
    analysis = models.ForeignKey(Analysis, models.CASCADE)
    grouper = models.ForeignKey(Grouper, models.CASCADE)

    def __str__(self):
        return f"Analisis: {self.analysis}; Grupo: {self.grouper}"
    
class BlindCarbonCopy(models.Model):
    email = models.CharField(max_length=255)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "BCC"
        verbose_name_plural = "BCCs"