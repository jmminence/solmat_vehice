import json
from datetime import date

import numpy as np
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from accounts.models import Area, UserArea
from backend.models import AnalysisTimes, SampleExams
from report.models import Analysis
from report.services import get_holidays


def get_pathologists(user):
    """Returns a queryset of :model:`User`.
    This queryset filter the User model according to it's profile, where a profile id of 4 and 5
    indicates a Pathologist, the userprofile also includes a boolean check for wether that user is
    pathologists, in cases where a user doesn't have the profile of a pathologists but it should be
    considered as one.
    It also filters for an Area's Lead to be able to see al Pathologists under their Area.
    """
    pathologists = User.objects.filter(
        Q(userprofile__profile_id__in=(4, 5)) | Q(userprofile__is_pathologist=True)
    )

    if not user.userprofile.profile_id in (1, 2):
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

    return pathologists


def get_areas(user):
    """Returns a queryset of :model:`accounts.Area`.
    This queryset filters the Area model according to the current user, taking into consideration
    if the current user is an Area's lead or if it's an admin role user.
    """
    assigned_areas = UserArea.objects.filter(user=user).values_list("area", flat=True)

    areas = Area.objects.filter(id__in=assigned_areas)

    if user.userprofile.profile_id in (1, 2):
        areas = Area.objects.all()

    return areas


@login_required
def service_report(request):
    """Displays multiple tables and charts to generate reportability.
    This is cattered for Pathologists Users, where they can see their
    pending work.
    """
    areas = get_areas(request.user)
    pathologists = get_pathologists(request.user)

    return render(
        request,
        "pathologist/service.html",
        {"pathologists": pathologists, "areas": areas},
    )


@login_required
def services_table(request):
    """
    Returns a JSON contaning preformatted data to be display in
    a DataTable filtered by unstarted services.
    """

    draw = int(request.GET.get("draw"))
    length = int(request.GET.get("length"))
    search = request.GET.get("search[value]")
    start = int(request.GET.get("start")) + 1

    pathologist = request.GET.get("pathologists")
    area = request.GET.get("areas")

    table = request.GET.get("table")

    if area:
        area = area.split(";")
        pathologist = UserArea.objects.filter(area_id__in=area).values_list(
            "user_id", flat=True
        )
    elif pathologist:
        pathologist = pathologist.split(";")
    else:
        pathologist = get_pathologists(request.user)


    # Assuming you want to exclude exams with certain names
    excluded_exam_name = "MATERIALES Y OTROS"

    services = Analysis.objects.filter(
        Q(manual_cancelled_date__isnull=True) | Q(forms__cancelled=False),
        Q(manual_closing_date__isnull=True) | Q(forms__form_closed=False),
        patologo__in=pathologist,
    ).exclude(exam__name=excluded_exam_name).only(
        "id", "entryform_id", "exam_id", "comments", "created_at",
        "patologo_id", "stain_id",
    ).select_related(
        "entryform__customer", "patologo", "stain", "exam",
    ).prefetch_related(
        "entryform__customer",
    )

    # The table parameter dictates which "state" filter will be applied
    # whereas `pending` it's for non started services, `reading` for
    # started and unfinished services, `reviewing` for
    # started and finished services but unclosed.
    if table == "PENDING":
        services = (
            services.filter(
                pre_report_started=False,
                pre_report_ended=False,
            )
            .order_by("created_at")
        )
    elif table == "READING":
        services = (
            services.filter(
                pre_report_started=True,
                pre_report_ended=False,
            )
            .order_by("created_at")
        )
    elif table == "REVIEWING":
        services = (
            services.filter(
                pre_report_started=True,
                pre_report_ended=True,
            )
            .order_by("created_at")
        )

    if search:
        services = services.filter(
            Q(entryform__no_caso__icontains=search)
            | Q(entryform__customer__name__icontains=search)
            | Q(exam__name__icontains=search)
            | Q(stain__abbreviation__icontains=search)
        )

    services_paginator = Paginator(services, length)

    context_response = {
        "draw": draw + 1,
        "recordsTotal": services.count(),
        "recordsFiltered": services_paginator.count,
        "data": [],
    }

    for page in services_paginator.page_range:
        page_start = services_paginator.get_page(page).start_index()
        if page_start == start:
            services_page = services_paginator.get_page(page).object_list
            for service in services_page:
                
                deadline = AnalysisTimes.objects.filter(analysis_id=service.id, type_deadline_id=3).last()
                if not deadline:
                    deadline = AnalysisTimes.objects.filter(analysis_id=service.id, type_deadline_id=2).last()
                if not deadline:
                    deadline = AnalysisTimes.objects.filter(analysis_id=service.id, type_deadline_id=1).last()

                samples_count = SampleExams.objects.filter(
                    exam=service.exam,
                    stain=service.stain,
                    sample__entryform=service.entryform,
                ).count()

                row = {
                    "case": model_to_dict(
                        service.entryform, fields=["no_caso", "created_at"]
                    ),
                    "customer": model_to_dict(service.entryform.customer, exclude=['center']) if service.entryform.customer else None,
                    "exam": model_to_dict(service.exam) if service.exam else None,
                    "stain": model_to_dict(service.stain) if service.stain else None,
                    "pathologist": model_to_dict(
                        service.patologo, fields=["first_name", "last_name"]
                    ) if service.patologo else None,
                    "service": model_to_dict(
                        service,
                        exclude=["external_reports", "service_comments", "files", "samples"],
                    ) if service else None,
                    "samples_count": samples_count,
                    "deadline":deadline.deadline
                    if deadline else service.assignment_deadline,
                }

                context_response["data"].append(row)

            # Row data should only include current page
            break


    return JsonResponse(context_response)


class EfficiencyView(View):
    @method_decorator(login_required)
    def get(self, request):
        """
        Displays multiples tables detailing :model:`backend.Analysis` grouped
        by their state.
        """
        assigned_areas = UserArea.objects.filter(user=request.user).values_list(
            "area", flat=True
        )

        areas = Area.objects.filter(id__in=assigned_areas)
        if request.user.userprofile.profile_id in (1, 2):
            areas = Area.objects.all()

        return render(
            request,
            "pathologist/efficiency.html",
            {
                "pathologists": get_pathologists(request.user),
                "areas": areas,
            },
        )
    def post(self, request):
        """
        Returns a JSON containing detailed information list of :model:`backend.Analysis`
        filtered by request parameters of `date_start`, `date_end`, and `pathologist`.
        """
        body = json.loads(request.body)
        pathologist = (
            int(body["user_id"])
            if str(body["user_id"]).isnumeric()
            else get_pathologists(request.user).values_list("id", flat=True)
        )
        area = int(body["area_id"]) if str(body["area_id"]).isnumeric() else 0
        date_start = body["date_start"]
        date_end = body["date_end"]

        date_start = (
            (date.today() + relativedelta(months=-5)) if not date_start else date_start
        )
        
        date_end = (date.today()) if not date_end else date_end

        reports = Analysis.objects.filter(
            Q(manual_cancelled_date__isnull=True) | Q(forms__cancelled=False),
            Q(manual_closing_date__isnull=False) | Q(forms__form_closed=True),
            created_at__gte=date_start,
            created_at__lte=date_end,
        ).prefetch_related("entryform", "patologo", "stain", 'forms', 'exam', 'entryform__customer')

        if pathologist and pathologist > 0:
            reports = reports.filter(patologo_id=pathologist)
        else:
            reports = reports.filter(
                patologo_id__in=get_pathologists(request.user).values_list(
                    "id", flat=True
                )
            )

        if area and area > 0:
            users = area.users
            reports = reports.filter(patologo_id__in=users)

        context = []
        
        for report in reports:
            user = None
            if report.patologo is not None:
                user = report.patologo
            try:
                context.append(
                    {
                        "report": model_to_dict(
                            report,
                            fields=[
                                "assignment_deadline",
                                "manual_cancelled_date",
                                "manual_closing_date",
                                "assignment_done_at",
                                "pre_report_ended",
                                "pre_report_ended_at",
                                "pre_report_started",
                                "pre_report_started_at",
                                "report_code",
                                "score_diagnostic",
                                "score_report",
                                "patologo",
                            ],
                        ),
                        "case": model_to_dict(
                            report.entryform,
                            fields=[
                                "created_at",
                                "no_caso",
                            ],
                        ),
                        "customer": model_to_dict(
                            report.entryform.customer,
                            fields=[
                                "name",
                            ],
                        ) if report.entryform.customer else None,
                        "exam": model_to_dict(
                            report.exam, fields=["name", "pathologist_assignment"], exclude=['center']
                        ) if report.exam else None,
                        "user": model_to_dict(user, fields=["first_name", "last_name"]),
                        "stain": model_to_dict(
                            report.stain if report.stain else None, fields=["name", "abbreviation"]
                        ),
                        "samples": report.exam.sampleexams_set.filter(
                            sample__entryform_id=report.entryform_id
                        ).count(),
                        "workflow": model_to_dict(
                            list(report.forms.all())[0],
                            fields=[
                                "form_closed",
                                "cancelled",
                                "closed_at",
                                "cancelled_at",
                            ],
                        ),
                    }
                )
            except AttributeError:
                continue
        
        return HttpResponse(
            json.dumps(context, cls=DjangoJSONEncoder), content_type="application/json"
        )


class ControlView(View):
    def get(self, request):
        """Displays multiple tables and charts to generate reportability.
        This is cattered for Administration Users, where they can see their
        current workload.
        """
        areas = get_areas(request.user)
        pathologists = get_pathologists(request.user)

        return render(
            request,
            "control/home.html",
            {"pathologists": pathologists, "areas": areas},
        )


@login_required
def control_charts(request):
    date_start = request.GET.get("date_start")
    date_start = (
        (date.today() + relativedelta(weeks=-4)) if not date_start else date_start
    )
    date_end = request.GET.get("date_end")
    date_end = date.today() if not date_end else date_end

    pathologist = request.GET.get("pathologists")
    area = request.GET.get("areas")

    if area:
        area = area.split(";")
        pathologist = UserArea.objects.filter(area_id__in=area).values_list(
            "user_id", flat=True
        )
    elif pathologist:
        pathologist = pathologist.split(";")
    else:
        pathologist = get_pathologists(request.user)

    analysis_filter = Analysis.objects.filter(
        Q(manual_cancelled_date__isnull=True) | Q(forms__cancelled=False),
        exam__pathologists_assignment=True,
        patologo__in=pathologist,
        pre_report_started=True,
        pre_report_ended_at__gte=date_start,
    )

    analysis_data = []

    holidays = np.array(get_holidays(), dtype="datetime64")

    for analysis in analysis_filter:
        analysis_data.append(
            {
                "organs": analysis.organs_count,
                "user": analysis.pathologist_name,
                "exam": analysis.exam.name,
                "date": analysis.pre_report_ended_at,
                "week": analysis.week_finished,
                "days_processing": analysis.days_processing(holidays),
                "days_assigning": analysis.days_assigning(holidays),
                "days_waiting": analysis.days_waiting(holidays),
                "days_reading": analysis.days_reading(holidays),
            }
        )

    return JsonResponse(analysis_data, safe=False)


@login_required
def response_time_charts(request):
    date_start = request.GET.get("date_start")
    date_start = (
        (date.today() + relativedelta(weeks=-4)) if not date_start else date_start
    )
    date_end = request.GET.get("date_end")
    date_end = date.today() if not date_end else date_end

    pathologist = request.GET.get("pathologists")
    area = request.GET.get("areas")

    if area:
        area = area.split(";")
        pathologist = UserArea.objects.filter(area_id__in=area).values_list(
            "user_id", flat=True
        )
    elif pathologist:
        pathologist = pathologist.split(";")
    else:
        pathologist = get_pathologists(request.user)

    analysis_filter = Analysis.objects.filter(
        Q(manual_cancelled_date__isnull=True) | Q(forms__cancelled=False),
        Q(manual_closing_date__gte=date_start) | Q(forms__closed_at__gte=date_start),
        exam__pathologists_assignment=True,
        patologo__in=pathologist,
        pre_report_started=True,
        pre_report_ended=True,
    )

    analysis_data = []

    holidays = np.array(get_holidays(), dtype="datetime64")

    for analysis in analysis_filter:
        analysis_data.append(
            {
                "user": analysis.pathologist_name,
                "week": analysis.week_closed,
                "exam": analysis.exam.name,
                "days_processing": analysis.days_processing(holidays),
                "days_assigning": analysis.days_assigning(holidays),
                "days_waiting": analysis.days_waiting(holidays),
                "days_reading": analysis.days_reading(holidays),
                "days_reviewing": analysis.days_reviewing(holidays),
            }
        )

    return JsonResponse(analysis_data, safe=False)
