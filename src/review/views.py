import json
import mimetypes
import os
from datetime import datetime
from re import template
from smtplib import SMTPException

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import mail, serializers
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.forms.models import model_to_dict
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import get_template
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from backend.models import AnalysisForm, ExternalReport
from review.models import (Analysis, AnalysisGrouper, AnalysisRecipient, Attachment, BlindCarbonCopy, File, FinalReport, Grouper,
                           MailList, Recipient, RecipientMail, Stage,)


@login_required
@permission_required("review.view_stage", raise_exception=True)
def index(request):
    """
    Renders template which lists multiple :model:`review.Analysis` grouped by
    their state, allowing the user to move them accross multiple states as necessary.
    """

    recipients = Recipient.objects.all()
    return render(request, "index.html", {"recipients": recipients})



@login_required
@permission_required("review.view_stage", raise_exception=True)
def list(request, index):
    """
    Returns a JSON detailing all :model:`review.Analysis` where their :model:`review.Stage`
    state has the current index.
    """
    analysis = None
    groups = None

    def serialize_analysis(queryset):
        context = []
        for item in queryset:
            context.append(
                serializers.serialize(
                    "json", [item, item.entryform, item.exam, item.entryform.customer]
                )
            )
        return context

    def serialize_groupers(queryset):
        context = []
        for item in queryset:
            group_dict = model_to_dict(item, fields=["id", "name"])
            group_dict["title"] = item.title
            row = {
                "group": group_dict,
                "case": model_to_dict(item.entryform, fields=["id", "no_caso", "center"], exclude=['center']),
                "customer": model_to_dict(item.entryform.customer, fields=["name"]),
            }
            context.append(row)

        return context

    analysis_grouper = AnalysisGrouper.objects.filter(
        grouper__closed_at__isnull=True,
        analysis__exam__pathologists_assignment=True,
        analysis__pre_report_started=True,
        analysis__pre_report_ended=True
    )
    analysis_pk = analysis_grouper.values_list("analysis_id", flat=True)
    groupers_pk = analysis_grouper.values_list("grouper_id", flat=True)

    if index in (1, 2, 3, 4):
        analysis = Analysis.objects.stage(index, request.user).exclude(pk__in=analysis_pk)
        groups = Grouper.objects.stage(index).filter(pk__in=groupers_pk)

    else:
        analysis = Analysis.objects.waiting(request.user).exclude(pk__in=analysis_pk)
        groups = Grouper.objects.waiting().filter(pk__in=groupers_pk)

    context = {
        "analysis": serialize_analysis(analysis),
        "grouper": serialize_groupers(groups)
    }
    return JsonResponse(context, safe=False)


class UpdateStageView(View, LoginRequiredMixin):
    """
    Updates a :model:`review.Stage`, storing the change in :model:`review.Logbook`.
    """

    def update_analysis(self, pk, state, user):
        analysis = get_object_or_404(Analysis, pk=pk)

        stage = Stage.objects.update_or_create(
            analysis=analysis, defaults={"state": state, "created_by": user}
        )

        return (stage[0], analysis)

    def update_grouper(self, pk, state, user):
        grouper = get_object_or_404(Grouper, pk=pk)

        stage = Stage.objects.update_or_create(
            grouper=grouper, defaults={"state": state, "created_by": user}
        )

        return (stage[0], grouper)

    def post(self, request, *args, **kwargs):
        post = json.loads(request.body)
        state = post["state"]

        obj = kwargs.get("type", 0)

        result = None
        if obj == 1:
            result = self.update_grouper(kwargs.get("pk"), state, request.user)
        else:
            result = self.update_analysis(kwargs.get("pk"), state, request.user)

        return JsonResponse(serializers.serialize("json", result), safe=False)


@login_required
def object_mailing_list(request, type, pk):
    """
    Returns a JsonResponse with a list detailing the given
    pk's :model:`review.Analysis` its :model:`review.MailList`
    """
    recipients_pk = []
    if type == 0:
        recipients_pk = AnalysisRecipient.objects.filter(analysis_id=pk).values_list(
            "recipient_id", flat=True
        )
    elif type == 1:
        recipients_pk = AnalysisRecipient.objects.filter(grouper_id=pk).values_list(
            "recipient_id", flat=True
        )
    recipients = Recipient.objects.filter(pk__in=recipients_pk)

    return JsonResponse(serializers.serialize("json", recipients), safe=False)


class EmailSendView(View, LoginRequiredMixin):
    def send_email(self, request, pk, correlatives, is_analysis=True, is_test=False, language=1 , template=1 ):
        """
        Takes a :model:`review.Analysis`'pk and sends an email to all :model:`review.MailList`
        of that Analysis, returns a JSON with `status` according to wether all emails were send
        succesfully.
        Receives in the request an integer defining the language where 0 is english and 1 is spanish.
        It defaults to 1 when the value is invalid or not received.
        Returns a JSON with `status` which can be either OK or ERR, if ERR then it will also send a `code`
        which is either 0 for not file attachment, or 1 for bad email.
        """
        obj = None
        reports = None
        attachments = []
        if is_analysis:
            reports = FinalReport.objects.filter(analysis_id=pk).order_by("created_at")
            obj = get_object_or_404(Analysis, pk=pk)
            attachments = Attachment.objects.filter(analysis_id=pk)
        else:
            reports = FinalReport.objects.filter(grouper_id=pk).order_by("created_at")
            obj = get_object_or_404(Grouper, pk=pk)
            attachments = Attachment.objects.filter(grouper_id=pk)

        if reports.count() <= 0:
            return JsonResponse({"status": "ERR", "code": 0})

        recipients = obj.get_recipients()
        if len(recipients["to"]) <= 0:
            return JsonResponse({"status": "ERR", "code": 1})


        report_index = 1
        current_date = datetime.now().strftime("%d%m%y")
        pathologists = obj.get_pathologist()

        analysis_report_codes = []
        emails = []
        external_reports = []
        for report in reports:
            index = None
            key = str(report.id)
            if key in correlatives:
                index = correlatives[key]
            else:
                index = report_index
            report_index += 1
            index_text = str(index).zfill(2)
            basename = obj.get_basename(index_text, current_date)
            analysis_report_codes.append(basename)
            context = obj.get_template_context()
            context["report_code"] = basename

            subject = f"{obj.email_subject}/{basename}"
            if is_test:
                subject = "[PRUEBA]" + subject

            template_format = "normal_"
            if template == 0:
                template_format = "rectificacion_"
            elif template == 2:
                template_format = "remision_"
                
            template_name = "email_es.html"
            if language == 0:
                template_name = "email_en.html"
            
            """template_format = "normal_"
            if template == 0:
                template_format = "rectificacion_"
            elif template == 1:
                template_format = "remision_"

            template_name = "email_es.html"
            if language == 0:
                template_name = "email_en.html"
                """
            """
            template_format = "remision_"
            if template == 1:
                template_format = "remision_"
            else:
                template_name = "email_en.html"
            """
            """template_name = "remision.html"
            if language == 0:
                template_format = "remision_es.html"
            """
            message = get_template(template_format+template_name).render(context=context)

            bcc = []
            to = []
            cc = []
            if is_test:
                to = [request.user.email]
                bcc = []
            else:
                to = recipients["to"]
                cc = recipients["cc"]
                bccs = BlindCarbonCopy.objects.all().values_list("email", flat=True)
                bcc = [*bccs, *pathologists]

            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email='"VeHiCe"<reports@vehice.com>',
                to=to,
                cc=cc,
                bcc=bcc,
            )
            email.content_subtype = "html"

            filename = basename
            case = obj.entryform

            if case.customer:
                filename = filename + " " + case.customer.name

            if case.center:
                filename = filename + " " + case.center

            content_type = mimetypes.guess_type(report.path.name)[0]
            email.attach(
                filename + ".pdf",
                report.path.read(),
                content_type,
            )

            for attachment in attachments:
                content_type = mimetypes.guess_type(attachment.path.name)[0]
                email.attach(
                    attachment.path.name,
                    attachment.path.read(),
                    content_type,
                )


            emails.append(email)

            external_report = ExternalReport.objects.create(
                created_at=datetime.now(),
                file=report.path,
                loaded_by=report.user
            )
            external_reports.append(external_report)


        connection = mail.get_connection(username="reports@vehice.com", password="djNF94&7")

        try:
            connection.send_messages(emails)
        except (BadHeaderError, SMTPException):
            return JsonResponse({"status": "ERR", "code": 2})
        connection.close()

        if not is_test:
            if is_analysis:
                stage = Stage.objects.update_or_create(
                    analysis_id=pk, defaults={"state": 4, "created_by": request.user}
                )
                obj.report_code = " / ".join(analysis_report_codes)
                obj.save()
            else:
                stage = Stage.objects.update_or_create(
                    grouper_id=pk, defaults={"state": 4, "created_by": request.user}
                )
                analysisgroupers = AnalysisGrouper.objects.filter(grouper=obj)
                for analysis in analysisgroupers:
                    analysis.analysis.report_code = " / ".join(analysis_report_codes)
                    analysis.analysis.save()

            obj.close()
        return JsonResponse({"status": "OK"})


    def put(self, request, *args, **kwargs):
        data = json.loads(request.body)
        pk = data["pk"]
        is_analysis = data["analysis"] and not data["grouper"]
        is_test = data["test"]
        language = int(data["language"])     
        template = int(data["template"])
        correlatives = data["correlatives"]
        return self.send_email(request, pk, correlatives, is_analysis, is_test, language, template)


class MailListView(View):
    def get(self, request, pk):
        """Returns a JSON list with all :model:`review.Recipients` from a single :model:`review.MailList`."""
        mail_list = get_object_or_404(MailList, pk=pk)

        recipients_lists = RecipientMail.objects.filter(mail_list=mail_list)

        context = []
        for recipient_list in recipients_lists:
            row = model_to_dict(
                recipient_list.recipient,
                fields=["id", "first_name", "last_name", "email"],
            )
            row["is_main"] = recipient_list.is_main
            context.append(row)

        return JsonResponse(context, safe=False)

    def post(self, request, pk):
        """
        Stores a single new :model:`review.MailList`
        and returns the created resource in JSON.

        Required:
            - name
            - recipients
        """
        form_data = json.loads(request.body)

        analysis = get_object_or_404(Analysis, pk=pk)
        customer = analysis.entryform.customer

        mail_list = MailList.objects.create(name=form_data["name"], customer=customer)

        for recipient in form_data["recipients"]:
            RecipientMail.objects.create(
                mail_list=mail_list,
                recipient_id=recipient["id"],
                is_main=recipient["is_main"],
            )

        return JsonResponse(model_to_dict(mail_list, fields=["id", "name"]), safe=False)

    def put(self, request, pk):
        """Updates a single existing :model:`review.MailList`
        and returns a JSON detailing the created resource."""
        form_data = json.loads(request.body)

        mail_list = get_object_or_404(MailList, pk=pk)

        RecipientMail.objects.filter(mail_list=mail_list).delete()

        for recipient in form_data:
            RecipientMail.objects.create(
                mail_list=mail_list,
                recipient_id=recipient["id"],
                is_main=recipient["is_main"],
            )

        return JsonResponse(model_to_dict(mail_list, fields=["id", "name"]), safe=False)


@login_required
def new_recipient(request):
    """
    Stores a single new :model:`lab.Recipient`
    and returns the created resource in JSON.

    Required:
        - first_name
        - email
    Optional:
        - last_name
        - role
    """
    form_data = json.loads(request.body)

    recipient = Recipient.objects.create(
        first_name=form_data["first_name"],
        last_name=form_data["last_name"],
        role=form_data["role"],
        email=form_data["email"],
    )

    return JsonResponse(model_to_dict(recipient), safe=False)


class FileView(View, LoginRequiredMixin):

    def get_analysis_files(self, pk):
        analysis = get_object_or_404(Analysis, pk=pk)

        prereport_files = []
        for prefile in analysis.external_reports.all():
            filename = prefile.file.name.split("/")
            prereport_files.append({"name": filename[1], "download": prefile.file.url})

        review_files = []
        for review in File.objects.filter(analysis=analysis).order_by("created_at"):
            try:
                review_files.append(
                    {
                        "name": review.path.name,
                        "download": review.path.url,
                        "state": review.state,
                        "created_at": review.created_at,
                        "delete_url": reverse("review:files", kwargs={"pk": review.id, "type": 0})
                    }
                )
            except ValueError:
                pass

        final_files = []
        final_files_index = 1
        current_date = datetime.now().strftime("%d%m%y")
        for final_report in FinalReport.objects.filter(analysis=analysis).order_by("created_at"):
            index_text = str(final_files_index).zfill(2)
            base_name = f"{final_report.analysis.entryform.no_caso}_{final_report.analysis.exam.abbreviation}{index_text}_{current_date}"
            final_files_index += 1
            try:
                final_files.append(
                    {
                        "id": final_report.id,
                        "name": base_name,
                        "original": final_report.path.name,
                        "download": final_report.path.url,
                        "created_at": final_report.created_at,
                        "delete_url": reverse("review:final_report", kwargs={"pk": final_report.id, "type": 0})
                    }
                )
            except ValueError:
                pass

        attachments = []
        for attachment in Attachment.objects.filter(analysis=analysis).order_by("created_at"):
            try:
                attachments.append({
                    "name": attachment.path.name,
                    "download": attachment.path.url,
                    "created_at": attachment.created_at,
                    "delete_url": reverse("review:attachment", kwargs={"pk": attachment.id, "type": 0})
                })
            except ValueError:
                pass

        return {
            "prereports": prereport_files,
            "reviews": review_files,
            "final_reports": final_files,
            "attachments": attachments
        }

    def get_analysis_grouper(self, pk):
        group = get_object_or_404(Grouper, pk=pk)
        entryform = group.entryform

        prereport_files = []
        for analysis in group.analysis.all():
            for prefile in analysis.external_reports.all():
                filename = prefile.file.name.split("/")
                prereport_files.append({"name": filename[1], "download": prefile.file.url})

        review_files = []
        for review in File.objects.filter(grouper=group).order_by("created_at"):
            try:
                review_files.append(
                    {
                        "name": review.path.name,
                        "download": review.path.url,
                        "state": review.state,
                        "created_at": review.created_at,
                        "delete_url": reverse("review:files", kwargs={"pk": review.id, "type": 0})
                    }
                )
            except ValueError:
                pass

        final_files = []
        final_files_index = 1
        current_date = datetime.now().strftime("%d%m%y")
        for final_report in FinalReport.objects.filter(grouper=group).order_by("created_at"):
            index_text = str(final_files_index).zfill(2)
            base_name = group.get_basename(index_text, current_date)
            final_files_index += 1
            try:
                final_files.append(
                    {
                        "name": base_name,
                        "original": final_report.path.name,
                        "download": final_report.path.url,
                        "created_at": final_report.created_at,
                        "delete_url": reverse("review:final_report", kwargs={"pk": final_report.id, "type": 0})
                    }
                )
            except ValueError:
                pass

        attachments = []
        for attachment in Attachment.objects.filter(grouper=group).order_by("created_at"):
            try:
                attachments.append({
                    "name": attachment.path.name,
                    "download": attachment.path.url,
                    "created_at": attachment.created_at,
                    "delete_url": reverse("review:attachment", kwargs={"pk": attachment.id, "type": 0})
                })
            except ValueError:
                pass

        return {
            "prereports": prereport_files,
            "reviews": review_files,
            "final_reports": final_files,
            "attachments": attachments
        }


    def get(self, request, *args, **kwargs):
        """
        Returns a list of files that belong to a single :model:`review.Analysis`
        """

        obj = kwargs.get("type", 0)
        pk = kwargs.get("pk")

        context = None
        if obj == 0:
            context = self.get_analysis_files(pk)
        elif obj == 1:
            context = self.get_analysis_grouper(pk)

        return JsonResponse(context)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """
        Stores a file resource and creates a :model:`review.File` to bind it to
        an :model:`review.Stage`
        """

        obj = kwargs.get("type", 0)
        pk = kwargs.get("pk")

        if obj == 0:
            analysis = get_object_or_404(Analysis, pk=pk)
            stage = Stage.objects.filter(analysis=analysis).first()
            review_file = File(
                path=request.FILES.get("file"),
                analysis=analysis,
                state=stage.state if stage else 0,
                user=request.user,
            )
        elif obj == 1:
            grouper = get_object_or_404(Grouper, pk=pk)
            stage = Stage.objects.filter(grouper=grouper).first()
            review_file = File(
                path=request.FILES.get("file"),
                grouper=grouper,
                state=stage.state if stage else 0,
                user=request.user,
            )

        review_file.save()
        return JsonResponse(serializers.serialize("json", [review_file]), safe=False)

    @method_decorator(login_required)
    def delete(self, request, *args, **kwargs):
        """
        Deletes a file resource from the server.
        """

        pk = kwargs.get("pk")
        review_file = File.objects.get(pk=pk)

        if review_file.path:
            if os.path.exists(review_file.path.path):
                os.remove(review_file.path.path)

        review_file.delete()

        return JsonResponse({"status": "OK"})


class AnalysisRecipientView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """
        Returns a JSON containing a list of all :model:`review.MailList` for the given pk's
        :model:`review.Analysis`'s entryform's customer, including as well the current selected
        ones.
        """
        obj = kwargs.get("type", 0)
        pk = kwargs.get("pk")

        customer = None
        current_recipients = None
        if obj == 0:
            analysis = get_object_or_404(Analysis, pk=pk)
            customer = analysis.entryform.customer
            current_recipients = AnalysisRecipient.objects.filter(analysis=analysis)
        elif obj == 1:
            grouper = get_object_or_404(Grouper, pk=pk)
            customer = grouper.entryform.customer
            current_recipients = AnalysisRecipient.objects.filter(grouper=grouper)

        mail_lists = MailList.objects.filter(customer=customer)

        return JsonResponse(
            {
                "mail_lists": serializers.serialize("json", mail_lists),
                "current_recipients": serializers.serialize("json", current_recipients),
            }
        )

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """
        Updates the given pk's :model:`review.Analysis`'s related :model:`review.MailList`.
        Returns a JSON containing the status between OK or ERR, in which case will also include
        and array containing ids which caused the error.
        """
        obj = kwargs.get("type", 0)
        pk = kwargs.get("pk")

        if obj == 0:
            AnalysisRecipient.objects.filter(analysis_id=pk).delete()
        elif obj == 1:
            AnalysisRecipient.objects.filter(grouper_id=pk).delete()

        recipients = json.loads(request.body)
        errors = []
        for recipient in recipients:
            try:
                recipient_instace = Recipient.objects.get(pk=recipient["pk"])
            except Recipient.DoesNotExist:
                errors.append(recipient)
                continue
            else:
                if obj == 0:
                    AnalysisRecipient.objects.create(
                        analysis_id=pk,
                        recipient=recipient_instace,
                        is_main=recipient["is_main"],
                    )
                elif obj == 1:
                    AnalysisRecipient.objects.create(
                        grouper_id=pk,
                        recipient=recipient_instace,
                        is_main=recipient["is_main"],
                    )

        if len(errors) > 0:
            return JsonResponse({"status": "ERR", "errors": errors})

        return JsonResponse({"status": "OK"})


class FinalReportView(View):
    def post(self, request, *args, **kwargs):
        """Stores a new :model:`review.FinalReport` file."""
        obj = kwargs.get("type", 0)
        pk = kwargs.get("pk")

        final_report = FinalReport(
            path=request.FILES.get("file"),
            user=request.user
        )
        if obj == 0:
            final_report.analysis_id = pk
        elif obj == 1:
            final_report.grouper_id = pk

        try:
            final_report.save()
        except:
            return JsonResponse({"status": "ERR"})

        return JsonResponse({"status": "OK"})

    def delete(self, request, *args, **kwargs):
        """
        Removes a :model:`review.FinalReport` from the database and the respective file
        from the filesystem.
        """
        pk = kwargs.get("pk")
        final_report = get_object_or_404(FinalReport, pk=pk)
        final_report.delete()

        return JsonResponse({"status": "OK"})


class AttachmentView(View):
    def post(self, request, *args, **kwargs):
        """Stores a new :model:`review.Attachment` file."""

        obj = kwargs.get("type", 0)
        pk = kwargs.get("pk")

        attachment = Attachment(
            path=request.FILES.get("file"),
            user=request.user
        )

        if obj == 0:
            attachment.analysis_id = pk
        elif obj == 1:
            attachment.grouper_id = pk

        try:
            attachment.save()
        except:
            return JsonResponse({"status": "ERR"})

        return JsonResponse({"status": "OK"})

    def delete(self, request, *args, **kwargs):
        """
        Removes a :model:`review.Attachment` from the database and the respective file
        from the filesystem.
        """
        pk = kwargs.get("pk")
        attachment = get_object_or_404(Attachment, pk=pk)
        attachment.delete()

        return JsonResponse({"status": "OK"})


class GrouperView(View):
    def get(self, request, *args, **kwargs):
        """
        Returns a list with :model:`review.Grouper` for the given
        :model:`review.EntryForm`.
        """
        pk = request.GET.get("pk")
        analysis = get_object_or_404(AnalysisForm, pk=pk)
        entryform = analysis.entryform
        groupers = Grouper.objects.filter(entryform=entryform)
        selected = AnalysisGrouper.objects.filter(analysis=analysis)

        context = {
            "groupers": serializers.serialize("json", groupers),
            "selected": serializers.serialize("json", selected)
        }

        return JsonResponse(context)

    def post(self, request, *args, **kwargs):
        """
        Creates a new :model:`review.Grouper`.
        """
        data = json.loads(request.body)
        pk = data["pk"]
        analysis = get_object_or_404(AnalysisForm, pk=pk)
        exam = analysis.exam
        entryform = analysis.entryform
        grouper = Grouper.objects.create(name=data["name"], entryform=entryform, subclass=exam.subclass, subclass_abbreviation=exam.subclass_abbreviation)
        AnalysisGrouper.objects.create(grouper=grouper, analysis=analysis)
        return JsonResponse(model_to_dict(grouper, fields=["id", "name"]), safe=False)


    def put(self, request, *args, **kwargs):
        """
        Adds or removes a :model:`backend.AnalysisForm` from a group.
        """
        data = json.loads(request.body)
        analysis_pk = data["analysis_pk"]
        grouper_pk = data["grouper_pk"]

        analysis = get_object_or_404(AnalysisForm, pk=analysis_pk)
        grouper = get_object_or_404(Grouper, pk=grouper_pk)
        try:
            AnalysisGrouper.objects.get(analysis_id=analysis_pk, grouper_id=grouper_pk).delete()
        except AnalysisGrouper.DoesNotExist:
            if analysis.exam.subclass == grouper.subclass:
                AnalysisGrouper.objects.create(analysis_id=analysis_pk, grouper_id=grouper_pk)
            else:
                return JsonResponse({
                    "status": "ERR"
                }, status=400)


        return JsonResponse({
            "status": "OK"
        })
