from email.headerregistry import Group
import json
import random
import string
from datetime import datetime, timedelta
from distutils.util import strtobool
import xlsxwriter
import io
from itertools import islice
import pdfkit

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import mail
from django.core.mail import BadHeaderError, EmailMultiAlternatives, send_mail
from django.db import connection
from django.db.models import F, Prefetch
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.core.serializers import serialize
from django.http import QueryDict, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.cache import never_cache
from django.urls import reverse
from django.views.decorators.cache import cache_page
from PyPDF2 import PdfReader, PdfWriter

from accounts.models import *
from app import views as app_view
from backend.models import *
from mb.models import Pool
from review.models import AnalysisGrouper, FinalReport, Analysis
from workflows.models import *
from lab.models import Analysis, Cassette
from smtplib import SMTPException
from datetime import date

#para img file
import base64

#render para imagenes
from django.template.loader import render_to_string

from collections import defaultdict

import logging
logger = logging.getLogger(__name__)

class CUSTOMER(View):
    http_method_names = ["post"]

    def post(self, request):
        """
        Stores a new :model:`backend.Customer`
        """
        var_post = request.POST.copy()

        if var_post.get("laboratorio") == "on":
            laboratorio = "l"
        else:
            laboratorio = "s"

        customer = Customer.objects.create(
            name=var_post.get("nombre"),
            company=var_post.get("rut"),
            type_customer=laboratorio,
        )
        customer.save()

        return JsonResponse({"ok": True})


class EXAM(View):
    http_method_names = ["post"]

    def post(self, request):
        """
        Stores a new :model:`backend.Exam`
        """
        var_post = request.POST.copy()

        exam = Exam.objects.create(
            name=var_post.get("nombre"),
        )
        exam.save()

        return JsonResponse({"ok": True})


class ORGAN(View):
    http_method_names = ["get"]

    def get(self, request, organ_id=None):
        if organ_id:
            organ = Organ.objects.filter(pk=organ_id)
        else:
            organs = list(Organ.objects.all().values())

            data = {
                "organs": organs,
            }

        return JsonResponse(data)


class ENTRYFORM(View):
    http_method_names = ["get"]

    def get(self, request, id=None):
        if id:
            entryform = EntryForm.objects.values().get(pk=id)
            entryform_object = EntryForm.objects.get(pk=id)
            identifications = list(
                Identification.objects.filter(
                    entryform=entryform["id"]).values()
            )

            samples = Sample.objects.filter(entryform=entryform["id"]).order_by(
                "index"
            )

            samples_as_dict = []
            analysis_status = {}
            
            for s in samples:
                s_dict = model_to_dict(
                    s,
                    exclude=["organs", "unit_organs",
                             "sampleexams", "identification"],
                )
                organs = []

                for org in s.unit_organs.all():
                    unit = model_to_dict(
                        org.unit,
                        exclude=[
                            "organs",
                        ],
                    )
                    organ = model_to_dict(org.organ)
                    organs.append(
                        {"unit": unit, "organ": organ, "organ_unit_id": org.id}
                    )

                s_dict["organs_set"] = organs

                sampleexams = s.sampleexams_set.all()

                sampleExa = {}
                for sE in sampleexams:
                    key = str(sE.exam_id) + '-' + str(sE.stain_id)
                    if  key not in analysis_status:
                        analysis_status[key]= entryform_object.analysisform_set.filter(exam_id=sE.exam_id, stain_id=sE.stain_id).first().status

                    exam_stain_tuple = str(sE.exam_id) + "-" + str(sE.stain_id)

                    uo_organ_id = None

                    if sE.unit_organ is not None:
                        uo_organ_id = sE.unit_organ.organ.id
                    else:
                        # Fix missing unit organ related to sample exams (old cases)
                        for uo in s.unit_organs.all():
                            if uo.organ_id == sE.organ_id:
                                sE.unit_organ = uo
                                sE.save()
                                uo_organ_id = uo.organ_id
                                break

                    sE_dict = {
                        "organ_name": sE.organ.name,
                        "uo_id": sE.unit_organ_id,
                        "uo_organ_id": uo_organ_id,
                        "organ_id": sE.organ.id,
                        "stain_id": sE.stain_id,
                        "stain_abbr": sE.stain.abbreviation,
                        "exam_id": sE.exam_id,
                        "exam_name": sE.exam.name,
                        "analysis_status": analysis_status[key],
                    }

                    if exam_stain_tuple in sampleExa.keys():
                        sampleExa[exam_stain_tuple].append(sE_dict)
                    else:
                        sampleExa[exam_stain_tuple] = [sE_dict]

                s_dict["sample_exams_set"] = sampleExa
                s_dict["identification"] = model_to_dict(
                    s.identification, exclude=[
                        "organs", "organs_before_validations"]
                )
                samples_as_dict.append(s_dict)

            entryform["identifications"] = []
            for ident in entryform_object.identification_set.all():
                ident_json = model_to_dict(
                    ident,
                    exclude=[
                        "organs",
                        "organs_before_validations",
                        "no_fish",
                        "no_container",
                        "temp_id",
                    ],
                )
                entryform["identifications"].append(ident_json)

            entryform["analyses"] = []
            for analysis in entryform_object.analysisform_set.filter(exam__isnull=False):
                try:
                    analysis_form = analysis.forms.get()
                except Form.DoesNotExist:
                    continue

                samples = Sample.objects.filter(
                    entryform=analysis.entryform
                ).values_list("id", flat=True)
                sampleExams = SampleExams.objects.filter(
                    sample__in=samples, exam=analysis.exam, stain=analysis.stain
                )
                organs_count = samples_count = len(sampleExams)
                exam_pools = Pool.objects.filter(identification__entryform=entryform_object, exams=analysis.exam)
                organs_count += len(exam_pools)
                if analysis.exam.pricing_unit == 1:
                    samples_count = organs_count
                else:
                    sampleExams = SampleExams.objects.filter(
                        sample__in=samples, exam=analysis.exam, stain=analysis.stain
                    ).values_list("sample_id", flat=True)
                    samples_count = len(list(set(sampleExams)))

                aux = {
                    "id": analysis.id,
                    "created_at": analysis.created_at,
                    "comments": analysis.comments,
                    "stain": analysis.stain.abbreviation.upper()
                    if analysis.stain
                    else "N/A",
                    "entryform_id": analysis.entryform_id,
                    "exam_id": analysis.exam_id,
                    "exam__name": analysis.exam.name,
                    "exam__stain_id": analysis.stain.id
                    if analysis.exam.stain
                    else None,
                    "patologo_id": analysis.patologo_id,
                    "patologo__first_name": analysis.patologo.first_name
                    if analysis.patologo
                    else None,
                    "patologo__last_name": analysis.patologo.last_name
                    if analysis.patologo
                    else None,
                    "service_comments": [],
                    "service_deadline": [],
                    "deadline_comments": [],
                    "status": analysis.status,
                    "samples_count": samples_count,
                    "organs_count": organs_count,
                    "samples_charged": analysis.samples_charged,
                    "pools":[],
                }

                for cmm in analysis.service_comments.all():
                    aux["service_comments"].append(
                        {
                            "text": cmm.text,
                            "created_at": cmm.created_at.strftime("%d/%m/%Y %H:%M:%S"),
                            "done_by": cmm.done_by.get_full_name(),
                        }
                    )

                if AnalysisTimes.objects.filter(analysis=analysis, type_deadline=1).last() != None:
                    laboratoryDeadline = AnalysisTimes.objects.filter(
                        analysis=analysis, type_deadline=1).last().deadline.__format__('%d-%m-%Y')
                    aux["service_deadline"].append({
                        "deadline": laboratoryDeadline,
                        "type": "Laboratorio"
                    })

                if AnalysisTimes.objects.filter(analysis=analysis, type_deadline=2).exists():
                    pathologistDeadline = AnalysisTimes.objects.filter(
                        analysis=analysis, type_deadline=2).last().deadline.__format__('%d-%m-%Y')
                    aux["service_deadline"].append({
                        "deadline": pathologistDeadline,
                        "type": "Patologo"
                    })

                if AnalysisTimes.objects.filter(analysis=analysis, type_deadline=3).exists():
                    reviewDeadline = AnalysisTimes.objects.filter(
                        analysis=analysis, type_deadline=3).last().deadline.__format__('%d-%m-%Y')
                    aux["service_deadline"].append({
                        "deadline": reviewDeadline,
                        "type": "Revision"
                    })

                comments = AnalysisTimes.objects.filter(analysis=analysis)
                comments_aux = []
                for comment in comments:
                    if comment.service_comments != None and comment.service_comments not in comments_aux:
                        comments_aux.append(comment.service_comments)
                        aux["deadline_comments"].append({
                            "text": comment.service_comments.text,
                            "created_at": comment.service_comments.created_at.strftime("%d/%m/%Y %H:%M:%S"),
                            "done_by": comment.service_comments.done_by.get_full_name(),
                        })

                entryform["analyses"].append(aux)

            entryform["customer"] = (
                model_to_dict(entryform_object.customer, exclude=['center'])
                if entryform_object.customer
                else None
            )
            entryform["company_index"] = (
                model_to_dict(entryform_object.company_index, exclude=['center'])
                if entryform_object.company_index
                else None
            )
            entryform["larvalstage"] = (
                model_to_dict(entryform_object.larvalstage)
                if entryform_object.larvalstage
                else None
            )
            entryform["fixative"] = (
                model_to_dict(entryform_object.fixative)
                if entryform_object.fixative
                else None
            )
            entryform["entryform_type"] = (
                model_to_dict(entryform_object.entryform_type)
                if entryform_object.entryform_type
                else None
            )
            entryform["watersource"] = (
                model_to_dict(entryform_object.watersource)
                if entryform_object.watersource
                else None
            )
            entryform["specie"] = (
                model_to_dict(entryform_object.specie)
                if entryform_object.specie
                else None
            )
            entryform["entry_format"] = (
                entryform_object.entry_format,
                entryform_object.get_entry_format_display(),
            )

            pools = Pool.objects.filter(identification__entryform=entryform_object)
            pools_list = []
            for pool in pools:
                exams=[]
                for exam in pool.exams.all():
                    exams.append({
                        "id":exam.id,
                        "name":exam.name
                    })

                pool_organs = []
                for organ in pool.organ_unit.all():
                    pool_organs.append({
                        "name":organ.organ.name,
                        "correlative":organ.unit.correlative,
                    })

                pools_list.append({
                    "id":pool.id,
                    "name":pool.name,
                    "identification":{
                        "cage":pool.identification.cage,
                        "group":pool.identification.group,
                        "extra_features_detail":pool.identification.extra_features_detail,
                    },
                    "exams":exams,
                    "organs":pool_organs,
                })

            entryform["pools"] = pools_list

            exams_set = list(Exam.objects.all().values())
            organs_set = list(Organ.objects.all().values())

            species_list = list(Specie.objects.all().values())
            larvalStages_list = list(LarvalStage.objects.all().values())
            fixtatives_list = list(Fixative.objects.all().values())
            waterSources_list = list(WaterSource.objects.all().exclude(id__range=(
                1, 13)).values() | WaterSource.objects.filter(id=9).values())
            customers_list = list(Customer.objects.all().values())
            patologos = list(
                User.objects.filter(
                    userprofile__profile_id__in=[4, 5]).values()
            )
            # entryform_types = list(EntryForm_Type.objects.all().values())
            if entryform_object.customer:
                researches = list(
                    Research.objects.filter(
                        status=True, clients__in=[entryform_object.customer]
                    ).values()
                )
            else:
                researches = []

            stains_list = list(Stain.objects.values())
            laboratories_list = list(Laboratory.objects.values())

            data = {
                "entryform": entryform,
                "identifications": identifications,
                "samples": samples_as_dict,
                "exams": exams_set,
                "organs": organs_set,
                "stains": stains_list,
                "species_list": species_list,
                "larvalStages_list": larvalStages_list,
                "fixtatives_list": fixtatives_list,
                "waterSources_list": waterSources_list,
                "customers_list": customers_list,
                "laboratories": laboratories_list,
                "patologos": patologos,
                # 'entryform_types_list': entryform_types,
                "research_types_list": researches,
            }
        else:
            # This case is when is creating a new entryform from the frontend. See init_step_1() in step-1.js
            species = list(Specie.objects.all().values())
            larvalStages = list(LarvalStage.objects.all().values())
            fixtatives = list(Fixative.objects.all().values())
            waterSources = list(WaterSource.objects.all().exclude(id__range=(
                1, 13)).values() | WaterSource.objects.filter(id=9).values())
            exams = list(Exam.objects.all().values())
            organs = list(Organ.objects.all().values())
            customers = list(Customer.objects.all().values())
            researches = list(Research.objects.filter(status=True).values())
            stains_list = list(Stain.objects.values())
            laboratories_list = list(Laboratory.objects.values())

            data = {
                "species": species,
                "larvalStages": larvalStages,
                "fixtatives": fixtatives,
                "waterSources": waterSources,
                "exams": exams,
                "organs": organs,
                "stains": stains_list,
                "customers": customers,
                "laboratories": laboratories_list,
                "research_types_list": researches,
            }
        return JsonResponse(data)


class ANALYSIS(View):
    def get(self, request, entry_form=None):
        analyses_qs = AnalysisForm.objects.filter(
            entryform=entry_form, exam__isnull=False
        )
        analyses = []

        analysis_with_zero_sample = []
        for analysis in analyses_qs:

            if request.user.userprofile.profile_id == 5:
                if analysis.patologo_id != request.user.id:
                    continue
            exam = analysis.exam
            try:
                form = analysis.forms.get()
            except Form.DoesNotExist:
                continue

            form_id = form.id

            current_step_tag = form.state.step.tag
            current_step = form.state.step.order
            total_step = form.flow.step_set.count()

            if exam.service_id == 2:
                total_step = 2
                percentage_step = (int(current_step) / int(total_step)) * 100
            elif exam.service_id in [3, 4, 5]:
                total_step = 0
                percentage_step = 0
            else:
                percentage_step = (int(current_step) / int(total_step)) * 100

            samples = Sample.objects.filter(entryform=analysis.entryform).values_list(
                "id", flat=True
            )
            sampleExams = SampleExams.objects.filter(
                sample__in=samples, exam=exam, stain=analysis.stain
            )
            organs_count = samples_count = len(sampleExams)
            if analysis.exam.pricing_unit == 1:
                samples_count = organs_count
            else:
                sampleExams = SampleExams.objects.filter(
                    sample__in=samples, exam=analysis.exam, stain=analysis.stain
                ).values_list("sample_id", flat=True)
                samples_count = len(list(set(sampleExams)))

            analysis_pool = Pool.objects.filter(identification__entryform=analysis.entryform, exams=analysis.exam)
            samples_count += len(analysis_pool)

            slices = []
            if not form.cancelled and not form.form_closed:
                analysis_with_zero_sample.append(
                    False if samples_count > 0 else True)

            analyses.append(
                {
                    "form_id": form_id,
                    "id": analysis.id,
                    "exam_name": exam.name,
                    "exam_stain": analysis.stain.abbreviation.upper()
                    if analysis.stain
                    else "N/A",
                    "exam_type": exam.service_id,
                    "exam_pathologists_assignment": exam.pathologists_assignment,
                    "exam_chargeable": exam.chargeable,
                    "has_portal": exam.subclass == "HE" or exam.name == "SCORE_GILL" or exam.name == "GENERAL_SCORE",
                    "slices": slices,
                    "current_step_tag": current_step_tag,
                    "current_step": current_step,
                    "total_step": total_step,
                    "percentage_step": percentage_step,
                    "form_closed": form.form_closed,
                    "form_reopened": form.form_reopened,
                    "service": exam.service_id,
                    "service_name": exam.service.name,
                    "cancelled": form.cancelled,
                    "patologo_name": analysis.patologo.get_full_name()
                    if analysis.patologo
                    else "",
                    "patologo_id": analysis.patologo.id if analysis.patologo else "",
                    "pre_report_started": analysis.pre_report_started,
                    "pre_report_ended": analysis.pre_report_ended,
                    "status": analysis.status,
                    "cancelled_by": analysis.manual_cancelled_by.get_full_name()
                    if analysis.manual_cancelled_by
                    else "",
                    "cancelled_at": analysis.manual_cancelled_date.strftime("%d/%m/%Y")
                    if analysis.manual_cancelled_date
                    else "",
                    "samples_count": samples_count,
                    "report_code": analysis.report_code,
                    "on_hold": analysis.on_hold,
                    "on_standby": analysis.on_standby,
                    "samples_charged": analysis.samples_charged
                }
            )

        entryform = EntryForm.objects.values().get(pk=entry_form)
        entryform_object = EntryForm.objects.get(pk=entry_form)
        subflow = entryform_object.get_subflow
        entryform["subflow"] = subflow

        entryform["identifications"] = []
        for ident in entryform_object.identification_set.all():
            ident_json = model_to_dict(
                ident, exclude=["organs", "organs_before_validations"]
            )
            ident_json["organs_set"] = list(ident.organs.all().values())
            entryform["identifications"].append(ident_json)

        entryform["analyses"] = list(
            entryform_object.analysisform_set.all().values(
                "id",
                "created_at",
                "comments",
                "entryform_id",
                "exam_id",
                "exam__name",
                "patologo_id",
                "patologo__first_name",
                "patologo__last_name",
            )
        )
        entryform["cassettes"] = []
        entryform["customer"] = (
            model_to_dict(entryform_object.customer, exclude=['center'])
            if entryform_object.customer
            else None
        )
        entryform["larvalstage"] = (
            model_to_dict(entryform_object.larvalstage)
            if entryform_object.larvalstage
            else None
        )
        entryform["fixative"] = (
            model_to_dict(entryform_object.fixative)
            if entryform_object.fixative
            else None
        )
        entryform["watersource"] = (
            model_to_dict(entryform_object.watersource)
            if entryform_object.watersource
            else None
        )
        entryform["specie"] = (
            model_to_dict(
                entryform_object.specie) if entryform_object.specie else None
        )

        organs_set = list(Organ.objects.all().values())
        exams_set = list(Exam.objects.all().values())

        species_list = list(Specie.objects.all().values())
        larvalStages_list = list(LarvalStage.objects.all().values())
        fixtatives_list = list(Fixative.objects.all().values())
        waterSources_list = list(WaterSource.objects.all().values())
        customers_list = list(Customer.objects.all().values())
        patologos = list(
            User.objects.filter(userprofile__profile_id__in=[4,5]).values()
        )
        # entryform_types = list(EntryForm_Type.objects.all().values())
        if entryform_object.customer:
            researches = list(
                Research.objects.filter(
                    status=True, clients__in=[entryform_object.customer]
                ).values()
            )
        else:
            researches = []

        data = {
            "analyses": analyses,
            "entryform": entryform,
            "exams_set": exams_set,
            "organs": organs_set,
            "species_list": species_list,
            "larvalStages_list": larvalStages_list,
            "fixtatives_list": fixtatives_list,
            "waterSources_list": waterSources_list,
            "customers_list": customers_list,
            "patologos": patologos,
            # 'entryform_types_list': entryform_types,
            "research_types_list": researches,
            "analysis_with_zero_sample": 1 if True in analysis_with_zero_sample else 0,
        }

        return JsonResponse(data)

    def put(self, request, pk):
        analysis = get_object_or_404(AnalysisForm, pk=pk)

        form = json.loads(request.body)
        analysis.samples_charged = form["value"]
        analysis.save()

        return JsonResponse({"status": "OK"})


class WORKFLOW(View):
    http_method_names = ["get", "post", "delete"]

    def sortReport(self, report):
        return report.organ_id

    @method_decorator(login_required)
    def get(self, request, form_id, step_tag=None):
        form = Form.objects.get(pk=form_id)
        if not step_tag:
            step_tag = form.state.step.tag
        object_form_id = form.content_object.id
        actor = Actor.objects.filter(
            profile_id=request.user.userprofile.profile_id
        ).first()
        if form.content_type.name == "entry form":
            state_id = step_tag.split("_")[1]
            permisos = actor.permission.filter(from_state_id=state_id)
            edit = 1 if permisos.filter(type_permission="w").first() else 0
            route = "app/workflow_main.html"

            close_allowed = 1
            closed = 0
            if form.form_closed or form.cancelled:
                close_allowed = 0
                closed = 1
            else:
                childrens = Form.objects.filter(parent_id=form)
                for ch in childrens:
                    if not ch.form_closed and not ch.cancelled:
                        close_allowed = 0
                        break

            up = UserProfile.objects.filter(user=request.user).first()
            edit_case = not form.form_closed and (
                up.profile.id in (1, 2, 3) or request.user.is_superuser
            )

            data = {
                "form": form,
                "form_id": form_id,
                "entryform_id": object_form_id,
                "set_step_tag": step_tag,
                "edit": edit,
                "closed": closed,
                "close_allowed": close_allowed,
                "edit_case": edit_case,
                "reception_finished": form.reception_finished,
            }

        return render(request, route, data)

    def post(self, request):

        var_post = request.POST.copy()

        up = UserProfile.objects.filter(user=request.user).first()
        form = Form.objects.get(pk=var_post.get("form_id"))

        form_closed = False

        if var_post.get("form_closed"):
            form_closed = True

        id_next_step = var_post.get("id_next_step", None)
        previous_step = strtobool(var_post.get("previous_step", "false"))
               
        if not id_next_step:
            form_closed = True
        

        if not form_closed:
            next_step_permission = False
            process_response = False
            process_answer = True

            actor_user = None
            next_state = None

            if id_next_step:
                next_step = Step.objects.get(pk=id_next_step)

                for actor in next_step.actors.all():
                    if actor.profile == up.profile:
                        actor_user = actor
                        if previous_step:
                            next_state = Permission.objects.get(
                                to_state=form.state, type_permission="w"
                            ).from_state
                        else:
                            next_state = actor.permission.get(
                                from_state=form.state, type_permission="w"
                            ).to_state
                        break
            if not previous_step:
                process_answer = call_process_method(
                    form.content_type.model, request)
                if next_state:
                    next_step_permission = next_state.id != 1 and not len(
                        actor_user.permission.filter(
                            to_state=next_state, type_permission="w"
                        )
                    )
            else:
                if next_state:
                    next_step_permission = next_state.id != 1 and not len(
                        actor_user.permission.filter(
                            from_state=next_state, type_permission="w"
                        )
                    )
                    form.form_reopened = False

            if process_answer and next_state:
                current_state = form.state
                form.state = next_state
                form.save()
                if next_step_permission:
                    return redirect(app_view.show_ingresos)
                next_step_permission = not next_step_permission
                process_response = True
                # sendEmailNotification(form, current_state, next_state)
            else:
                return redirect(app_view.show_ingresos)

            return JsonResponse(
                {
                    "process_response": process_response,
                    "next_step_permission": next_step_permission,
                }
            )

        else:
            process_answer = call_process_method(
                form.content_type.model, request)

            form.form_closed = False

            form.form_reopened = False
            form.save()

            return JsonResponse({"redirect_flow": True})

    def delete(self, request, form_id):
        form = Form.objects.get(pk=form_id)
        form.cancelled = True
        form.cancelled_at = datetime.now()
        form.save()
        forms = Form.objects.filter(
            parent_id=form_id, form_closed=False, cancelled=False
        )
        for f in forms:
            f.cancelled = True
            f.cancelled_at = datetime.now()
            f.save()
        # object_form_id = form.content_object.id
        return JsonResponse({"ok": True})


class RESPONSIBLE(View):
    http_method_names = ["get", "post", "delete"]

    def get(self, request):
        responsibles = Responsible.objects.filter(active=True)
        data = []
        for r in responsibles:
            data.append(model_to_dict(r))

        return JsonResponse({"ok": True, "responsibles": data})

    def post(self, request):
        try:
            var_post = request.POST.copy()
            responsible = Responsible()
            id = var_post.get("id", None)
            if id:
                responsible.id = id
            responsible.name = var_post.get("name", None)
            email_str = var_post.get("email", None)
            responsible.phone = var_post.get("phone", None)
            responsible.job = var_post.get("job", None)
            responsible.active = var_post.get("active", True)
            if email_str:
                responsible.email = email_str.strip().replace(" ", "")
            responsible.save()

            return JsonResponse({"ok": True})
        except Exception as e:
            return JsonResponse({"ok": False})

    def delete(self, request, id):
        responsible = Responsible.objects.get(pk=id)
        responsible.active = False
        responsible.save()

        return JsonResponse({"ok": True})


class SERVICE_REPORTS(View):
    http_method_names = ["get", "post", "delete"]

    def get(self, request, analysis_id):
        af = AnalysisForm.objects.get(pk=analysis_id)

        data = []
        for report in af.external_reports.all().order_by("-created_at"):
            data.append(
                {
                    "final_report": False,
                    "id": report.id,
                    "path": report.file.url,
                    "name": report.file.name.split("/")[-1],
                }
            )

        if af.final_reports.all():
            final_report = af.final_reports.all().order_by("-created_at").last()
            data.append(
                {
                    "final_report": True,
                    "id": final_report.id,
                    "path": final_report.path.url,
                    "name": final_report.path.name.split("/")[-1],
                }
            )
        else:
            try:
                final_report = FinalReport.objects.get(
                    grouper__analysisgrouper__analysis=af)
                data.append(
                    {
                        "final_report": True,
                        "id": final_report.id,
                        "path": final_report.path.url,
                        "name": final_report.path.name.split("/")[-1],
                    }
                )
            except FinalReport.DoesNotExist:
                final_report = ""

        return JsonResponse({"ok": True, "reports": data})

    def post(self, request, analysis_id):
        try:
            if analysis_id:
                af = AnalysisForm.objects.get(pk=analysis_id)
                file_report = request.FILES["file"]
                external_report = ExternalReport.objects.create(
                    file=file_report, loaded_by=request.user
                )
                af.external_reports.add(external_report)
                return JsonResponse(
                    {
                        "ok": True,
                        "file": {
                            "id": external_report.id,
                            "path": external_report.file.url,
                            "name": external_report.file.name.split("/")[-1],
                        },
                    }
                )
            else:
                return JsonResponse({"ok": False})
        except:
            return JsonResponse({"ok": False})

    def delete(self, request, analysis_id, id):
        try:
            report = ExternalReport.objects.get(pk=id)
            af = AnalysisForm.objects.get(pk=analysis_id)
            af.external_reports.remove(report)
            return JsonResponse({"ok": True})
        except:
            return JsonResponse({"ok": False})


class SERVICE_COMMENTS(View):
    http_method_names = ["get", "post", "delete"]

    def get(self, request, analysis_id):
        af = AnalysisForm.objects.get(pk=analysis_id)

        data = []
        for cmm in af.service_comments.all().order_by("-created_at"):
            response = {
                "id": cmm.id,
                "text": cmm.text,
                "created_at": cmm.created_at.strftime("%d/%m/%Y %H:%M:%S"),
                "done_by": cmm.done_by.get_full_name(),
            }
            data.append(response)

        return JsonResponse({"ok": True, "comments": data})

    def post(self, request, analysis_id):
        try:
            if analysis_id:
                af = AnalysisForm.objects.get(pk=analysis_id)
                var_post = request.POST.copy()
                comment = var_post.get("comment", None)
                if comment:
                    service_comment = ServiceComment.objects.create(
                        text=comment, done_by=request.user
                    )
                    af.service_comments.add(service_comment)
                    response = {
                        "id": service_comment.id,
                        "text": service_comment.text,
                        "created_at": service_comment.created_at.strftime(
                            "%d/%m/%Y %H:%M:%S"
                        ),
                        "done_by": service_comment.done_by.get_full_name(),
                    }
                    return JsonResponse({"ok": True, "comment": response})
                else:
                    return JsonResponse({"ok": True})
            else:
                return JsonResponse({"ok": False})
        except:
            return JsonResponse({"ok": False})

    def delete(self, request, analysis_id, id):
        try:
            sc = ServiceComment.objects.get(pk=id)
            af = AnalysisForm.objects.get(pk=analysis_id)
            af.service_comments.remove(sc)
            return JsonResponse({"ok": True})
        except:
            return JsonResponse({"ok": False})


class SERVICE_RESEARCHES(View):
    http_method_names = ["get", "post", "delete"]

    def get(self, request, analysis_id):
        af = AnalysisForm.objects.get(pk=analysis_id)

        data = []
        for rs in Research.objects.filter(services__in=[af]).distinct():
            response = {
                "id": rs.id,
                "code": rs.code,
                "name": rs.name,
                "description": rs.description,
                "status": rs.status,
            }
            data.append(response)

        return JsonResponse({"ok": True, "researches": data})

    def post(self, request, analysis_id):
        try:
            if analysis_id:
                af = AnalysisForm.objects.get(pk=analysis_id)
                var_post = request.POST.copy()
                researches = var_post.getlist("researches[]")
                # af.researches.clear()
                for r in Research.objects.all():
                    if r.services.filter(id=af.id).count():
                        r.services.remove(af)
                        r.save()
                for r in Research.objects.filter(id__in=researches):
                    r.services.add(af)
                    r.save()

                return JsonResponse({"ok": True})

            else:
                return JsonResponse({"ok": False})
        except:
            return JsonResponse({"ok": False})

    def delete(self, request, analysis_id, id):
        try:
            rs = Research.objects.get(pk=id)
            af = AnalysisForm.objects.get(pk=analysis_id)
            af.researches.remove(rs)
            return JsonResponse({"ok": True})
        except:
            return JsonResponse({"ok": False})


class EMAILTEMPLATE(View):
    def get(self, request, id=None):
        if id:
            template = EmailTemplate.objects.get(pk=id)
            data = model_to_dict(template, exclude=["cc"])
            return JsonResponse({"ok": True, "template": data})
        else:
            var_get = request.GET.copy()
            entryform = EntryForm.objects.get(pk=var_get["form"])
            responsible = Responsible.objects.filter(
                name=entryform.responsible, active=True
            ).first()
            email = ""
            if responsible:
                email = responsible.email
            templates = EmailTemplate.objects.all()
            data = []
            for r in templates:
                data.append(model_to_dict(r, exclude=["cc"]))

            return JsonResponse({"ok": True, "templates": data, "email": email})

    def post(self, request):
        try:
            var_post = request.POST.copy()
            from app import views as appv

            lang = var_post.get("lang", "es")
            formId = var_post.get("formId")
            doc = appv.get_resume_file(request.user, formId, lang)
            center = doc.entryform.center if doc.entryform.center else ""
            subject = "Recepción de muestras/" + doc.entryform.no_caso + "/" + center
            from_email = settings.EMAIL_HOST_USER
            to = var_post.get("to").split(",")
            message = var_post.get("body")
            plantilla = var_post.get("plantilla")
            bcc = []
            if plantilla:
                emailtemplate = EmailTemplate.objects.get(pk=plantilla)
                for cc in emailtemplate.cc.all():
                    bcc.append(cc.email)
            msg = EmailMultiAlternatives(
                subject, message, from_email, to, bcc=bcc)

            if settings.DEBUG:
                file_path = settings.BASE_DIR + settings.MEDIA_URL + "pdfs/"
            else:
                file_path = settings.MEDIA_ROOT + "/pdfs/"

            with open(file_path + "" + str(doc.file), "rb") as pdf:
                msg.attach(doc.filename, pdf.read(), "application/pdf")

            msg.send()

            DocumentResumeActionLog.objects.create(
                document=doc, mail_action=True, done_by=request.user
            )
            return JsonResponse({"ok": True})
        except Exception as e:
            print(e)
            return JsonResponse({"ok": False})


class CASE_FILES(View):
    http_method_names = ["get", "post", "delete"]

    def get(self, request, entryform_id):
        ef = EntryForm.objects.get(pk=entryform_id)

        caseFilesIdsOutsources = OutsourceAttachedFiles.objects.select_related('attachedFiles').filter(attachedFiles__entryform_id=entryform_id).distinct().values_list('attachedFiles__caseFile_id', flat=True)
        
        data = []
        outsources = []
        for file in ef.attached_files.all().order_by("-created_at"):
            
            if file.id in caseFilesIdsOutsources:
                outsources.append(
                    {
                        "id": file.id,
                        "path": file.file.url,
                        "name": file.file.name.split("/")[-1],
                    }
                )
            else:
                data.append(
                    {
                        "id": file.id,
                        "path": file.file.url,
                        "name": file.file.name.split("/")[-1],
                    }
                )

        return JsonResponse({"ok": True, "files": data, "outsourcesFiles": outsources})

    def post(self, request, entryform_id):
        try:
            if entryform_id:
                ef = EntryForm.objects.get(pk=entryform_id)
                file = request.FILES["file"]
                case_file = CaseFile.objects.create(
                    file=file, loaded_by=request.user)
                ef.attached_files.add(case_file)
                return JsonResponse(
                    {
                        "ok": True,
                        "file": {
                            "id": case_file.id,
                            "path": case_file.file.url,
                            "name": case_file.file.name.split("/")[-1],
                        },
                    }
                )
            else:
                return JsonResponse({"ok": False})
        except:
            return JsonResponse({"ok": False})

    def delete(self, request, entryform_id, id):
        try:
            file = CaseFile.objects.get(pk=id)
            ef = EntryForm.objects.get(pk=entryform_id)
            ef.attached_files.remove(file)
            return JsonResponse({"ok": True})
        except:
            return JsonResponse({"ok": False})


class RESEARCH(View):
    http_method_names = ["get", "post", "delete"]

    @method_decorator(cache_page(90)) # Cache for 90 seconds
    def get(self, request, id):
        research = Research.objects.get(pk=id)

        up = UserProfile.objects.filter(user=request.user).first()

        research_analysis = research.services.all()

        fecha_actual = date.today()

        # Fecha de inicio que deseas filtrar
        fecha_inicio = date(2021, 1, 1)  # Reemplaza esta fecha con la que desees
        analysis = (
            AnalysisForm.objects.filter(
                exam__isnull=False, entryform__customer__in=research.clients.all(), created_at__range=(fecha_inicio, fecha_actual)
            )
            .exclude(id__in=research_analysis)
            .prefetch_related('forms', 'exam', 'entryform', 'entryform__forms', 'entryform__customer')
            .order_by("-entryform_id")
        )
  
        data1 = []
        data2 = []
        
        available_analysis = []
        for a in analysis:
            entryform_form = list(a.entryform.forms.all())[0]
            analysisform_form = list(a.forms.all())[0]
            
            if not entryform_form.cancelled and not analysisform_form.cancelled:
                available_analysis.append(
                    {
                        "analysis": a,
                        "entryform_form": entryform_form,
                        "analysisform_form": analysisform_form,
                    }
                )
                
        for a in available_analysis:
            parte = a["analysis"].entryform.get_subflow
            
            if parte == "N/A":
                parte = ""
            else:
                parte = " (Parte " + parte + ")"
            data1.append(
                {
                    "analisis": a["analysis"].id,
                    "no_caso": a["analysis"].entryform.no_caso + parte,
                    "exam": a["analysis"].exam.name,
                    "centro": a["analysis"].entryform.center,
                    "cliente": a["analysis"].entryform.customer.name,
                    "fecha_ingreso": a["analysis"].created_at.strftime("%d/%m/%Y"),
                    "fecha_muestreo": a["analysis"].entryform.sampled_at.strftime(
                        "%d/%m/%Y"
                    )
                    if a["analysis"].entryform.sampled_at
                    else "",
                    "f_m_year": a["analysis"].entryform.sampled_at.strftime("%Y")
                    if a["analysis"].entryform.sampled_at
                    else "",
                    "f_m_month": a["analysis"].entryform.sampled_at.strftime("%m")
                    if a["analysis"].entryform.sampled_at
                    else "",
                    "entryform": a["analysis"].entryform.id,
                    "estado": a["analysis"].status,
                    "edit_case": not a["entryform_form"].form_closed
                    and (up.profile.id in (1, 2, 3) or request.user.is_superuser),
                    "case_closed": a["entryform_form"].form_closed
                    or a["entryform_form"].cancelled,
                }
            )
            
        for a in research_analysis:
            parte = a.entryform.get_subflow
            if parte == "N/A":
                parte = ""
            else:
                parte = " (Parte " + parte + ")"

            data2.append(
                {
                    "analisis": a.id,
                    "no_caso": a.entryform.no_caso + parte,
                    "exam": a.exam.name,
                    "centro": a.entryform.company_center.center.name if a.entryform.company_center != None else ( a.entryform.company_laboratory if a.entryform.company_laboratory != None else ""),
                    "cliente": a.entryform.customer.name,
                    "fecha_ingreso": a.created_at.strftime("%d/%m/%Y"),
                    "fecha_muestreo": a.entryform.sampled_at.strftime("%d/%m/%Y")
                    if a.entryform.sampled_at
                    else "",
                    "f_m_year": a.entryform.sampled_at.strftime("%Y")
                    if a.entryform.sampled_at
                    else "",
                    "f_m_month": a.entryform.sampled_at.strftime("%m")
                    if a.entryform.sampled_at
                    else "",
                    "entryform": a.entryform.id,
                    "estado": a.status,
                    "edit_case": not a.entryform.forms.get().form_closed
                    and (up.profile.id in (1, 2, 3) or request.user.is_superuser),
                    "case_closed": a.entryform.forms.get().form_closed
                    or a.entryform.forms.get().cancelled,
                }
            )

        clients_available = Customer.objects.all()
        users_available = User.objects.all()

        return render(
            request,
            "app/research.html",
            {
                "research": research,
                "casos1": data1,
                "casos2": data2,
                "analysis_selected": [RA.id for RA in research_analysis],
                "clients_available": clients_available,
                "users_available": users_available,
            },
        )

    def post(self, request, id):
        try:
            var_post = request.POST.copy()
            research = Research.objects.get(pk=id)
            analisis = var_post.getlist("analisis[]", [])
            research.services.clear()
            for af in AnalysisForm.objects.filter(id__in=analisis):
                research.services.add(af)
            research.save()

            return JsonResponse({"ok": True})
        except Exception as e:
            return JsonResponse({"ok": False})

    def delete(self, request, id):
        responsible = Responsible.objects.get(pk=id)
        responsible.active = False
        responsible.save()

        return JsonResponse({"ok": True})


def save_block_timing(request):
    try:
        var_post = request.POST.copy()

        block_cassette_pk = [
            v for k, v in var_post.items() if k.startswith("block_cassette_pk")
        ]

        block_start_block = [
            v for k, v in var_post.items() if k.startswith("block_start_block")
        ]

        block_end_block = [
            v for k, v in var_post.items() if k.startswith("block_end_block")
        ]

        block_start_slice = [
            v for k, v in var_post.items() if k.startswith("block_start_slice")
        ]

        block_end_slice = [
            v for k, v in var_post.items() if k.startswith("block_end_slice")
        ]

        zip_block = zip(
            block_cassette_pk,
            block_start_block,
            block_end_block,
            block_start_slice,
            block_end_slice,
        )


        return JsonResponse({"ok": True})
    except:
        return JsonResponse({"ok": False})


def checkSampleExams(olds, news):
    if len(olds) != len(news):
        return True
    for s in news:
        if not olds.filter(
            sample_id=s.sample_id, exam_id=s.exam_id, organ_id=s.organ_id
        ).first():
            return True
    return False


def changeCaseVersion(allow_new, form_id, user_id):
    versions = CaseVersion.objects.filter(entryform_id=form_id)
    if len(versions) or allow_new:
        CaseVersion.objects.create(
            entryform_id=form_id, version=len(versions) + 1, generated_by_id=user_id
        )


# Generic function for call any process method for any model_form
def call_process_method(model_name, request):
    method_name = "process_" + str(model_name)
    possibles = globals().copy()
    possibles.update(locals())
    method = possibles.get(method_name)
    if not method:
        raise NotImplementedError("Method %s not implemented" % method_name)
    return method(request)

# This method is called by call_precess_method. Before there was another method also called process_analysisform. But given its uselessness it was deleted. Maybe that's why call_oricessmethod existed. Bad practice.
def process_entryform(request):
    step_tag = request.POST.get("step_tag")

    # try:
    switcher = {
        "step_1": step_1_entryform,
        "step_2": step_2_entryform,
        "step_3": step_3_entryform,
        "step_4": step_4_entryform,
        "step_3_new": step_new_analysis,
        "step_4_new": step_new_analysis2,
    }

    method = switcher.get(step_tag)

    if not method:
        raise NotImplementedError(
            "Method %s_entryform not implemented" % step_tag)

    return method(request)

# Steps Function for entry forms. This methods depends of process_entryform
def step_1_entryform(request):
    var_post = request.POST.copy()

    entryform = EntryForm.objects.get(pk=var_post.get("entryform_id"))

    entryform.analysisform_set.all().delete()
    Sample.objects.filter(entryform=entryform).delete()

    entryform.specie_id = var_post.get("specie")
    entryform.watersource_id = var_post.get("watersource")
    entryform.fixative_id = var_post.get("fixative")
    entryform.laboratory_id = var_post.get("laboratory")
    entryform.larvalstage_id = var_post.get("larvalstage")
    entryform.customer_id = var_post.get("customer")
    
    entryform.entryform_type_id = var_post.get("entryform_type")
    entryform.no_order = var_post.get("no_order")

    try:
        entryform.created_at = datetime.strptime(var_post.get("created_at"), "%d/%m/%Y %H:%M")
    except:
        pass
    try:
        entryform.sampled_at = datetime.strptime(var_post.get("sampled_at"), "%d/%m/%Y")
    except:
        pass
    entryform.sampled_at_hour = var_post.get("sampled_at_hour")
    entryform.sampled_at_am_pm = var_post.get("sampled_at_am_pm")

    entryform.entry_format = var_post.get("entry_format")
    entryform.transfer_order = var_post.get("transfer_order")
    entryform.responsible = var_post.get("responsible")
    entryform.no_request = var_post.get("no_request")
    entryform.anamnesis = var_post.get("anamnesis")
    
    if var_post.get("company_index") != "" and var_post.get("company_index") != None:
        entryform.company_index_id = var_post.get("company_index")
    else:
        entryform.company_index_id = None 
    
    if var_post.get("company_center") != "" and var_post.get("company_center") != None:
        entryform.company_center_id = var_post.get("company_center")
    elif len(str(var_post.get("company_laboratory")).split(' ')) > 0:
        entryform.company_laboratory = str(var_post.get("company_laboratory")).upper()
    

    entryform.save()

    return True

def step_2_entryform(request):
    var_post = request.POST.copy()
    entryform = EntryForm.objects.get(pk=var_post.get("entryform_id"))
    sample_correction = []

    index = 1

    # Processing correlative idents

    correlative_idents = Identification.objects.filter(
        entryform=entryform, samples_are_correlative=True
    ).order_by("id")

    for ident in correlative_idents:

        units = Unit.objects.filter(identification=ident).order_by("pk")

        unit_by_correlative = {}
        for unit in units:
            if unit.correlative in unit_by_correlative.keys():
                unit_by_correlative[unit.correlative].append(unit)
            else:
                unit_by_correlative[unit.correlative] = [unit]

        for k, v in unit_by_correlative.items():

            sample = Sample.objects.filter(
                entryform=entryform, index=index, identification=ident
            ).first()

            if not sample:
                sample = Sample.objects.create(
                    entryform=entryform, index=index, identification=ident
                )

            sample.save()
            sample_correction.append(sample)

            # Cleaning sample's unit organs not setted
            to_remove = []
            for ou in sample.unit_organs.all():
                if ou.pk not in list(map(lambda x: x.pk, v)):
                    to_remove.append(ou)

            for ou in to_remove:
                sample.unit_organs.remove(ou)

            # Adding new unit organs to sample
            for ou in OrganUnit.objects.filter(unit__in=map(lambda x: x.pk, v)):
                if ou.pk not in sample.unit_organs.all().values_list("pk", flat=True):
                    sample.unit_organs.add(ou)

            index += 1

    # Processing non-correlative idents

    non_correlative_idents = Identification.objects.filter(
        entryform=entryform, samples_are_correlative=False
    ).order_by("id")

    for ident in non_correlative_idents:
        units = Unit.objects.filter(
            identification=ident).order_by("correlative")
        organs_units = {}
        for unit in units:
            for uo in OrganUnit.objects.filter(unit=unit).order_by("id"):
                if uo.organ.pk in organs_units:
                    organs_units[uo.organ.pk].append(uo)
                else:
                    organs_units[uo.organ.pk] = [uo]

        larger_organs_set = []
        for key, value in organs_units.items():
            if len(value) > len(larger_organs_set):
                larger_organs_set = value

        groups = []

        for organ in larger_organs_set:
            groups.append([organ])

        for unit in units:
            used_organ = False

            for ou_available in OrganUnit.objects.filter(unit=unit).order_by("id"):
                ou_is_used = False
                for group in groups:
                    organs_ids_in_group = list(
                        map(lambda ou: ou.organ.pk, group))
                    if ou_available.organ.pk not in organs_ids_in_group:
                        group.append(ou_available)
                        ou_is_used = True
                        break

        for group in groups:

            index_sample = Sample.objects.filter(
                entryform=entryform,
                index=index,
            ).first()

            nexts_samples = Sample.objects.filter(
                entryform=entryform,
                index__gt=index,
            ).order_by("index")

            if index_sample and len(nexts_samples) > 0:

                if index_sample.identification != ident:
                    new_sample = Sample.objects.create(
                        entryform=entryform, index=index, identification=ident
                    )
                    index_sample.index = int(index_sample.index) + 1
                    index_sample.save()

                    for ns in nexts_samples:
                        ns.index = int(ns.index) + 1
                        ns.save()
                else:
                    diff = nexts_samples[0].index - index
                    if diff > 1:
                        for ns in nexts_samples:
                            ns.index = int(ns.index) - (diff - 1)
                            ns.save()

            elif not index_sample and len(nexts_samples) > 0:
                diff = nexts_samples[0].index - index

                if nexts_samples[0].identification != ident:
                    new_sample = Sample.objects.create(
                        entryform=entryform, index=index, identification=ident
                    )

                    if diff > 1:
                        for ns in nexts_samples:
                            ns.index = int(ns.index) - (diff - 1)
                            ns.save()
                else:
                    for ns in nexts_samples:
                        ns.index = int(ns.index) - diff
                        ns.save()

            elif not index_sample and len(nexts_samples) == 0:
                new_sample = Sample.objects.create(
                    entryform=entryform, index=index, identification=ident
                )

            sample = Sample.objects.filter(
                entryform=entryform, index=index, identification=ident
            ).first()
            sample_correction.append(sample)

            # Cleaning sample's unit organs not setted
            to_remove = []
            if sample:
                for ou in sample.unit_organs.all():
                    if ou.id not in list(map(lambda x: x.id, group)):
                        to_remove.append(ou)

                for ou in to_remove:
                    sample.unit_organs.remove(ou)
                    # SampleExams.objects.filter(sample=sample, unit_organ=ou).delete()

                # Adding new unit organs to sample
                for ou in group:
                    if ou.pk not in sample.unit_organs.all().values_list(
                        "pk", flat=True
                    ):
                        sample.unit_organs.add(ou)

            index += 1

    # Cleanning samples error

    sample_compare = Sample.objects.filter(entryform=entryform)
    sample_to_remove = []
    for sp in sample_compare:
        sample_list = list(map(lambda x: x.id, sample_correction))
        if sp.id not in sample_list:
            sample_to_remove.append(sp.id)

    for ou in sample_to_remove:
        Sample.objects.filter(id=ou).delete()

    return True

def step_3_entryform(request):
    var_post = request.POST.copy()
    entryform = EntryForm.objects.get(pk=var_post.get("entryform_id"))
    change = False
    sample_id = [v for k, v in var_post.items() if k.startswith("sample[id]")]

    general_exam_stains = {}

    for samp in sample_id:
        sample = Sample.objects.get(pk=int(samp))

        sample_exams = [
            v[0]
            for k, v in dict(var_post).items()
            if k.startswith("sample[exams][" + samp)
        ]
        sample_stains = [
            v[0]
            for k, v in dict(var_post).items()
            if k.startswith("sample[stain][" + samp)
        ]

        sample_exams_stains = list(zip(sample_exams, sample_stains))

        sample_organs = []
        bulk_data = []

        for se in SampleExams.objects.filter(sample=sample):
            exists = False
            for elem in sample_exams_stains:
                exams_stain = list(elem)
                if se.exam_id == int(exams_stain[0]) and se.stain_id == int(
                    exams_stain[1]
                ):
                    exists = True
                    break
            if not exists:
                se.delete()

        for exam_stain in sample_exams_stains:
            if exam_stain[0] in general_exam_stains.keys():
                general_exam_stains[exam_stain[0]].append(exam_stain[1])
            else:
                general_exam_stains[exam_stain[0]] = [exam_stain[1]]

            sample_organs = [
                v
                for k, v in dict(var_post).items()
                if k.startswith(
                    "sample[organs]["
                    + samp
                    + "]["
                    + exam_stain[0]
                    + "]["
                    + exam_stain[1]
                    + "]"
                )
            ]

            for se in SampleExams.objects.filter(
                sample=sample, exam_id=exam_stain[0], stain_id=exam_stain[1]
            ):
                if se.unit_organ_id is not None:
                    if (
                        str(se.organ_id) + "-" + str(se.organ_id)
                        not in sample_organs[0]
                    ):
                        se.delete()

            unit_organ_dict = {}
            for uo in sample.unit_organs.all():
                unit_organ_dict[uo.organ.id] = uo.id

            if len(sample_organs) > 0:
                for organ in sample_organs[0]:
                    uo_organ_id = organ.split("-")[0]
                    organ_id = organ.split("-")[1]
                    uo_id = unit_organ_dict[int(uo_organ_id)]

                    if (
                        SampleExams.objects.filter(
                            sample=sample,
                            exam_id=exam_stain[0],
                            stain_id=exam_stain[1],
                            organ_id=organ_id,
                            unit_organ_id=uo_id,
                        ).count()
                        == 0
                    ):
                        bulk_data.append(
                            SampleExams(
                                sample_id=sample.pk,
                                exam_id=exam_stain[0],
                                organ_id=organ_id,
                                unit_organ_id=uo_id,
                                stain_id=exam_stain[1],
                            )
                        )

        change = change or checkSampleExams(
            sample.sampleexams_set.all(), bulk_data)
        SampleExams.objects.bulk_create(bulk_data)
        sample.save()

    services = []
    for key, value in general_exam_stains.items():
        for item in value:
            services.append((key, item))

    for a, b in services:
        ex = Exam.objects.get(pk=a)

        if ex.service_id in [1, 3, 4, 5]:
            flow = Flow.objects.get(pk=2)
        else:
            flow = Flow.objects.get(pk=3)

        AFS = AnalysisForm.objects.filter(
            entryform_id=entryform.id, exam=ex, stain_id=b
        )
        if AFS.count() == 0:
            analysis_form = AnalysisForm.objects.create(
                entryform_id=entryform.id, exam=ex, stain_id=b
            )

            user = request.user

            count_days = 0
            date = analysis_form.created_at
            if analysis_form.exam.laboratory_deadline != None:
                while count_days < analysis_form.exam.laboratory_deadline:
                    date = date+timedelta(1)
                    if date.weekday() < 5:
                        count_days = count_days+1
                AnalysisTimes.objects.create(analysis=analysis_form, exam=analysis_form.exam, deadline=date.date(
                ), changeDeadline=False, type_deadline_id=1, created_by=user, service_comments=None)

            count_days = 0
            if analysis_form.exam.pathologist_deadline != None:
                while count_days < analysis_form.exam.pathologist_deadline:
                    date = date+timedelta(1)
                    if date.weekday() < 5:
                        count_days = count_days+1
                AnalysisTimes.objects.create(analysis=analysis_form, exam=analysis_form.exam, deadline=date.date(
                ), changeDeadline=False, type_deadline_id=2, created_by=user, service_comments=None)

            count_days = 0
            if analysis_form.exam.review_deadline != None:
                while count_days < analysis_form.exam.review_deadline:
                    date = date+timedelta(1)
                    if date.weekday() < 5:
                        count_days = count_days+1
                AnalysisTimes.objects.create(analysis=analysis_form, exam=analysis_form.exam, deadline=date.date(
                ), changeDeadline=False, type_deadline_id=3, created_by=user, service_comments=None)

            Form.objects.create(
                content_object=analysis_form,
                flow=flow,
                state=flow.step_set.all()[0].state,
                parent_id=entryform.forms.first().id,
            )
        else:
            AFS_list = list(AFS)
            for AF in AFS_list[1:]:
                AF.delete()

            sampleExams = SampleExams.objects.filter(
                sample__in=sample_id, exam=AFS_list[0].exam, stain=AFS_list[0].stain
            )

            # af_form = AFS_list[0].forms.get()
            # if af_form.cancelled and sampleExams.count() > 0:
            #     af_form.cancelled = False
            #     af_form.cancelled_at = None
            #     af_form.save()
            #     AFS_list[0].manual_cancelled_date = None
            #     AFS_list[0].manual_cancelled_by = None
            #     AFS_list[0].save()
    if change:
        changeCaseVersion(True, entryform.id, request.user.id)

    return 1

def step_4_entryform(request):
    var_post = request.POST.copy()

    entryform = EntryForm.objects.get(pk=var_post.get("entryform_id"))

    block_cassette_pk = [
        v for k, v in var_post.items() if k.startswith("block_cassette_pk")
    ]

    block_start_block = [
        v for k, v in var_post.items() if k.startswith("block_start_block")
    ]

    block_end_block = [
        v for k, v in var_post.items() if k.startswith("block_end_block")
    ]

    block_start_slice = [
        v for k, v in var_post.items() if k.startswith("block_start_slice")
    ]

    block_end_slice = [
        v for k, v in var_post.items() if k.startswith("block_end_slice")
    ]

    zip_block = zip(
        block_cassette_pk,
        block_start_block,
        block_end_block,
        block_start_slice,
        block_end_slice,
    )

    for values in zip_block:
        _slices = Slice.objects.filter(
            cassette=Cassette.objects.get(pk=values[0]))
        for _slice in _slices:
            _slice.start_block = (
                datetime.strptime(values[1], "%d/%m/%Y %H:%M:%S") or None
            )
            _slice.end_block = datetime.strptime(
                values[2], "%d/%m/%Y %H:%M:%S") or None
            _slice.start_slice = (
                datetime.strptime(values[3], "%d/%m/%Y %H:%M:%S") or None
            )
            _slice.end_slice = datetime.strptime(
                values[4], "%d/%m/%Y %H:%M:%S") or None
            _slice.save()

    return True

def step_new_analysis(request):
    var_post = request.POST.copy()
    entryform = EntryForm.objects.get(pk=var_post.get("entryform_id"))

    exams_to_do = var_post.getlist("analysis")
    analyses_qs = entryform.analysisform_set.all()

    for analysis in analyses_qs:
        analysis.forms.get().delete()

    analyses_qs.delete()

    for exam in exams_to_do:
        ex = Exam.objects.get(pk=exam)
        if (
            AnalysisForm.objects.filter(
                entryform_id=entryform.id, exam_id=exam).count()
            == 0
        ):
            if ex.service_id in [1, 3, 4]:
                flow = Flow.objects.get(pk=2)
            elif ex.service_id == 5:
                continue
            else:
                flow = Flow.objects.get(pk=3)

            analysis_form = AnalysisForm.objects.create(
                entryform_id=entryform.id, exam=ex, stain=ex.stain
            )

            Form.objects.create(
                content_object=analysis_form,
                flow=flow,
                state=flow.step_set.all()[0].state,
                parent_id=entryform.forms.first().id,
            )

    sample_id = [v for k, v in var_post.items() if k.startswith("sample[id]")]

    for values in sample_id:
        sample = Sample.objects.get(pk=int(values))
        sample_exams = [
            v[0]
            for k, v in dict(var_post).items()
            if k.startswith("sample[exams][" + values)
        ]
        sample_organs = []
        for exam in sample_exams:
            sample_organs = [
                v
                for k, v in dict(var_post).items()
                if k.startswith("sample[organs][" + values + "][" + exam)
            ]
            for organ in sample_organs[0]:
                if (
                    SampleExams.objects.filter(
                        sample=sample, exam_id=exam, organ_id=organ
                    ).count()
                    == 0
                ):
                    SampleExams.objects.create(
                        sample=sample, exam_id=exam, organ_id=organ
                    )
                    for cassette in Cassette.objects.filter(sample=sample):
                        if not len(cassette.organs.filter(id=organ)):
                            cassette.organs.add(organ)
                            cassette.save()

        for cassette in Cassette.objects.filter(sample=sample):
            cassette.slice_set.all().delete()
            exams = [
                sampleexam.exam
                for sampleexam in sample.sampleexams_set.all()
                if sampleexam.exam.service_id in [1, 2, 3]
            ]
            _exams = []
            exams_uniques = []

            for item in exams:
                if item.pk not in exams_uniques:
                    exams_uniques.append(item.pk)
                    _exams.append(item)

            slice_index = 0

            for index, val in enumerate(_exams):
                slice_index = index + 1
                slice_name = cassette.cassette_name + "-S" + str(slice_index)

                analysis_form = AnalysisForm.objects.filter(
                    entryform_id=entryform.id,
                    exam_id=val.id,
                ).first()

                slice_new = Slice.objects.create(
                    entryform_id=entryform.id,
                    slice_name=slice_name,
                    index=slice_index,
                    cassette=cassette,
                    analysis=analysis_form,
                )
                slice_new.save()

    return False

def step_new_analysis2(request):
    var_post = request.POST.copy()
    entryform = EntryForm.objects.get(pk=var_post.get("entryform_id"))

    exams_to_do = var_post.getlist("analysis")
    analyses_qs = entryform.analysisform_set.all()

    new_analysisform = {}
    for exam in exams_to_do:
        ex = Exam.objects.get(pk=exam)
        if (
            AnalysisForm.objects.filter(
                entryform_id=entryform.id, exam_id=exam).count()
            == 0
        ):
            if ex.service_id in [1, 3, 4]:
                flow = Flow.objects.get(pk=2)
            elif ex.service_id == 5:
                continue
            else:
                flow = Flow.objects.get(pk=3)

            analysis_form = AnalysisForm.objects.create(
                entryform_id=entryform.id, exam=ex, stain=ex.stain
            )
            new_analysisform[exam] = analysis_form.pk

            Form.objects.create(
                content_object=analysis_form,
                flow=flow,
                state=flow.step_set.all()[0].state,
                parent_id=entryform.forms.first().id,
            )

    sample_id = [v for k, v in var_post.items() if k.startswith("sample[id]")]

    for values in sample_id:
        sample = Sample.objects.get(pk=int(values))
        sample_exams = [
            v[0]
            for k, v in dict(var_post).items()
            if k.startswith("sample[exams][" + values)
        ]
        sample_organs = []
        for exam in sample_exams:
            sample_organs = [
                v
                for k, v in dict(var_post).items()
                if k.startswith("sample[organs][" + values + "][" + exam)
            ]
            for organ in sample_organs[0]:
                if (
                    SampleExams.objects.filter(
                        sample=sample, exam_id=exam, organ_id=organ
                    ).count()
                    == 0
                ):
                    SampleExams.objects.create(
                        sample=sample, exam_id=exam, organ_id=organ
                    )
                    for cassette in Cassette.objects.filter(samples__in=[sample]):
                        if not len(cassette.organs.filter(id=organ)):
                            cassette.organs.add(organ)
                            cassette.save()

            if new_analysisform.get(exam, None):
                for cassette in Cassette.objects.filter(sample=sample):
                    last_slice_from_cassette = Slice.objects.filter(
                        cassette=cassette
                    ).last()
                    last_slice_from_cassette.pk = None
                    old_index = last_slice_from_cassette.index
                    new_index = old_index + 1
                    last_slice_from_cassette.index = new_index
                    last_slice_from_cassette.analysis_id = new_analysisform.get(
                        exam, None
                    )
                    last_slice_from_cassette.slice_name = (
                        last_slice_from_cassette.slice_name.replace(
                            "S" + str(old_index), "S" + str(new_index)
                        )
                    )
                    last_slice_from_cassette.save()

    return False



def save_identification(request, id):
    var_post = request.POST.copy()
    change = False
    ident = Identification.objects.get(pk=id)
    if ident.cage != var_post["jaula"]:
        change = True
    ident.cage = var_post["jaula"]

    if ident.group != var_post["grupo"]:
        change = True
    ident.group = var_post["grupo"]

    if str(ident.no_container) != var_post["contenedores"]:
        change = True
    ident.no_container = var_post["contenedores"]

    if ident.weight != var_post["peso"] and (
        var_post["peso"] != "0" and ident.weight == 0.0
    ):
        change = True
    ident.weight = var_post["peso"]

    if ident.extra_features_detail != var_post["extras"]:
        change = True
    ident.extra_features_detail = var_post["extras"]

    if ident.observation != var_post["observation"]:
        change = True
    ident.observation = var_post["observation"]

    if ident.is_optimum != True if "1" == var_post["optimo"] else False:
        change = True
    ident.is_optimum = var_post["optimo"]

    if ident.no_fish != var_post["no_fish"]:
        change = True
        identification_ids = Identification.objects.filter(
            entryform=ident.entryform
        ).values_list("id", flat=True)
        current_total_samples = Sample.objects.filter(
            identification__in=identification_ids
        ).order_by("-index")
        current_ident_samples = Sample.objects.filter(identification=ident).order_by(
            "-index"
        )
        new_samples = int(var_post["no_fish"]) - current_ident_samples.count()
        max_index = (
            current_total_samples.first().index
            if current_total_samples.count() > 0
            else 0
        )
        new_counter_index = 0
        for i in range(
            len(current_total_samples), len(
                current_total_samples) + new_samples
        ):
            sample = Sample.objects.create(
                entryform=ident.entryform,
                index=max_index + new_counter_index + 1,
                identification=ident,
            )
            new_counter_index += 1

    ident.no_fish = var_post["no_fish"]

    organs = var_post.getlist("organs")
    orgs = []
    for org in ident.organs_before_validations.all():
        orgs.append(str(org.id))
    if len(orgs) != len(organs):
        change = True
    for o in organs:
        if not o in orgs:
            change = True

    ident.organs.set([])
    ident.organs_before_validations.set([])

    organs_type2_count = Organ.objects.filter(
        id__in=organs, organ_type=2).count()
    if organs_type2_count > 0:
        for org in Organ.objects.all():
            ident.organs.add(org)
    else:
        for org in organs:
            ident.organs.add(int(org))

    for org in organs:
        ident.organs_before_validations.add(int(org))

    ident.save()

    if change:
        ident.removable = False
        ident.save()
        changeCaseVersion(True, ident.entryform.id, request.user.id)
    return JsonResponse({})


def list_identification(request, entryform_id):
    # try:
    organs = list(Organ.objects.all().values())

    ident = []
    for i in Identification.objects.filter(entryform_id=entryform_id):
        ident_as_dict = model_to_dict(
            i,
            exclude=[
                "organs",
                "organs_before_validations",
                "no_fish",
                "no_container",
                "temp_id",
            ],
        )
        ident.append(ident_as_dict)

    data = {
        "ident": ident,
        "organs": organs,
    }
    return JsonResponse({"ok": 1, "data": data})
    # except :
    #     return JsonResponse({'ok': 0})


def list_units(request, identification_id):
    try:
        units = []
        for u in Unit.objects.filter(identification_id=identification_id):
            unit = model_to_dict(u)
            unit["organs"] = []
            for ou in OrganUnit.objects.filter(unit=u):
                unit["organs"].append(model_to_dict(ou.organ))
            units.append(unit)

        return JsonResponse({"ok": 1, "units": units})
    except:
        return JsonResponse({"ok": 0})


def create_unit(request, identification_id, correlative):
    unit = Unit.objects.create(
        identification_id=identification_id, correlative=correlative
    )
    return JsonResponse({"ok": 1, "unit": model_to_dict(unit)})


def save_units(request):
    units = json.loads(request.POST.get("units"))
    ok = 1
    for unit in units:
        unit_obj = Unit.objects.get(pk=unit["id"])
        unit_obj.correlative = unit["correlative"]
        unit_obj.save()

        organs_fmt = list(map(lambda x: int(x.split("-")[0]), unit["organs"]))

        # Check if organs previously saved must exists in new organs set.
        # If it doesn't exists must be removed
        org_already_used = []
        for ou in OrganUnit.objects.filter(unit=unit_obj):
            ou_exists_in_new_set = False
            for org in organs_fmt:
                if ou.organ.pk == org and org not in org_already_used:
                    ou_exists_in_new_set = True
                    org_already_used.append(org)
                    break

            if not ou_exists_in_new_set:

                # # Check if the organ is used in a Cassette of that unit
                # # If it's being used then don't delete it and skip to the next organ
                # cassettes = Cassette.objects.filter(unit=unit_obj)
                # cassettes_organs = CassetteOrgan.objects.filter(
                #     cassette_id__in=cassettes.values_list("id", flat=True),
                #     organ=ou.organ,
                # )

                # if cassettes_organs.count() > 0:
                #     ok = 0
                #     continue

                # Check if there are samples with the OrganUnit.
                # If they exist then validate if when removing the OrgaUnit the sample remains empty, therefore it must also be removed.
                samples = Sample.objects.filter(unit_organs__in=[ou.id])
                for s in samples:
                    s.unit_organs.remove(ou)
                    SampleExams.objects.filter(unit_organ=ou).delete()

                    if s.unit_organs.all().count() == 0:
                        SampleExams.objects.filter(sample=s).delete()
                        s.delete()

                ou.delete()

        unit_organs = OrganUnit.objects.filter(unit=unit_obj)

        # Check if new organs set exists in unit.
        # Just if it doesn't exists must be created as OrganUnit.
        ou_already_used = []
        for org in organs_fmt:
            new_org_exists_in_unit = False
            for ou in unit_organs:
                if ou.organ.pk == org and ou.id not in ou_already_used:
                    new_org_exists_in_unit = True
                    ou_already_used.append(ou.id)
                    break

            if not new_org_exists_in_unit:
                OrganUnit.objects.create(unit=unit_obj, organ_id=org)

    if ok:
        return JsonResponse({"ok": 1})

    return JsonResponse({"ok": 0, "message": "CASSETTES"})


def remove_unit(request, id):
    cassettes = Cassette.objects.filter(unit_id=id)

    if cassettes.count() > 0:
        return JsonResponse({"ok": 0, "message": "CASSETTES"})

    for OU in OrganUnit.objects.filter(unit_id=id):
        samples = Sample.objects.filter(unit_organs__in=[OU.id])
        for s in samples:
            s.unit_organs.remove(OU)
            if s.unit_organs.all().count() == 0:
                s.delete()
    Unit.objects.get(pk=id).delete()
    return JsonResponse({"ok": 1})


def new_empty_identification(request, entryform_id, correlative):
    try:
        ident = Identification.objects.create(
            entryform_id=entryform_id,
            temp_id="".join(
                random.choices(string.ascii_uppercase + string.digits, k=11)
            ),
            removable=True,
            correlative=correlative,
        )
        return JsonResponse({"ok": 1, "id": ident.id, "obj": model_to_dict(ident)})
    except:
        return JsonResponse({"ok": 0})


def save_new_identification(request, id):
    var_post = request.POST.copy()
    change = False
    ident = Identification.objects.get(pk=id)

    if ident.cage != var_post["cage"]:
        change = True
        ident.cage = var_post["cage"]

    if ident.group != var_post["group"]:
        change = True
        ident.group = var_post["group"]

    if (
        ident.weight != var_post["weight"]
        and var_post["weight"]
        and var_post["weight"].strip() != ""
    ):
        change = True
        ident.weight = var_post["weight"]

    if ident.extra_features_detail != var_post["extra_features_detail"]:
        change = True
        ident.extra_features_detail = var_post["extra_features_detail"].strip()

    if ident.observation != var_post["observation"]:
        change = True
        ident.observation = var_post["observation"].strip()

    if ident.is_optimum != (True if "1" == var_post["is_optimum"] else False):
        change = True
        ident.is_optimum = True if "1" == var_post["is_optimum"] else False

    if ident.client_case_number != var_post["client_case_number"]:
        change = True
        ident.client_case_number = var_post["client_case_number"].strip()

    if ident.quantity != var_post["quantity"]:
        change = True
        ident.quantity = int(var_post["quantity"])

    if ident.correlative != var_post["correlative"]:
        change = True
        ident.correlative = int(var_post["correlative"])

    if ident.samples_are_correlative != (
        True if "1" == var_post["samples_are_correlative"] else False
    ):
        change = True
        ident.samples_are_correlative = var_post["samples_are_correlative"]

    ident.save()

    if change:
        ident.removable = False
        ident.save()
        changeCaseVersion(True, ident.entryform.id, request.user.id)
    return JsonResponse({"ok": 1})


def remove_identification(request, id):
    try:
        units = Unit.objects.filter(identification_id=id)
        cassettes = Cassette.objects.filter(
            unit_id__in=units.values_list("id", flat=True)
        )

        if cassettes.count() > 0:
            return JsonResponse({"ok": 0, "message": "CASSETTES"})

        units.delete()
        Sample.objects.filter(identification_id=id).delete()
        Identification.objects.get(pk=id).delete()
    except:
        return JsonResponse({"ok": 1})


def save_generalData(request, id):
    """
    Updates the given id's :model:`backend.EntryForm`,
    creating a new :model:`backend.CaseVersion` when any change
    is registered.
    """
    var_post = request.POST.copy()
    entry = EntryForm.objects.get(pk=id)

    change = any(key for key in var_post.items())

    entry.specie_id = int(var_post["specie"])
    entry.laboratory_id = int(var_post["laboratory"])
    entry.watersource_id = int(var_post["watersource"])
    entry.larvalstage_id = int(var_post["larvalstage"])
    if "fixative" in var_post and var_post["fixative"]:
        entry.fixative_id = int(var_post["fixative"])
    entry.customer_id = int(var_post["client"])
    entry.entryform_type_id = int(var_post["entryform_type"])
    entry.entry_format = int(var_post["entry_format"])
    
    
    entry.responsible = var_post["responsable"]
    entry.no_order = var_post["no_order"]
    entry.no_request = var_post["no_solic"]
    entry.transfer_order = var_post["transfer_order"]
    entry.anamnesis = var_post["anamnesis"]
    entry.sampled_at_hour = var_post["sampled_at_hour"]
    entry.sampled_at_am_pm = var_post["sampled_at_am_pm"]
    
    if var_post.get("company_center") != "" and var_post.get("company_center") != None:
        entry.company_index_id = int(var_post.get("company_index"))

    if var_post.get("company_center") != "" and var_post.get("company_center") != None:
        entry.company_center_id = var_post.get("company_center")
        entry.company_laboratory = None
    elif len(str(var_post.get("company_laboratory")).split(' ')) > 0:
        entry.company_laboratory = str(var_post.get("company_laboratory")).upper()
        entry.company_center_id = None
    

    try:
        entry.created_at = datetime.strptime(
            var_post.get("recive"), "%d/%m/%Y %H:%M")
        entry.sampled_at = datetime.strptime(
            var_post.get("muestreo"), "%d/%m/%Y")
    except:
        pass

    if change:
        changeCaseVersion(True, id, request.user.id)

    entry.save()

    return JsonResponse({})



def completeForm(request, form_id):
    form = Form.objects.get(pk=form_id)
    form.form_closed = True
    form.closet_at = datetime.now()
    form.save()
    return JsonResponse({"ok": True})


def finishReception(request, form_id):
    form = Form.objects.get(pk=form_id)
    form.reception_finished = True
    form.reception_finished_at = datetime.now()
    form.save()
    return JsonResponse({"ok": True})


def save_step1(request, form_id):
    valid = step_1_entryform(request)
    return JsonResponse({"ok": valid})


def service_assignment(request):
    var_post = request.POST.copy()
    analysis = var_post.get("analysis", None)
    pathologist = var_post.get("pathologist", None)
    comment = var_post.get("comment", None)

    template = "app/template_assignment.html"
    from_email = settings.EMAIL_HOST_USER2
    connection = mail.get_connection(
        username=settings.EMAIL_HOST_USER2,
        password=settings.EMAIL_HOST_PASSWORD2,
    )
    msg_res = ""

    try:
        if analysis:
            af = AnalysisForm.objects.get(pk=int(analysis))
            to = ""
            message = ""
            samples = Sample.objects.filter(entryform=af.entryform).values_list(
                "id", flat=True
            )
            nro_samples = SampleExams.objects.filter(
                sample__in=samples, exam=af.exam
            ).count()

            deadline = AnalysisTimes.objects.filter(
                analysis_id=af.id, type_deadline_id=3).last()
            if not af.patologo and pathologist != "NA":
                # Asignando patologo por primera vez
                af.patologo_id = int(pathologist)
                af.assignment_comment = comment if comment and comment != "" else None
                af.assignment_done_at = datetime.now()
                af.save()
                af.refresh_from_db()
                to = af.patologo.email
                subject = (
                    "Derivación de Análisis/"
                    + af.entryform.no_caso
                    + "/"
                    + af.exam.name
                )
                ctx = {
                    "msg": "Informamos derivación de análisis "
                    + af.exam.name
                    + ", correspondiente al caso "
                    + af.entryform.no_caso
                    + " ("
                    + str(nro_samples)
                    + " muestras) ingresado el "
                    + af.created_at.strftime("%d/%m/%Y"),
                    "deadline": deadline.deadline.strftime("%d/%m/%Y")
                    if deadline else "",
                    "comment": af.assignment_comment if af.assignment_comment else "",
                }
                message = get_template(template).render(context=ctx)
                msg = EmailMultiAlternatives(
                    subject, message, from_email, [to], connection=connection
                )
                msg.content_subtype = "html"
                try:
                    msg.send()
                except:
                    msg_res = "No ha sido posible enviar el correo de notificación"
                    pass

            elif af.patologo and pathologist != "NA":
                # Reemplazando al patologo anterior
                prev_patologo = af.patologo
                af.patologo_id = int(pathologist)
                af.assignment_comment = comment if comment and comment != "" else None
                af.assignment_done_at = datetime.now()
                af.pre_report_started = False
                af.pre_report_started_at = None
                af.pre_report_ended = False
                af.pre_report_ended_at = None
                af.save()
                af.refresh_from_db()

                # Al nuevo
                to = af.patologo.email
                subject = (
                    "Derivación de Análisis/"
                    + af.entryform.no_caso
                    + "/"
                    + af.exam.name
                )
                ctx = {
                    "msg": "Informamos que se ha reasignado a usted el análisis "
                    + af.exam.name
                    + ", correspondiente al caso "
                    + af.entryform.no_caso
                    + " ("
                    + str(nro_samples)
                    + " muestras) ingresado el "
                    + af.created_at.strftime("%d/%m/%Y"),
                    "deadline": deadline.deadline.strftime("%d/%m/%Y"),
                    "comment": af.assignment_comment if af.assignment_comment else "",
                }
                message = get_template(template).render(context=ctx)
                msg = EmailMultiAlternatives(
                    subject, message, from_email, [to], connection=connection
                )
                msg.content_subtype = "html"
                try:
                    msg.send()
                except:
                    msg_res = "No ha sido posible enviar el correo de notificación"
                    pass

                # Al anterior
                to = prev_patologo.email
                subject = (
                    "Reasignación de Análisis/"
                    + af.entryform.no_caso
                    + "/"
                    + af.exam.name
                )
                ctx = {
                    "msg": "Informamos que el análisis "
                    + af.exam.name
                    + " que estaba asignado a usted, correspondiente al caso "
                    + af.entryform.no_caso
                    + ", ha sido reasignado.",
                }
                message = get_template(template).render(context=ctx)
                msg = EmailMultiAlternatives(
                    subject, message, from_email, [to], connection=connection
                )
                msg.content_subtype = "html"
                try:
                    msg.send()
                except:
                    msg_res = "No ha sido posible enviar el correo de notificación"
                    pass
            elif af.patologo and pathologist == "NA":
                # Desasignando patologo
                prev_patologo = af.patologo
                af.patologo_id = None
                af.assignment_deadline = None
                af.assignment_comment = comment if comment and comment != "" else None
                af.assignment_done_at = None
                af.save()
                af.refresh_from_db()
                to = prev_patologo.email
                subject = (
                    "Reasignación de Análisis/"
                    + af.entryform.no_caso
                    + "/"
                    + af.exam.name
                )
                ctx = {
                    "msg": "Informamos que el análisis "
                    + af.exam.name
                    + " que estaba asignado a usted, correspondiente al caso "
                    + af.entryform.no_caso
                    + ", ha sido reasignado.",
                    "comment": af.assignment_comment if af.assignment_comment else "",
                }
                message = get_template(template).render(context=ctx)
                msg = EmailMultiAlternatives(
                    subject, message, from_email, [to], connection=connection
                )
                msg.content_subtype = "html"
                try:
                    msg.send()
                except:
                    msg_res = "No ha sido posible enviar el correo de notificación"
                    pass
            else:
                # Caso no controlado
                pass
            return JsonResponse({"ok": 1, "msg": msg_res})
        else:
            msg_res = "Análisis requerido"
            return JsonResponse({"ok": 0, "msg": msg_res})
    except:
        msg_res = "Problemas al procesar la solicitud de derivación"
        return JsonResponse({"ok": 0, "msg": msg_res})


def dashboard_analysis(request):
    exam = request.GET.get("exam")
    year = request.GET.get("year")
    mes = request.GET.getlist("mes")
    query = """
                SELECT YEAR(a.created_at) AS `year`, MONTH(a.created_at) AS `month`, COUNT(a.id) AS count
                FROM backend_sample s
                INNER JOIN backend_analysisform a ON s.entryform_id = a.entryform_id
                INNER JOIN backend_entryform e ON a.entryform_id = e.id
                INNER JOIN workflows_form f ON a.entryform_id = f.object_id
                WHERE f.flow_id in (2,3) AND f.cancelled = 0
                AND YEAR(a.created_at) = {0}
                AND MONTH(a.created_at) IN {1}
            """.format(
        year, tuple(mes)
    )
    if exam != "0":
        query += """
                    AND a.exam_id = %s
                """.format(
            exam
        )
    query += """
                GROUP BY `year`, `month`
                ORDER BY `month`
            """
    cursor1 = connection.cursor()
    data1 = cursor1.execute(query)
    data = cursor1.fetchall()

    return JsonResponse({"data": data})


def dashboard_lefts(request):
    exam = request.GET.get("exam")
    year = request.GET.get("year")
    mes = request.GET.getlist("mes")
    query = """
                SELECT YEAR(e.created_at) AS `year`, MONTH(e.created_at) AS `month`, CONCAT(u.first_name,' ',u.last_name) AS fullName, COUNT(e.id) AS count
                FROM backend_analysisform e
                LEFT JOIN auth_user u ON e.patologo_id = u.id
                INNER JOIN workflows_form f ON f.object_id = e.id
                WHERE f.form_closed = 0 AND f.flow_id in (2,3) AND f.cancelled = 0
                AND YEAR(e.created_at) = {0}
                AND MONTH(e.created_at) IN {1}
            """.format(
        year, tuple(mes)
    )
    if exam != "0":
        query += """
                    AND e.exam_id = {0}
                """.format(
            exam
        )
    query += """
                GROUP BY `year`, `month`, fullName
                ORDER BY `month`
            """
    cursor1 = connection.cursor()
    data1 = cursor1.execute(query)
    data = cursor1.fetchall()

    return JsonResponse({"data": data})


def dashboard_reports(request):
    exam = request.GET.get("exam")
    year = request.GET.get("year")
    mes = request.GET.getlist("mes")

    query = """
                SELECT YEAR(f.closed_at) AS `year`, MONTH(f.closed_at) AS `month`, COUNT(e.id) AS count
                FROM backend_analysisform e
                INNER JOIN workflows_form f ON f.object_id = e.id
                WHERE f.form_closed = 1 AND f.flow_id in (2,3) AND f.cancelled = 0
                AND YEAR(f.closed_at) = {0}
                AND MONTH(f.closed_at) IN {1}
            """.format(
        year, tuple(mes)
    )
    if exam != "0":
        query += """
                    AND e.exam_id = {0}
                """.format(
            exam
        )
    query += """
                GROUP BY `year`, `month`
                ORDER BY `month`
            """
    cursor1 = connection.cursor()
    data1 = cursor1.execute(query)
    data = cursor1.fetchall()

    return JsonResponse({"data": data})


def close_service(request, form_id, closing_date):
    var_post = request.POST.copy()
    form = Form.objects.get(pk=form_id)
    form.form_closed = True
    form.closed_at = datetime.now()
    form.save()
    try:
        form.content_object.manual_closing_date = datetime.strptime(
            closing_date, "%d-%m-%Y"
        )
        form.content_object.report_code = var_post.get("report-code")
        form.content_object.save()
    except Exception as e:
        pass
    return JsonResponse({"ok": True})


def cancel_service(request, form_id):
    var_post = request.POST.copy()
    form = Form.objects.get(pk=form_id)
    form.cancelled = True
    form.cancelled_at = datetime.now()
    form.save()
    try:
        form.content_object.manual_cancelled_date = datetime.strptime(
            var_post.get("date"), "%d-%m-%Y"
        )
        form.content_object.manual_cancelled_by = request.user
        service_comment = ServiceComment.objects.create(
            text="[Comentario de Anulación]: " + var_post.get("comment"),
            done_by=request.user,
        )
        form.content_object.service_comments.add(service_comment)
        form.content_object.researches.clear()
        form.content_object.save()
    except Exception as e:
        pass
    return JsonResponse({"ok": True})


def reopen_form(request, form_id):
    var_post = request.POST.copy()
    form = Form.objects.get(pk=form_id)
    form.cancelled = False
    form.cancelled_at = None
    form.form_reopened = True
    form.form_closed = False
    form.closed_at = None
    form.save()
    try:
        form.content_object.manual_reopened_date = datetime.strptime(
            var_post.get("date"), "%d-%m-%Y"
        )
        form.content_object.manual_reopened_by = request.user
        service_comment = ServiceComment.objects.create(
            text="[Comentario de Reapertura]: " + var_post.get("comment"),
            done_by=request.user,
        )
        form.content_object.service_comments.add(service_comment)
        form.content_object.researches.clear()
        form.content_object.manual_cancelled_date = None
        form.content_object.manual_closing_date = None
        form.content_object.report_code = None
        form.content_object.save()
    except Exception as e:
        pass
    return JsonResponse({"ok": True})


def delete_sample(request, id):
    sample = Sample.objects.get(pk=id)
    ident = sample.identification
    ident.no_fish = ident.no_fish - 1
    ident.save()
    sample.delete()
    changeCaseVersion(True, ident.entryform.id, request.user.id)

    return JsonResponse({"ok": True})


def init_pre_report(request, analysis_id):
    try:
        analysis = AnalysisForm.objects.get(pk=analysis_id)

        if analysis.on_hold or analysis.on_standby:
            analysis.on_hold = None
            analysis.on_standby = None

        analysis.pre_report_started = True
        analysis.pre_report_started_at = datetime.now()
        analysis.save()
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "msg": str(e)})


def end_pre_report(request, analysis_id, end_date):
    try:
        pre_report_ended_at = datetime.strptime(end_date, "%d-%m-%Y %H:%M")
    except ValueError:
        pre_report_ended_at = datetime.now()

    try:
        analysis = AnalysisForm.objects.get(pk=analysis_id)
    except AnalysisForm.DoesNotExists as e:
        return JsonResponse({"ok": False, "msg": str(e)})
    else:
        analysis.pre_report_ended = True
        analysis.pre_report_ended_at = pre_report_ended_at
        analysis.save()

        comment = request.POST.get("comment")

        user_areas = UserArea.objects.filter(user=analysis.patologo)
        areas = Area.objects.filter(
            pk__in=user_areas.values_list("area_id", flat=True))
        leads = UserArea.objects.filter(area__in=areas, role=0)

        recipients = [lead.user.email for lead in list(leads)]
        recipients.extend(
            [
                analysis.patologo.email,
                "carlos.sandoval@vehice.com",
                "cristian.aedo@vehice.com",
                "denis.cardenas@vehice.com",
                "mario.mendoza@vehice.com",
            ]
        )

        subject = f"{analysis} - {analysis.entryform.customer.name}"
        connection = mail.get_connection(
            username=settings.EMAIL_HOST_USER2,
            password=settings.EMAIL_HOST_PASSWORD2,
        )
        from_email = f"Derivación <{settings.EMAIL_HOST_USER2}>"
        context = {
            "msg": (
                f"Informamos preinforme terminado de análisis {analysis.exam.name} "
                f"por el patólogo {analysis.patologo.first_name} {analysis.patologo.last_name}, "
                f"correspondiente al caso {analysis.entryform.no_caso} "
                f"ingresado el {analysis.created_at}, su fecha de cierre es "
                f"{analysis.pre_report_ended_at}."
                f"Adjunta este comentario: "
                f"{comment}"
            ),
        }
        template = "app/template_assignment.html"
        message = get_template(template).render(context=context)
        email = EmailMultiAlternatives(
            subject,
            message,
            from_email,
            recipients,
            connection=connection,
        )
        email.content_subtype = "html"

        try:
            email.send()
        except (BadHeaderError, SMTPException):
            return JsonResponse({"ok": False})

        return JsonResponse({"ok": True})


def save_scores(request, type, id):
    var_post = request.POST.copy()
    try:
        if type == "analysis":
            form = AnalysisForm.objects.get(pk=id)
            if var_post.get("score_diagnostic") != None:
                form.score_diagnostic = var_post.get("score_diagnostic", None)
            if var_post.get("score_report") != None:
                form.score_report = var_post.get("score_report", None)
            form.save()
        if type == "group":
            analysisgroups = AnalysisGrouper.objects.filter(grouper=id)
            for analysisgroup in analysisgroups:
                if var_post.get("score_diagnostic") != None:
                    analysisgroup.analysis.score_diagnostic = var_post.get(
                        "score_diagnostic", None)
                if var_post.get("score_report") != None:
                    analysisgroup.analysis.score_report = var_post.get(
                        "score_report", None)
                analysisgroup.analysis.save()

        return JsonResponse(
            {
                "ok": True,
                "score_diagnostic": form.score_diagnostic,
                "score_report": form.score_report,
            }
        )
    except Exception as e:
        return JsonResponse({"ok": False})


def get_scores(request, type, id):
    try:
        if type == "analysis":
            form = AnalysisForm.objects.get(pk=id)
        if type == "group":
            form = AnalysisGrouper.objects.filter(grouper=id).first().analysis
        return JsonResponse(
            {
                "ok": True,
                "score_diagnostic": form.score_diagnostic,
                "score_report": form.score_report,
            }
        )
    except Exception as e:
        return JsonResponse({"ok": False})


def get_research_metadata(request, id):
    try:
        r = Research.objects.get(pk=id)
        r_json = model_to_dict(r)
        r_json["init_date"] = r_json["init_date"].strftime("%d/%m/%Y %H:%M")
        r_json["clients"] = [client.id for client in r_json["clients"]]

        r_json["client_services"] = {}
        for serv in r_json["services"]:
            if serv.entryform.customer_id in r_json["client_services"]:
                r_json["client_services"][serv.entryform.customer_id].append(
                    serv.id)
            else:
                r_json["client_services"][serv.entryform.customer_id] = [serv.id]

        r_json["services"] = [serv.id for serv in r_json["services"]]
        r_json["status"] = 1 if r_json["status"] else 0

        return JsonResponse({"ok": True, "research": r_json})
    except Exception as e:
        print(e)
        return JsonResponse({"ok": False})


def force_form_to_step(request, form, step):
    try:
        form = Form.objects.get(pk=form)

        if form.reception_finished and int(step) in (2, 3):
            form.reception_finished = False
            form.reception_finished_at = None
        form.state_id = step
        form.save()

        return JsonResponse({"ok": True})
    except:
        return JsonResponse({"ok": False})


def fix_missing_units(request):

    cont = 0
    cont_to_procces = 0

    for ident in Identification.objects.filter(entryform_id__lte=2034).order_by(
        "-entryform"
    ):
        samples = Sample.objects.filter(identification=ident).order_by("index")
        units = Unit.objects.filter(identification=ident)

        if units.count() == 0:
            unit_index = 1
            for sample in samples:
                sample_exams = SampleExams.objects.filter(sample=sample)
                unit = Unit.objects.create(
                    correlative=unit_index, identification=ident)
                unit_index += 1

                unit_organs_id = []
                unit_organs = []
                for se in sample_exams:
                    Unit_Organ = OrganUnit.objects.filter(
                        unit=unit, organ=se.organ
                    ).first()

                    if not Unit_Organ:
                        Unit_Organ = OrganUnit.objects.create(
                            unit=unit, organ=se.organ)
                    if Unit_Organ.id not in unit_organs_id:
                        unit_organs_id.append(Unit_Organ.id)
                        unit_organs.append(Unit_Organ)

                    se.unit_organ = Unit_Organ
                    se.save()

                for uo in unit_organs:
                    sample.unit_organs.add(uo)
                sample.save()

            cont_to_procces += 1

        ident.quantity = Unit.objects.filter(identification=ident).count()
        ident.save()
        cont += 1

    result = {
        "Identificaciones Revisadas": cont,
        "Identificaciones Modificadas (sin unidades)": cont_to_procces,
    }

    return JsonResponse(
        {
            "ok": True,
            "response": result,
            "mensaje": "Se han creado las unidades y órganos faltantes en base a los individuos y servicios previamente definidos de manera exitosa.",
        }
    )


def centers_list(request):
    centers = Center.objects.all()

    datalist = [center.name for center in centers]

    return JsonResponse(datalist, safe=False)


def toggle_analysis_status(request, pk):
    analysis = get_object_or_404(AnalysisForm, pk=pk)

    form_data = json.loads(request.body)

    if form_data["is_hold"]:
        if analysis.on_hold:
            analysis.on_hold = None
        else:
            motive = form_data["motive"]
            analysis.on_hold = datetime.now()

            service_comment = ServiceComment.objects.create(
                text=f"[EN ESPERA]: {motive}",
                done_by=request.user,
            )
            analysis.service_comments.add(service_comment)
    else:
        if analysis.on_standby:
            analysis.on_standby = None
        else:
            motive = form_data["motive"]
            analysis.on_standby = datetime.now()

            service_comment = ServiceComment.objects.create(
                text=f"[PAUSADO]: {motive}",
                done_by=request.user,
            )
            analysis.service_comments.add(service_comment)

    analysis.save()

    return JsonResponse({"status": "OK"})


# Get analysis deadlines
def get_serviceDeadline(request, id):
    try:
        analysis = AnalysisForm.objects.get(id=id)
        analysisTimes = AnalysisTimes.objects.filter(analysis=analysis)
        data = {}

        if analysisTimes.exists():
            if AnalysisTimes.objects.filter(analysis=analysis, type_deadline=1).last() != None:
                laboratoryDeadline = AnalysisTimes.objects.filter(
                    analysis=analysis, type_deadline=1).last().deadline.__format__('%d-%m-%Y')
            else:
                laboratoryDeadline = analysis.exam.laboratory_deadline

            if AnalysisTimes.objects.filter(analysis=analysis, type_deadline=2).exists():
                pathologistDeadline = AnalysisTimes.objects.filter(
                    analysis=analysis, type_deadline=2).last().deadline.__format__('%d-%m-%Y')
            else:
                pathologistDeadline = analysis.exam.pathologist_deadline

            if AnalysisTimes.objects.filter(analysis=analysis, type_deadline=3).exists():
                reviewDeadline = AnalysisTimes.objects.filter(
                    analysis=analysis, type_deadline=3).last().deadline.__format__('%d-%m-%Y')
            else:
                reviewDeadline = analysis.exam.review_deadline
            exists = True
            analysisTimes_comment = AnalysisTimes.objects.filter(
                analysis=analysis).last().service_comments
            if analysisTimes_comment == None:
                comment = ""
            else:
                comment = analysisTimes_comment.text
        else:
            laboratoryDeadline = analysis.exam.laboratory_deadline
            pathologistDeadline = analysis.exam.pathologist_deadline
            reviewDeadline = analysis.exam.review_deadline
            exists = False
            comment = ""

        data["laboratoryDeadline"] = laboratoryDeadline
        data["pathologistDeadline"] = pathologistDeadline
        data["reviewDeadline"] = reviewDeadline

        return JsonResponse(
            {
                "ok": True,
                "data": data,
                "created_at": analysis.created_at.date(),
                "exists": exists,
                "comment": comment
            }
        )
    except Exception as e:
        return JsonResponse({"ok": False})


# Save analysis deadlines
def save_serviceDeadline(request, id):
    var_post = request.POST.copy()
    try:
        analysis = AnalysisForm.objects.get(id=id)
        user = request.user
        comment_text = var_post["comment"]

        if comment_text != "":
            comment = ServiceComment.objects.create(
                text=comment_text, done_by=user, created_at=datetime.now())
        else:
            comment = None

        for value in var_post:
            if value != "comment":
                changeDeadline = False
                str_date = str(var_post.getlist(value)[0]).replace('/', '-')
                finish_date = datetime.strptime(str_date, "%d-%m-%Y").date()

                if value == "laboratoryDeadline":
                    start_date = analysis.created_at.date()
                    standar = analysis.exam.laboratory_deadline
                if value == "pathologistDeadline":
                    str_date = str(var_post.getlist(
                        "laboratoryDeadline")[0]).replace('/', '-')
                    start_date = datetime.strptime(str_date, "%d-%m-%Y").date()
                    standar = analysis.exam.pathologist_deadline
                if value == "reviewDeadline":
                    str_date = str(var_post.getlist(
                        "pathologistDeadline")[0]).replace('/', '-')
                    start_date = datetime.strptime(str_date, "%d-%m-%Y").date()
                    standar = analysis.exam.review_deadline

                count_days = 0
                while start_date < finish_date:
                    if start_date.weekday() < 5:
                        count_days = count_days+1
                    start_date = start_date+timedelta(1)

                if count_days > standar or count_days < standar:
                    changeDeadline = True

                deadline_type = var_post.getlist(value)[1]
                deadline = AnalysisTimes.objects.create(analysis=analysis, exam=analysis.exam, deadline=finish_date,
                                                        changeDeadline=changeDeadline, type_deadline_id=deadline_type, created_by=user, service_comments=comment)
                deadline.save()

        return JsonResponse(
            {
                "ok": True,
            }
        )
    except Exception as e:
        print(e)
        return JsonResponse({"ok": False})


class ConsolidadosBase(View):
    @method_decorator(login_required)
    def get(self, request, form_id):
        analysisform = AnalysisForm.objects.get(id=form_id)
        if analysisform.exam.subclass == "HE":
            view = CONSOLIDADOS_HE()
        elif analysisform.exam.name == "SCORE_GILL":
            view = CONSOLIDADOS_SG()
        elif analysisform.exam.name == "GENERAL_SCORE":
            view = CONSOLIDADOS_GS()
            
        return view.get(request, form_id)
    @method_decorator(login_required)
    def post(self, request, form_id):
        analysisform = AnalysisForm.objects.get(id=form_id)
        if analysisform.exam.subclass == "HE":
            view = CONSOLIDADOS_HE()
        elif analysisform.exam.name == "SCORE_GILL":
            view = CONSOLIDADOS_SG()
        elif analysisform.exam.name == "GENERAL_SCORE":
            view = CONSOLIDADOS_GS()
        
        return view.post(request, form_id)

    @method_decorator(login_required)
    def delete(self, request, form_id):
        analysisform = AnalysisForm.objects.get(id=form_id)
        if analysisform.exam.subclass == "HE":
            view = CONSOLIDADOS_HE()
        elif analysisform.exam.name == "SCORE_GILL":
            view = CONSOLIDADOS_SG()
        return view.delete(request, form_id)

class CONSOLIDADOS_HE(View):
    http_method_names = ["get", "post", "delete"]

    @method_decorator(login_required)
    def get(self, request, form_id):

        organos = []
        samples = []
        sampleResults = []
        context = {
            "samples": [],
            "sampleExams": [],
            "diagnosticos": [],
            "results": [],
            "sampleResults": [],
        }

        analysis = AnalysisForm.objects.get(id=form_id)
        context["no_caso"] = analysis.entryform.no_caso
        context["exam_name"] = analysis.exam.name
        sampleExams = SampleExams.objects.filter(
            sample__entryform=analysis.entryform, exam=analysis.exam, stain=analysis.stain)
        sampleExamResults = SampleExamResult.objects.filter(analysis=analysis)

        for sampleExamResult in sampleExamResults:
            if sampleExamResult.sample_exam == None:
                AnalysisSampleExmanResult.objects.filter(sample_exam_result=sampleExamResult).delete()
                sampleExamResult.delete()

        sampleExamResults = SampleExamResult.objects.filter(analysis=analysis)
        context["sampleResults"] = serialize(
            'json', sampleExamResults, use_natural_foreign_keys=True, use_natural_primary_keys=True)

        for sampleExamResult in sampleExamResults:
            sampleResults.append(sampleExamResult.result_organ.id)
        sampleResults = list(set(sampleResults))

        context["results"] = sampleResults
        context["sampleExams"] = serialize(
            'json', sampleExams, use_natural_foreign_keys=True, use_natural_primary_keys=True)

        for sampleExam in sampleExams:
            organos.append(sampleExam.organ)
            sample = Sample.objects.get(id=sampleExam.sample.id)
            if sample not in samples:
                samples.append(sample)

        samples = sorted(samples, key=lambda x: x.index)
        context["samples"] = serialize(
            'json', samples, use_natural_foreign_keys=True, use_natural_primary_keys=True)
        organos = list(set(organos))
                
        flag = True
        for organo in organos:
            if organo.id == 49 or organo.id == 50 or organo.id == 72:
                results = ResultOrgan.objects.all().exclude(organ__name__contains='-')
                flag = False
                break
            
        if (flag):      
            results = ResultOrgan.objects.filter(organ__in=organos)

        for result in results:
            
            if "-" not in result.organ.name:
                if result.result.type_result.id == 1:
                    context["diagnosticos"].append({
                        "id": result.id,
                        "resultado": result.result,
                        "organo": result.organ.name
                    })

        route = "app/consolidados/consolidado_HE/consolidados_he.html"
        return render(request, route, context)

    @method_decorator(login_required)
    def post(self, request, form_id):

        analysis = AnalysisForm.objects.get(id=form_id)
        request = request.POST
        distribution = 0

        try:
            for key, value in request.items():
                keys = key[5:-1].split("%")

                if keys[0] == "distribution":
                    distribution = value
                else:
                    try:
                        sampleExam = SampleExams.objects.get(
                            sample__entryform=analysis.entryform, exam=analysis.exam, stain=analysis.stain, sample__index=keys[2], organ__name=keys[0])
                    except:
                        sampleExam = None
                    if not sampleExam:
                        sampleExam = SampleExams.objects.get(
                            sample__entryform=analysis.entryform, exam=analysis.exam, stain=analysis.stain, sample__index=keys[2])
                    sampleExamResult, created = SampleExamResult.objects.update_or_create(
                        sample_exam=sampleExam, result_organ_id=keys[1], defaults={'distribution': distribution, 'value': value})
                    analysisSampleExmanResult = AnalysisSampleExmanResult.objects.update_or_create(
                        analysis=analysis, sample_exam_result=sampleExamResult, defaults={'created_at': datetime.now()})

            return JsonResponse({'ok': True})
        except Exception as e:
            print(e)
            return JsonResponse({"ok": False, "error":e.__str__()})

    def delete(self, request, form_id):

        delete = QueryDict(request.body)
        organ = delete.get('organ')
        diagnostic = delete.get('diagnostic')

        sampleExamResults = SampleExamResult.objects.filter(
            analysis=form_id, result_organ_id=diagnostic)
        for sampleExamResult in sampleExamResults:
            AnalysisSampleExmanResult.objects.get(
                analysis_id=form_id, sample_exam_result=sampleExamResult).delete()
            sampleExamResult.delete()

        return JsonResponse({'ok': True})


class CONSOLIDADOS_SG(View):
    http_method_names = ["get", "post", "delete"]

    @method_decorator(login_required)
    def get(self, request, form_id):

        context = {
            "samples": [],
            "identifications": [],
            "entryform":'',
        }


        analysis = AnalysisForm.objects.get(id=form_id)
        context["no_caso"] = analysis.entryform.no_caso
        samples = list(Sample.objects.filter(entryform__id=analysis.entryform.id).order_by("index"))
        list_empty = dict()

        
        samples_id =SampleExams.objects.filter(sample__entryform__id=analysis.entryform.id, exam=analysis.exam, organ_id = 51).values_list('sample',flat=True)

        samples = list(Sample.objects.filter(id__in=samples_id).order_by("index"))

        identifications = []
        for sample in samples:
            if sample.identification not in identifications:
                identifications.append(sample.identification)

        list_empty = dict()

        watersource = WaterSource.objects.filter(name=analysis.entryform.watersource.name).first()
        type_of_water = watersource.type_of_water  # Assuming 'type_of_water' is the field name in your model

        entryForm = EntryForm.objects.get(id=analysis.entryform.id)

        results= Result.objects.filter(type_result__id__in=[3,4,5,6,7])
        for result in results:
            context[result.name] =  result.id

        for sample in range(len(samples)):
            try:
                if samples[sample].identification.id != samples[sample+1].identification.id:
                    list_empty[f"sample_{samples[sample].id}"] = {
                        "id": samples[sample].id,
                        "index": samples[sample].index,
                        "identification": {
                                "id": samples[sample].identification.id,
                                "cage": samples[sample].identification.cage,
                            }
                    }

                    prom={
                        "identification": {
                                "id": samples[sample].identification.id,
                                "cage": samples[sample].identification.cage,
                            }
                    }
                    list_empty[f"promedio_identification_{samples[sample].identification.id}"] = prom
                else:
                    list_empty[f"sample_{samples[sample].id}"] = {
                        "id": samples[sample].id,
                        "index": samples[sample].index,
                        "identification": {
                                "id": samples[sample].identification.id,
                                "cage": samples[sample].identification.cage,
                            }
                    }
            except:
                list_empty[f"sample_{samples[sample].id}"] = {
                        "id": samples[sample].id,
                        "index": samples[sample].index,
                        "identification": {
                                "id": samples[sample].identification.id,
                                "cage": samples[sample].identification.cage,
                            }
                    }
                list_empty[f"promedio_identification_{samples[sample].identification.id}"] = {
                    "identification":{
                        "id": samples[sample].identification.id,
                        "cage": samples[sample].identification.cage,
                            },
                }
                list_empty[f"promedio_center"] = {
                    "center": samples[sample].entryform.company_center.center.name if samples[sample].entryform.company_center != None else (samples[sample].entryform.company_laboratory if samples[sample].entryform.company_laboratory != None else ''),
                    }
                list_empty["porcentaje"] = []


        identifications = Identification.objects.filter(entryform__id=analysis.entryform.id)
        # Pasar identificaciones a dict con un for
        identifications_list = []
        for identification in identifications:
            identifications_dict = {
                "id": identification.id,
                "cage": identification.cage,
            }
            identifications_list.append(identifications_dict)


        sampleexamresultempty = []

        sampleexamresults = SampleExamResult.objects.filter(analysis__id=form_id)
        for sampleexamresult in sampleexamresults:
            sampleexamresultdict = {
                "value": sampleexamresult.value,
                "sample_id": sampleexamresult.sample_exam.sample.id,
                "result": sampleexamresult.result_organ.result.name,
            }
            sampleexamresultempty.append(sampleexamresultdict)

        analysisoptionalresult = AnalysisOptionalResult.objects.filter(analysis__id=form_id).first()
        if analysisoptionalresult is not None:
            result_name = analysisoptionalresult.resultOrgan.result.name
        else:
            result_name = "Nombre de resultado no encontrado"

        selected_options = ["Ameba", "Brookynella", "Amebas y otros parásitos"]
        is_selected = result_name in selected_options


        context["result_name"] = result_name
        context["is_selected"] = is_selected
        context["analysis"] = analysis
        context["samples"] = list_empty
        context["identifications"] = identifications_list
        context["entryform"] = entryForm
        context["sampleexamresults"] = sampleexamresultempty
        context["watersource"] = watersource.name
        context["type_of_water"] = type_of_water  # Add type of water to the context

        route = "app/consolidados/consolidado_SG/consolidado_sg.html"
        return render(request, route, context)

    @method_decorator(login_required)
    def post(self, request, form_id):
        analysis = AnalysisForm.objects.get(id=form_id)
        request = request.POST

        try:
            for key, value in request.items():
                keys = key[5:-1].split("-")

                if keys[0] == "mar_opcional":
                    result = Result.objects.get(name=value, type_result__id__in=[3,4,5,6,7])
                    resultOrgan = ResultOrgan.objects.get(organ__id=51, result= result)
                    
                    AnalysisOptionalResult.objects.update_or_create(analysis=analysis, defaults={'resultOrgan': resultOrgan})
                else:
                    sample_exam = SampleExams.objects.get(sample__id=keys[0], organ__id=51, exam=analysis.exam, stain=analysis.stain)
                    result = Result.objects.get(type_result__id__in=[3,4,5,6,7], name=keys[1])
                    resultorgan = ResultOrgan.objects.get(organ__id=51, result=result)
                    sampleexamresult, created = SampleExamResult.objects.update_or_create(sample_exam=sample_exam, result_organ=resultorgan, defaults={'value': value})
                    AnalysisSampleExmanResult.objects.update_or_create(analysis=analysis, sample_exam_result=sampleexamresult,  defaults={'created_at': datetime.now()})

            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({"ok": False, "error":e.__str__()})


class CONSOLIDADOS_GS(View):
    http_method_names = ["get", "post", "delete"]

    @method_decorator(login_required)
    def get(self, request, form_id):
        '''
        Only for pancreas, kidney, liver organs with ids (61, 86, 54) respectively
        '''
        organos = []
        samples = []
        sampleResults = []
        context = {
            "samples": [],
            "sampleExams": [],
            "diagnosticos": [],
            "results": [],
            "sampleResults": [],
        }

        analysis = AnalysisForm.objects.get(id=form_id)
        context["no_caso"] = analysis.entryform.no_caso
        context["exam_name"] = analysis.exam.name
        sampleExams = SampleExams.objects.filter(
            sample__entryform=analysis.entryform, exam=analysis.exam, stain=analysis.stain)
        sampleExamResults = SampleExamResult.objects.filter(analysis=analysis)

        context["sampleResults"] = serialize(
            'json', sampleExamResults, use_natural_foreign_keys=True, use_natural_primary_keys=True)

        for sampleExamResult in sampleExamResults:
            sampleResults.append(sampleExamResult.result_organ.id)
        sampleResults = list(set(sampleResults))

        context["results"] = sampleResults
        context["sampleExams"] = serialize(
            'json', sampleExams, use_natural_foreign_keys=True, use_natural_primary_keys=True)

        for sampleExam in sampleExams:
            organos.append(sampleExam.organ)
            sample = sampleExam.sample
            if sample not in samples:
                samples.append(sample)

        samples = sorted(samples, key=lambda x: x.index)
        context["samples"] = serialize(
            'json', samples, use_natural_foreign_keys=True, use_natural_primary_keys=True)
        organos = list(set(organos))

        results = ResultOrgan.objects.filter(organ__in=organos)

        for result in results:
            if "-" not in result.organ.name:
            # if result.result.type_result.id >= 8 and result.result.type_result.id <= 12:
                context["diagnosticos"].append({
                    "id": result.id,
                    "resultado": result.result,
                    "organo": result.organ.name
                })

        route = "app/consolidados/consolidado_GS/consolidados_gs.html"
        return render(request, route, context)

    @method_decorator(login_required)
    def post(self, request, form_id):

        analysis = AnalysisForm.objects.get(id=form_id)
        request = request.POST
        distribution = 0

        try:
            for key, value in request.items():
                keys = key[5:-1].split("%")

                if keys[0] == "distribution":
                    distribution = value
                else:
                    try:
                        sampleExam = SampleExams.objects.get(
                            sample__entryform=analysis.entryform, exam=analysis.exam, stain=analysis.stain, sample__index=keys[2], organ__name=keys[0])
                    except:
                        sampleExam = None
                    if not sampleExam:
                        sampleExam = SampleExams.objects.get(
                            sample__entryform=analysis.entryform, exam=analysis.exam, stain=analysis.stain, sample__index=keys[2])
                    sampleExamResult, created = SampleExamResult.objects.update_or_create(
                        sample_exam=sampleExam, result_organ_id=keys[1], defaults={'distribution': distribution, 'value': value})
                    analysisSampleExmanResult = AnalysisSampleExmanResult.objects.update_or_create(
                        analysis=analysis, sample_exam_result=sampleExamResult, defaults={'created_at': datetime.now()})

            return JsonResponse({'ok': True})
        except Exception as e:
            print(e)
            return JsonResponse({"ok": False, "error":e.__str__()})


# export excel consolidado
def export_consolidado(request, id):

    samples = []
    diagnostic = []
    headers = ["Órgano", "Diagnóstico", "Distribución"]

    analysis = AnalysisForm.objects.get(id=id)
    sampleExsamResults = SampleExamResult.objects.filter(analysis=analysis)
    sampleExams = SampleExams.objects.filter(
        sample__entryform=analysis.entryform, exam=analysis.exam, stain=analysis.stain)

    date = datetime.now().date().strftime("%d-%m-%Y")

    try:
        name_file = f'Consolidados_{analysis.entryform.no_caso}_{analysis.exam.name}_{date}.xlsx'
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Hoja 1")

        for sampleExam in sampleExams:
            sample = Sample.objects.get(id=sampleExam.sample.id)
            if sample not in samples:
                samples.append(sample)

        samples = sorted(samples, key=lambda x: x.index)

        for sample in samples:
            headers.append(sample.index)

        for col_num, header_title in enumerate(headers):
            worksheet.write(1, col_num+1, header_title)

        row_num = 2
        for sampleExsamResult in sampleExsamResults:
            if sampleExsamResult.result_organ.id not in diagnostic:
                worksheet.write(
                    row_num, 1, sampleExsamResult.result_organ.organ.name)
                worksheet.write(
                    row_num, 2, sampleExsamResult.result_organ.result.name)
                worksheet.write(row_num, 3, sampleExsamResult.distribution)
                diagnostic.append(sampleExsamResult.result_organ.id)
                row_num += 1

        diagnostic = []
        row_num = 1
        index = 0
        for sampleExsamResult in sampleExsamResults:
            col_num = 1
            if sampleExsamResult.result_organ.id not in diagnostic:
                diagnostic.append(sampleExsamResult.result_organ.id)
                row_num += 1

            index = headers.index(sampleExsamResult.sample_exam.sample.index)

            col_num += index
            worksheet.write(row_num, col_num, sampleExsamResult.value)

        workbook.close()
        output.seek(0)

        response = HttpResponse(output.read(
        ), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename='+name_file
        output.close()

        return response

    except Exception as e:
        print(e)
        return JsonResponse({"ok": False})


def analysis_report(request, id):
    analysis = Analysis.objects.get(id=id)

    try:
        report = AnalysisReport.objects.get(analysis=analysis)
    except ObjectDoesNotExist as e:
        report = AnalysisReport.objects.create(analysis=analysis, correlative=1)

    date = report.report_date.strftime('%d/%m/%Y') if report.report_date != None else ""
    methodology = "Sin metodología"
    if report.methodology != None:
        methodology = report.methodology.name

    data = {
        "report_date": date,
        "anamnesis": report.anamnesis,
        "comment": report.comment,
        "etiological_diagnostic": report.etiological_diagnostic,
        "images": [],
        "methodology":methodology,
        "correlative":report.correlative
    }

    images = ReportImages.objects.filter(
        analysis_report=report).order_by("index")

    for image in images:
        data["images"].append({
            "id": image.id,
            "image_name": image.imagen.name,
            "index": image.index,
            "size": image.size,
            "comment": image.comment,
        })

    return JsonResponse(data)


def analysisReport_addImage(request, id):
    request = request.POST
    index = request["index"]

    report = AnalysisReport.objects.get(analysis_id=id)
    image = ReportImages.objects.create(analysis_report=report, index=index)

    return JsonResponse({'id': image.id})


def analysisReport_deleteImage(request, id):

    data = QueryDict(request.body)
    new_order_data = data.getlist('new_order[]')

    ReportImages.objects.get(id=id).delete()
    new_order(new_order_data)

    return JsonResponse({'ok': True})


def analysisReport_save(request, id):
    request_files = request.FILES
    request_data = request.POST

    if "new_order[]" in request_data:
        new_order_data = request_data.getlist('new_order[]')
        new_order(new_order_data)
    else:
        report = AnalysisReport.objects.get(analysis_id=id)

        if "methodology" in request_data:
            if request_data["methodology"] != "" and request_data["methodology"] != "Sin metodología":
                methodology = Methodology.objects.get(id=int(request_data["methodology"]))
                report.methodology = methodology
                report.save()
            else:
                report.methodology = None
                report.save()

        report.report_date = datetime.strptime(
            request_data["report_date"], '%d/%m/%Y').date()
        report.anamnesis = request_data["anamnesis"]
        report.comment = request_data["comment"]
        report.correlative = int(request_data["correlative"])
        report.etiological_diagnostic = request_data["etiological_diagnostic"]
        report.save()

        for key in islice(request_data, 7, None):
            data = request_data[key]
            key = key.split("-")

            try:
                image = ReportImages.objects.get(id=key[1])
            except IndexError:
                # Handle the error, e.g., by logging it or setting `image` to None
                image = None
            if key[0] == "size":
                image.size = data
                image.save()

            if key[0] == "comment":
                image.comment = data
                image.save()

        for key, file in request_files.items():
            key = key.split("-")
            image = ReportImages.objects.get(id=key[1])
            image.imagen = file
            image.save()

    return JsonResponse({'ok': True})


def analysisReportMethology_save(request, id):
    request_data = request.POST
    report = AnalysisReport.objects.get(analysis_id=id)
    
    if "methodology" in request_data:
        if request_data["methodology"] != "" and request_data["methodology"] != "Sin metodología":
            methodology = Methodology.objects.get(id=int(request_data["methodology"]))
            report.methodology = methodology
            report.save()
            return JsonResponse({'name': methodology.name})
        else:
            report.methodology = None
            report.save()
            return JsonResponse({'name': "Sin metodología"})

def createMethodology(request):

    data = request.POST
    analysis_id = data.get("analysis_id")
    analysis = Analysis.objects.get(id=analysis_id)

    methodology = Methodology.objects.create(exam=analysis.exam)

    return JsonResponse({'id': methodology.id})

def saveMethodology(request,id):

    request_files = request.FILES
    request_data = request.POST

    if "new_order[]" in request_data:
        new_order_data = request_data.getlist('new_order[]')
        new_order_methodologyImages(new_order_data)
    else:
        methodology = Methodology.objects.get(id=id)
        methodology.name = request_data[f'methodologyName-{id}']
        methodology.description = request_data[f'methodologyText-{id}']
        methodology.save()

        for key in islice(request_data, 2, None):
            data = request_data[key]
            key = key.split("-")

            image = MethodologyImage.objects.get(id=key[1])
            if key[0] == "sizeMethodologyImage":
                image.size = data
                image.save()

            if key[0] == "commentImageMethodology":
                image.comment = data
                image.save()

        for key, file in request_files.items():
            key = key.split("-")
            image = MethodologyImage.objects.get(id=key[1])
            image.imagen = file
            image.save()

        return JsonResponse({"ok":True,'name': methodology.name})

    return JsonResponse({'ok': True})

def deleteMethodology(request,id):

    Methodology.objects.get(id=id).delete()

    return JsonResponse({'ok': True})

def createMethodologyImage(request,id):

    request = request.POST
    index = request["index"]

    methodology = Methodology.objects.get(id=id)
    image = MethodologyImage.objects.create(methodology=methodology, index=index)

    return JsonResponse({'id': image.id})

def methodology_deleteImage(request, id):

    data = QueryDict(request.body)
    new_order_data = data.getlist('new_order[]')

    MethodologyImage.objects.get(id=id).delete()
    new_order_methodologyImages(new_order_data)

    return JsonResponse({'ok': True})

def ExamMethodologys(request,id):

    exam = Analysis.objects.get(id=id).exam

    methodologys = exam.methodology_set.all()

    data = []

    for methodology in methodologys:
        methodology_data = {
            "id":methodology.id,
            "name":methodology.name,
            "description":methodology.description,
            "images":[]
        }

        for image in MethodologyImage.objects.filter(methodology=methodology).order_by("index"):
            image_data = {
                "id":image.id,
                "index":image.index,
                "size":image.size,
                "comment":image.comment,
                "name":image.imagen.name
            }
            methodology_data["images"].append(image_data)

        data.append(methodology_data)


    return JsonResponse({'data': data})

def new_order_methodologyImages(new_order):
    index = 0
    for image_order in new_order:
        index += 1
        image = MethodologyImage.objects.get(id=image_order)
        image.index = index
        image.save()

def new_order(new_order):
    index = 0
    for image_order in new_order:
        index += 1
        image = ReportImages.objects.get(id=image_order)
        image.index = index
        image.save()


def template_consolidados_HE(request, id):
    analysis = Analysis.objects.get(id=id)

    analysisSampleExmanResults = AnalysisSampleExmanResult.objects.filter(analysis_id=id)
    analysisSampleExmanResults = sorted(analysisSampleExmanResults, key=lambda x: x.sample_exam_result.result_organ.organ.name)

    analysis_report = AnalysisReport.objects.get(analysis_id=id)

    if analysis.research_set.all():
        research = True
    else:
        research = False

    no_caso = analysis.entryform.no_caso
    exam = analysis.exam.abbreviation
    no_reporte_date = analysis_report.report_date.strftime('%d%m%y') if analysis_report.report_date else "-"
    correlative = "{:02d}".format(analysis_report.correlative)
    no_reporte = f'{no_caso}_{exam}{correlative}_{no_reporte_date}'
    identifications = Identification.objects.filter(entryform__no_caso=no_caso).exclude(cage="Muestreo")

    identifications_group_empty = True
    for identification in identifications:
        if identification.group != "":
            identifications_group_empty = False

    samples = Sample.objects.filter(
        entryform=analysis.entryform
    ).values_list("id", flat=True).order_by('index')
    sampleExams = SampleExams.objects.filter(
          sample__in=samples, exam=analysis.exam, stain=analysis.stain
          ).order_by('sample__index')
    organs_count = samples_count = len(sampleExams)
    if analysis.exam.pricing_unit == 1:
            samples_count = organs_count
    else:
        sampleExams = SampleExams.objects.filter(
            sample__in=samples, exam=analysis.exam, stain=analysis.stain
        ).values_list("sample_id", flat=True).order_by('sample__index')
        samples_count = len(list(set(sampleExams)))

    sampleExams = SampleExams.objects.filter(sample__in=samples, exam=analysis.exam, stain=analysis.stain).order_by('sample__index')
    samples=[]
    identifications_filter = []
    for sampleExam in sampleExams:
        sample = Sample.objects.get(id=sampleExam.sample.id)

        identification = identifications.filter(id=sample.identification.id)[0]
        if identification not in identifications_filter and not any(iden.cage == identification.cage and iden.weight == identification.weight for iden in identifications_filter):
            identifications_filter.append(identification)

        if sample not in samples:
            samples.append(sample)

    samples = sorted(samples, key=lambda x: x.index)

    sample_charge = analysis.samples_charged if analysis.samples_charged != None and analysis.samples_charged > 0 else  samples_count

    reportImages = analysis_report.reportimages_set.all().order_by('index')

    pathologist = ""
    if analysis.patologo:
        pathologist = f"{analysis.patologo.first_name} {analysis.patologo.last_name}"

    if analysis_report.methodology != None:

        methodology = {
            "id":analysis_report.methodology.id,
            "name":analysis_report.methodology.name,
            "description":analysis_report.methodology.description,
            "image":[],
        }

        for image in MethodologyImage.objects.filter(methodology=analysis_report.methodology).order_by("index"):
            methodology_image = {
                "id":image.id,
                "comment":image.comment,
                "size":image.size,
                "url":image.imagen.url
            }
            methodology["image"].append(methodology_image)
    else:
        methodology = ""

    context = {
        "no_caso": no_caso,
        "no_reporte": no_reporte,
        "research": research,
        "pathologist": pathologist,
        "customer": analysis.entryform.customer.name,
        "center": analysis.entryform.company_center.center.name if analysis.entryform.company_center != None else ( analysis.entryform.company_laboratory if analysis.entryform.company_laboratory != None else '' ),
        "specie": analysis.entryform.specie.name,
        "larvalstage": analysis.entryform.larvalstage.name,
        "watersource": analysis.entryform.watersource.name,
        "identifications": identifications_filter,
        "identifications_group_empty":identifications_group_empty,
        "fecha_recepcion": analysis.created_at.strftime('%d-%m-%Y'),
        "fecha_informe": analysis_report.report_date.strftime('%d-%m-%Y'),
        "fecha_muestreo": analysis.entryform.sampled_at.strftime('%d-%m-%Y') if analysis.entryform.sampled_at != None else "-",
        "sample_charge": f'{sample_charge} {analysis.exam.name}',
        "anamnesis": analysis_report.anamnesis,
        "comment": analysis_report.comment,
        "etiological_diagnostic": analysis_report.etiological_diagnostic,
        "samples":samples,
        "reportImages": reportImages,
        "methodology":methodology,
    }

    return render(request, "app/consolidados/consolidado_HE/template_consolidado_HE.html", context)

def template_consolidados_HE_diagnostic(request, id):
    analysis = Analysis.objects.get(id=id)
    identifications_filter = []

    analysisSampleExmanResults = AnalysisSampleExmanResult.objects.filter(analysis_id=id)
    analysisSampleExmanResults = sorted(analysisSampleExmanResults, key=lambda x: x.sample_exam_result.result_organ.organ.name)

    identifications = Identification.objects.filter(entryform=analysis.entryform)

    samples = Sample.objects.filter(
        entryform=analysis.entryform
    ).values_list("id", flat=True)
    sampleExams = SampleExams.objects.filter(
          sample__in=samples, exam=analysis.exam, stain=analysis.stain
          ).order_by('sample__index')

    samples=[]
    for sampleExam in sampleExams:
            sample = Sample.objects.get(id=sampleExam.sample.id)
            identification = identifications.filter(id=sample.identification.id)[0]
            if identification not in identifications_filter:
                identifications_filter.append(identification)

            if sample not in samples:
                samples.append(sample)

    samples = sorted(samples, key=lambda x: x.index)

    context = {
        "calspan_identifications": len(samples),
        "identifications":[],
        "samples":samples,
        "diagnostics":[],
    }

    for identification in identifications_filter:
        colspan = len(identification.sample_set.all())

        samplesExams_identification = sampleExams.filter(sample__identification=identification)

        sample_count =[]
        for sampleExam in samplesExams_identification:
            sample_identification = Sample.objects.get(id=sampleExam.sample.id)
            if sample_identification not in sample_count:
                sample_count.append(sample_identification)

        sample_count = sorted(sample_count, key=lambda x: x.index)
        colspan = len(sample_count)

        context["identifications"].append({
            "cage":identification.cage,
            "colspan": colspan,
        })

    diagnostic=[]
    index=0
    samples_afected = 0
    total_samples = 0
    organ=[]
    organ_rowspan=1
    for analysisSampleExmanResult in analysisSampleExmanResults:
        if analysisSampleExmanResult.sample_exam_result.result_organ not in diagnostic:
            samples_afected = 0
            total_samples = 0
            if analysisSampleExmanResult.sample_exam_result.value > 0:
                samples_afected += 1

            index+=1
            diagnostic.append(analysisSampleExmanResult.sample_exam_result.result_organ)
            context["diagnostics"].append({
                "organ":analysisSampleExmanResult.sample_exam_result.result_organ.organ.name,
                "diagnostic": analysisSampleExmanResult.sample_exam_result.result_organ.result.name,
                "distribution": analysisSampleExmanResult.sample_exam_result.distribution,
                "results":{analysisSampleExmanResult.sample_exam_result.sample_exam.sample.index:analysisSampleExmanResult.sample_exam_result.value},
                "samples_afected": samples_afected,
            })

        else:
            if analysisSampleExmanResult.sample_exam_result.value > 0:
                samples_afected += 1

            context["diagnostics"][index-1]["results"][analysisSampleExmanResult.sample_exam_result.sample_exam.sample.index] = analysisSampleExmanResult.sample_exam_result.value
            context["diagnostics"][index-1]["samples_afected"] = samples_afected

        if analysisSampleExmanResult.sample_exam_result.value >= 0:
            total_samples += 1
            context["diagnostics"][index-1]["total_samples"] = total_samples

        if total_samples == 0:
            samples_afected_percentage = 0
        else:
            samples_afected_percentage = round((samples_afected*100)/total_samples)

        context["diagnostics"][index-1]["samples_afected_percentage"]=samples_afected_percentage

    organ = ""
    diagnostics=[]
    diagnostics_final=[]
    for i in range(len(context["diagnostics"])):
        if context["diagnostics"][i]["organ"] != organ:
            organ=context["diagnostics"][i]["organ"]
            diagnostics=[]
            diagnostics.append(context["diagnostics"][i])

            try:
                if context["diagnostics"][i+1]["organ"] != organ:
                    diagnostics_final.append(diagnostics[0])

            except IndexError:
                diagnostics_final.append(diagnostics[0])
        else:
            diagnostics.append(context["diagnostics"][i])

            try:
                if context["diagnostics"][i+1]["organ"] != organ:
                    diagnostics.sort(key=lambda e: e["samples_afected_percentage"],reverse=True)
                    for diagnostic in diagnostics:
                        diagnostics_final.append(diagnostic)

            except IndexError:
                diagnostics.sort(key=lambda e: e["samples_afected_percentage"],reverse=True)
                for diagnostic in diagnostics:
                    diagnostics_final.append(diagnostic)

    context["diagnostics"] = diagnostics_final

    organ = ""
    organ_rowspan=0
    for i in range(len(context["diagnostics"])):
        if context["diagnostics"][i]["organ"] != organ:
            organ=context["diagnostics"][i]["organ"]
            organ_rowspan=1

            try:
                if context["diagnostics"][i+1]["organ"] != organ:
                    context["diagnostics"][i-organ_rowspan+1]["organ_rowspan"] = organ_rowspan

            except IndexError:
                context["diagnostics"][i-organ_rowspan+1]["organ_rowspan"] = organ_rowspan

        else:
            organ_rowspan += 1

            try:
                if context["diagnostics"][i+1]["organ"] != organ:
                    context["diagnostics"][i-organ_rowspan+1]["organ_rowspan"] = organ_rowspan

            except IndexError:
                context["diagnostics"][i-organ_rowspan+1]["organ_rowspan"] = organ_rowspan

    for sample in samples:
        for diagnostics in context["diagnostics"]:
            if sample.index not in diagnostics["results"]:
                diagnostics["results"][sample.index] = -1

    for diagnostics in context["diagnostics"]:
        llaves_ordenadas = sorted(diagnostics["results"].keys())
        diagnostics["results"] = {k: diagnostics["results"][k] for k in llaves_ordenadas}

    return render(request, "app/consolidados/consolidado_HE/diagnostic_page.html", context)


def template_consolidados_HE_contraportada(request, id):
    analysis = Analysis.objects.get(id=id)
    contraportada = "/static/assets/images/contraportada.jpg"
    #if analysis.exam.id == 66:
    #    contraportada = "/static/assets/images/contraportada_HE Alevin.jpg"
    #else:
    #    contraportada = "/static/assets/images/contraportada_HE Vertebra.jpg"

    if analysis.exam.id == 67:
        contraportada = "/static/assets/images/contraportada.jpg"
    elif analysis.exam.id == 66:
        contraportada = "/static/assets/images/contraportada_HE Alevin.jpg"
    elif analysis.exam.id == 156:
        contraportada = "/static/assets/images/contraportada_HE Vertebra.jpg"

    context= {
        "contraportada":contraportada,
    }

    return render(request, "app/consolidados/contraportada.html",context)

@never_cache
def download_consolidados_HE(request, id):
    """Downloads a PDF file for a :model:`backend.Preinvoice` resume"""
    analysis = Analysis.objects.get(id=id)
    report = AnalysisReport.objects.get(analysis_id=id)
    no_caso = analysis.entryform.no_caso
    exam = analysis.exam.abbreviation
    date = report.report_date.strftime('%d%m%y') if report.report_date != None else " "
    correlative= "{:02d}".format(report.correlative)

    options = {
        "quiet": "",
        "page-size": "letter",
        "encoding": "UTF-8",
        "margin-top": "25mm",
        "margin-left": "5mm",
        "margin-right": "5mm",
        "margin-bottom": "20mm",
        "header-html": "https://storage.googleapis.com/vehice-media/header_HE.html",
        "header-spacing": 7,
        "header-font-size": 8,
        "footer-html": "https://storage.googleapis.com/vehice-media/footer_HE.html",
        "footer-spacing": 5,
    }

    url = reverse("template_consolidados_HE", kwargs={"id": id})
    pdf_vertical = pdfkit.from_url(settings.SITE_URL + url, False, options=options)

    options["orientation"] = "Landscape"
    url = reverse("template_consolidados_HE_diagnostic", kwargs={"id": id})
    pdf_horizontal = pdfkit.from_url(settings.SITE_URL + url, False, options=options)

    options = {
        "quiet": "",
        "page-size": "letter",
        "encoding": "UTF-8",
        "margin-top": "0mm",
        "margin-left": "0mm",
        "margin-right": "0mm",
        "margin-bottom": "0mm",
    }

    url = reverse("template_consolidados_HE_contraportada", kwargs={"id": id})
    pdf_contraportada = pdfkit.from_url(settings.SITE_URL + url, False, options=options)

    pdf_vertical = io.BytesIO(pdf_vertical)
    pdf_horizontal = io.BytesIO(pdf_horizontal)
    pdf_contraportada = io.BytesIO(pdf_contraportada)

    pdf_vertical_reader = PdfReader(pdf_vertical)
    pdf_horizontal_reader = PdfReader(pdf_horizontal)
    pdf_contraportada_reader = PdfReader(pdf_contraportada)
    pdf_combinado_writer = PdfWriter()

    index_vertical = 0
    pagina_vertical = pdf_vertical_reader.pages
    pdf_combinado_writer.add_page(pagina_vertical[index_vertical])

    if report.methodology != None:
        index_vertical += 1
        pdf_combinado_writer.add_page(pagina_vertical[index_vertical])

    for page in pdf_horizontal_reader.pages:
        pagina_horizontal = page
        pdf_combinado_writer.add_page(pagina_horizontal)

    index_vertical += 1
    for page in pdf_vertical_reader.pages[index_vertical:]:
        pdf_combinado_writer.add_page(page)

    pdf_combinado_writer.add_page(pdf_contraportada_reader.pages[0])

    pdf_combinado = io.BytesIO()

    pdf_combinado_writer.write(pdf_combinado)

    datos_pdf_combinado = pdf_combinado.getvalue()

    pdf_vertical.close()
    pdf_horizontal.close()
    pdf_combinado.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline;filename=" + f"{no_caso}_{exam}{correlative}_{date}.pdf"
    response.write(datos_pdf_combinado)

    return response


# ======================================
# SCOREGILL
# 10/05/2024
# Creado y elaborado por Jaime Herrera y Luis Urrutia
# ======================================

def template_consolidados_SG(request, id):

    analysis = Analysis.objects.get(id=id)

    analysisSampleExmanResults = AnalysisSampleExmanResult.objects.filter(analysis_id=id)
    analysisSampleExmanResults = sorted(analysisSampleExmanResults, key=lambda x: x.sample_exam_result.result_organ.organ.name)

    analysis_report = AnalysisReport.objects.get(analysis_id=id)

    if analysis.research_set.all():
        research = True
    else:
        research = False

    no_caso = analysis.entryform.no_caso
    exam = analysis.exam.abbreviation
    no_reporte_date = analysis_report.report_date.strftime('%d%m%y') if analysis_report.report_date else "-"
    correlative = "{:02d}".format(analysis_report.correlative)
    no_reporte = f'{no_caso}_{exam}{correlative}_{no_reporte_date}'
    identifications = Identification.objects.filter(entryform__no_caso=no_caso).exclude(cage="Muestreo")

    identifications_group_empty = True
    for identification in identifications:
        if identification.group != "":
            identifications_group_empty = False

    samples = Sample.objects.filter(
        entryform=analysis.entryform
    ).values_list("id", flat=True)
    sampleExams = SampleExams.objects.filter(
          sample__in=samples, exam=analysis.exam, stain=analysis.stain
          )
    organs_count = samples_count = len(sampleExams)
    if analysis.exam.pricing_unit == 1:
            samples_count = organs_count
    else:
        sampleExams = SampleExams.objects.filter(
            sample__in=samples, exam=analysis.exam, stain=analysis.stain
        ).values_list("sample_id", flat=True)
        samples_count = len(list(set(sampleExams)))

    sampleExams = SampleExams.objects.filter(sample__in=samples, exam=analysis.exam, stain=analysis.stain)
    samples=[]

    identifications_filter = []
    for sampleExam in sampleExams:
        sample = Sample.objects.get(id=sampleExam.sample.id)

        identification = identifications.filter(id=sample.identification.id)[0]
        if identification not in identifications_filter and not any(iden.cage == identification.cage and iden.weight == identification.weight for iden in identifications_filter):
            identifications_filter.append(identification)

        if sample not in samples:
            samples.append(sample)

    samples = sorted(samples, key=lambda x: x.index)

    sample_charge = analysis.samples_charged if analysis.samples_charged != None and analysis.samples_charged > 0 else  samples_count

    reportImages = analysis_report.reportimages_set.all().order_by('index')

    pathologist = ""
    if analysis.patologo:
        pathologist = f"{analysis.patologo.first_name} {analysis.patologo.last_name}"

    if analysis_report.methodology != None:

        methodology = {
            "id":analysis_report.methodology.id,
            "name":analysis_report.methodology.name,
            "description":analysis_report.methodology.description,
            "image":[],
        }

        for image in MethodologyImage.objects.filter(methodology=analysis_report.methodology).order_by("index"):
            if image.imagen:  # Check if the image file exists
                image_url = image.imagen.url
            else:
                image_url = None  # Or a default placeholder image URL

            methodology_image = {
                "id":image.id,
                "comment":image.comment,
                "size":image.size,
                "url":image_url
            }
            methodology["image"].append(methodology_image)
    else:
        methodology = ""

    fecha_informe = analysis_report.report_date.strftime('%d-%m-%Y') if analysis_report.report_date else "-"


    context = {
        "no_caso": no_caso,
        "no_reporte": no_reporte,
        "research": research,
        "pathologist": pathologist,
        "customer": analysis.entryform.customer.name,
        "center": analysis.entryform.company_center.center.name if analysis.entryform.company_center != None else ( analysis.entryform.company_laboratory if analysis.entryform.company_laboratory != None else '' ),
        "specie": analysis.entryform.specie.name,
        "larvalstage": analysis.entryform.larvalstage.name,
        "watersource": analysis.entryform.watersource.name,
        "identifications": identifications_filter,
        "identifications_group_empty":identifications_group_empty,
        "fecha_recepcion": analysis.created_at.strftime('%d-%m-%Y'),
        "fecha_informe": fecha_informe,  # Use the variable with the conditional check
        "fecha_muestreo": analysis.entryform.sampled_at.strftime('%d-%m-%Y') if analysis.entryform.sampled_at != None else "-",
        "sample_charge": f'{sample_charge} {analysis.exam.name}',
        "anamnesis": analysis_report.anamnesis,
        "comment": analysis_report.comment,
        "etiological_diagnostic": analysis_report.etiological_diagnostic,
        "samples":samples,
        "reportImages": reportImages,
        "methodology":methodology,
    }


    return render(request, "app/consolidados/consolidado_SG/template_consolidado_SG.html", context)

def calculate_score_row_haciaabajo(sample_values):
    category_sums = {}
    exclude_categories = {'Espongeosis', 'Necrosis', 'Degeneración Ballonizante', 'Exfoliación'}

    for key, value in sample_values.items():
        _, category = key.split('-')
        if category not in exclude_categories:
            if category not in category_sums:
                category_sums[category] = 0
            category_sums[category] += value

    return category_sums

def calculate_averages(samples, sample_values):
    averages_data = defaultdict(lambda: defaultdict(lambda: {'sum': 0, 'count': 0}))

    for sample in samples:
        if 'id' not in sample or 'identification' not in sample:
            continue

        identification_id = sample['identification']['id']
        for key, value in sample_values.items():
            if str(sample['id']) in key:
                category = key.split('-', 1)[1]
                averages_data[identification_id][category]['sum'] += value
                averages_data[identification_id][category]['count'] += 1

    averages = defaultdict(dict)
    for identification_id, categories in averages_data.items():
        for category, data in categories.items():
            if data['count'] > 0:
                averages[identification_id][category] = round(data['sum'] / data['count'], 2)
            else:
                averages[identification_id][category] = None
    return averages

def calculate_score_sums_by_cage(sample_values):
    cage_sums = {}
    exclude_categories = {'Espongeosis', 'Necrosis', 'Degeneración Ballonizante', 'Exfoliación'}

    # Assuming sample_values keys are in the format "{cage_id}-{category}"
    for key, value in sample_values.items():
        cage_id, category = key.split('-')
        if category in exclude_categories:
            logger.debug(f"Skipping {category} for cage {cage_id}")
            continue  # Skip this iteration if the category should be excluded

        if cage_id not in cage_sums:
            cage_sums[cage_id] = 0
        cage_sums[cage_id] += value
        # Log each addition
        # logger.debug(f"Adding {value} to cage {cage_id}. Total now: {cage_sums[cage_id]}")

    return cage_sums

def calculate_sums_by_identification(averages, exclude_categories):
    identification_sums = {}
    for identification_id, scores in averages.items():
        valid_scores = [score for category, score in scores.items() if category not in exclude_categories]
        if valid_scores:  # Ensure there are scores to sum
            total_score = sum(valid_scores)
            identification_sums[identification_id] = total_score
            logger.debug(f"Calculated sum for identification {identification_id}: {total_score}")
        else:
            identification_sums[identification_id] = 0
            logger.debug(f"No valid scores for identification {identification_id}. Set sum to 0.")

    return identification_sums

def calculate_averages_by_category_and_identification(scores):
    # Structure to hold the sums and counts for averaging
    category_data = defaultdict(lambda: {'sum': 0, 'count': 0})

    # Iterate over all scores and sum them by category across all identifications
    for identification_id, categories in scores.items():
        for category, score in categories.items():
            category_data[category]['sum'] += score
            category_data[category]['count'] += 1

    # Calculate averages for each category
    category_averages = {}
    for category, data in category_data.items():
        if data['count'] > 0:
            average_score = data['sum'] / data['count']
            category_averages[category] = average_score
        else:
            category_averages[category] = 0  # or None if you prefer

    return category_averages

def template_consolidados_SG_diagnostic(request, id):
    context = {
        "samples": [],
        "identifications": [],
        "Entryform":'',
    }

    analysis = AnalysisForm.objects.get(id=id)
    samples_id =SampleExams.objects.filter(sample__entryform__id=analysis.entryform.id, exam=analysis.exam, organ_id = 51).values_list('sample',flat=True)

    samples = list(Sample.objects.filter(id__in=samples_id).order_by("index"))

    identifications = []
    for sample in samples:
        if sample.identification not in identifications:
            identifications.append(sample.identification)

    list_empty = dict()

    entryForm = EntryForm.objects.get(id=analysis.entryform.id)

    results= Result.objects.filter(type_result__id__in=[3,4,5,6,7])
    for result in results:
            context[result.name] =  result.id

    for sample in range(len(samples)):
            try:
                if samples[sample].identification.id != samples[sample+1].identification.id:
                    list_empty[f"sample_{samples[sample].id}"] = {
                        "id": samples[sample].id,
                        "index": samples[sample].index,
                        "identification": {
                                "id": samples[sample].identification.id,
                                "cage": samples[sample].identification.cage,
                            }
                    }

                    prom={
                        "identification": {
                                "id": samples[sample].identification.id,
                                "cage": samples[sample].identification.cage,
                            }
                    }
                    list_empty[f"promedio_identification_{samples[sample].identification.id}"] = prom
                else:
                    list_empty[f"sample_{samples[sample].id}"] = {
                        "id": samples[sample].id,
                        "index": samples[sample].index,
                        "identification": {
                                "id": samples[sample].identification.id,
                                "cage": samples[sample].identification.cage,
                            }
                    }
            except:
                list_empty[f"sample_{samples[sample].id}"] = {
                        "id": samples[sample].id,
                        "index": samples[sample].index,
                        "identification": {
                                "id": samples[sample].identification.id,
                                "cage": samples[sample].identification.cage,
                            }
                    }
                list_empty[f"promedio_identification_{samples[sample].identification.id}"] = {
                    "identification":{
                        "id": samples[sample].identification.id,
                        "cage": samples[sample].identification.cage,
                            },
                }
                list_empty[f"promedio_center"] = {
                    "center":samples[sample].entryform.center,
                    }
                list_empty["porcentaje"] = []

    # Pasar identificaciones a dict con un for
    identifications_list = []
    for identification in identifications:
        identifications_dict = {
            "id": identification.id,
            "cage": identification.cage,
        }
        identifications_list.append(identifications_dict)

        sampleexamresultempty = []

        sampleexamresults = SampleExamResult.objects.filter(analysis__id=id)

        for sampleexamresult in sampleexamresults:
            sampleexamresultdict = {
                "value": sampleexamresult.value,
                "sample_id": sampleexamresult.sample_exam.sample.id,
                "result": sampleexamresult.result_organ.result.name,
            }
            sampleexamresultempty.append(sampleexamresultdict)

        analysisoptionalresult = AnalysisOptionalResult.objects.filter(analysis__id=id).first()
        if analysisoptionalresult is not None:
            result_name = analysisoptionalresult.resultOrgan.result.name
        else:
            result_name = "Nombre de resultado no encontrado"

    # Prepare a structured data representation for the template
    sample_values = {}
    for sampleexamresult in sampleexamresults:
        key = f"{sampleexamresult.sample_exam.sample.id}-{sampleexamresult.result_organ.result.name}"
        sample_values[key] = sampleexamresult.value

    exclude_categories = {'Espongeosis', 'Necrosis', 'Degeneración Ballonizante', 'Exfoliación'}

    # Initialize a dictionary to store the count of non-zero values and total counts
    category_counts = {}
    for sample in samples:
        for key, value in sample_values.items():
            sample_id, category = key.split('-')
            if sample_id == str(sample.id):  # Corrected line
                if category not in category_counts:
                    category_counts[category] = {'non_zero': 0, 'total': 0}
                category_counts[category]['total'] += 1
                if value > 0:
                    category_counts[category]['non_zero'] += 1

       # Calculate percentages
    category_percentages = {}
    for category, counts in category_counts.items():
        if counts['total'] > 0:
            percentage = (counts['non_zero'] / counts['total']) * 100
        else:
            percentage = 0
        category_percentages[category] = round(percentage, 2)  # Round to two decimal places

    # Calculate score sums
    cage_sums = calculate_score_sums_by_cage(sample_values)
    averages = calculate_averages(list(list_empty.values()), sample_values)
    identification_sums = calculate_sums_by_identification(averages, exclude_categories)
    identification_averages = calculate_averages_by_category_and_identification(averages)

    watersource = WaterSource.objects.filter(name=analysis.entryform.watersource.name).first()

    if watersource:
        type_of_water = watersource.type_of_water
    else:
        type_of_water = "Unknown"  # Default or error handling case

    context["result_name"] = result_name
    context["analysis"] = analysis
    context["samples"] = list_empty
    context["identifications"] = identifications_list
    context["entryform"] = entryForm
    context["sample_values"] = sample_values
    context["sampleexamresults"] = sampleexamresultempty
    context["averages"] = averages
    context["cage_sums"] = cage_sums
    context["identification_sums"] = identification_sums
    context["identification_averages"] = identification_averages
    context['category_percentages'] = category_percentages
    context["watersource"] = analysis.entryform.watersource.name
    context["type_of_water"] = type_of_water  # Add type of water to the context

    return render(request, "app/consolidados/consolidado_SG/diagnostic_page_sg.html", context)

def template_consolidados_SG_contraportada(request, id):

    #contraportada = "/static/assets/images/contraportada_score_gill.jpg"
    #contraportada = "/static/assets/images/contraportada.jpg"
    contraportada = "/static/assets/images/contraportada_SG.jpg"


    context= {
        "contraportada":contraportada,
    }

    return render(request, "app/consolidados/contraportada.html",context)

@never_cache
def download_consolidados_SG(request, id):


    """Downloads a PDF file for a :model:`backend.Preinvoice` resume"""
    try:
        # Inside your download_consolidados_SG view
        table_html1 = request.POST.get('tableHTML1', '')
        table_html2 = request.POST.get('tableHTML2', '')


        analysis = Analysis.objects.get(id=id)

        chart_images_base64 = {}
        for chart_id in ['myChart', 'myMixedChart', 'myMixedChart2', 'myBoxChart','scoreDistributionChart']:
            chart_image_file = request.FILES.get(chart_id, None)
            if chart_image_file:
                chart_image_data = chart_image_file.read()
                chart_images_base64[chart_id] = base64.b64encode(chart_image_data).decode('utf-8')


        report = AnalysisReport.objects.get(analysis_id=id)
        no_caso = analysis.entryform.no_caso
        exam = analysis.exam.abbreviation
        date = report.report_date.strftime('%d%m%y') if report.report_date != None else " "
        correlative= "{:02d}".format(report.correlative)
        
        options = {
            "quiet": "",
            "page-size": "letter",
            "encoding": "UTF-8",
            "margin-top": "25mm",
            "margin-left": "5mm",
            "margin-right": "5mm",
            "margin-bottom": "25mm",
            "header-html": "https://storage.googleapis.com/vehice-media/header_HE.html",
            "header-spacing": 7,
            "header-font-size": 8,
            "footer-html": "https://storage.googleapis.com/vehice-media/footer_HE.html",
            "footer-spacing": 5,
            "dpi": "600",
            'image-quality': "100",
        }


        url = reverse("template_consolidados_SG", kwargs={"id": id})
        pdf_vertical = pdfkit.from_url(settings.SITE_URL + url, False, options=options)

        options["orientation"] = "Landscape"
        url = reverse("template_consolidados_SG_diagnostic", kwargs={"id": id})
        pdf_horizontal = pdfkit.from_url(settings.SITE_URL + url, False, options=options)

        # Set the options for the graph section with appropriate margins
        options = {
                    "quiet": "",
                    "page-size": "letter",
                    "encoding": "UTF-8",
                    "margin-top": "20mm",
                    "margin-bottom": "20mm",
                    "header-html": "https://storage.googleapis.com/vehice-media/header_HE.html",
                    "header-spacing": 6,  # Espacio debajo del encabezado
                    #"footer-center": "Página [page] de [topage]",
                    "footer-html": "https://storage.googleapis.com/vehice-media/footer_HE.html",
                    "margin-left": "0mm",
                    "margin-right": "0mm",
                    "zoom": 1,  # Adjust as necessary
                    "dpi": "600",  # Adjust as necessary
                    'image-quality': "100",
                # Include any other necessary options here
            }

        context = {
            'chart_images': chart_images_base64,
            'table_html1': table_html1,
            'table_html2': table_html2,
            # Include other context variables as needed
        }


        # Define descriptions for each chart
        descriptions = [
            "Score general de salud branquial (promedio).",
            "Score de hallazgos principales.",
            "Score de criterio auxiliar.",
            "Distribución muestreal score branquial (0 – 24).",
            "Distribución porcentual de score gill (0 – 24)."
        ]


            # CHARTS TO PDF
        graph_html_content = render_to_string(
            "app/consolidados/consolidado_SG/consolidado_graphs.html",
            {
                'chart_images': chart_images_base64,
                'table_html1': table_html1,
                'table_html2': table_html2,
                'descriptions': descriptions,  # Pass descriptions to the template
                # Include other context variables as needed
                'narrow_first_column': True,  # Add a flag to conditionally include the CSS
            }
        )
        pdf_graph_section = pdfkit.from_string(graph_html_content, False, options=options)


        options = {
            "quiet": "",
            "page-size": "letter",
            "encoding": "UTF-8",
            "margin-top": "0mm",
            "margin-left": "0mm",
            "margin-right": "0mm",
            "margin-bottom": "0mm",
        }

        url = reverse("template_consolidados_SG_contraportada", kwargs={"id": id})  ##esta con la normal, poner scoregill
        pdf_contraportada = pdfkit.from_url(settings.SITE_URL + url, False, options=options)


        # Convert the PDF outputs from pdfkit to BytesIO objects

        pdf_vertical = io.BytesIO(pdf_vertical)
        pdf_horizontal = io.BytesIO(pdf_horizontal)
        pdf_graph_section = io.BytesIO(pdf_graph_section)
        pdf_contraportada = io.BytesIO(pdf_contraportada)


        # Initialize PdfReader objects for each PDF section

        pdf_vertical_reader = PdfReader(pdf_vertical)
        pdf_horizontal_reader = PdfReader(pdf_horizontal)
        pdf_contraportada_reader = PdfReader(pdf_contraportada)
        pdf_graph_section_reader = PdfReader(pdf_graph_section)

        # Initialize a PdfWriter for the combined PDF
        pdf_combinado_writer = PdfWriter()

        index_vertical = 0
        pagina_vertical = pdf_vertical_reader.pages
        pdf_combinado_writer.add_page(pagina_vertical[index_vertical])

        if report.methodology != None:
            index_vertical += 1
            pdf_combinado_writer.add_page(pagina_vertical[index_vertical])

        for page in pdf_horizontal_reader.pages:
            pagina_horizontal = page
            pdf_combinado_writer.add_page(pagina_horizontal)

        # Add the graph section
        # Assuming the graph section is a single page. If more, loop through reader_graph_section.pages
        for page in pdf_graph_section_reader.pages:
            pdf_combinado_writer.add_page(page)

        index_vertical += 1
        for page in pdf_vertical_reader.pages[index_vertical:]:
            pdf_combinado_writer.add_page(page)

        pdf_combinado_writer.add_page(pdf_contraportada_reader.pages[0])

        pdf_combinado = io.BytesIO()

        pdf_combinado_writer.write(pdf_combinado)

        datos_pdf_combinado = pdf_combinado.getvalue()

        pdf_vertical.close()
        pdf_horizontal.close()
        pdf_combinado.close()
        pdf_contraportada.close()
        pdf_graph_section.close()

        if pdf_combinado:
            response = HttpResponse(content_type="application/pdf")
            response["Content-Disposition"] = "inline;filename=" + f"{no_caso}_{exam}{correlative}_{date}.pdf"
            response.write(datos_pdf_combinado)
            return response
        else:
            return HttpResponse("Error generating PDF", status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)