import csv
import json
from datetime import date, datetime, timedelta
from smtplib import SMTPException

from dateutil.parser import ParserError, parse
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.core import serializers, mail
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import InvalidPage, Paginator
from django.db.models import Count
from django.db.models.query_utils import Q
from django.db.utils import IntegrityError
from django.forms.models import model_to_dict
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView
from django.template.loader import get_template
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.views.decorators.cache import cache_page

from accounts.models import User
from backend.models import (
    EntryForm,
    Identification,
    AnalysisForm,
    Organ,
    OrganUnit,
    Sample,
    SampleExams,
    Stain,
    Unit,
    Exam
)
from lab.models import (
    Analysis,
    Case,
    Cassette,
    CassetteOrgan,
    Process,
    Slide,
    UnitDifference,
    UnitProxy,
)
from lab.services import (
    change_case_step,
    create_or_update_analysisform_in_portal,
    create_or_update_identification_in_portal,
    create_or_update_unit_in_portal,
    create_or_update_sample_in_portal,
    generate_differences,
)

from api.serializers import EntryformSerializer, IdentificationSerializer, UnitSerializer, CassetteSerializer
from vehice import settings


@login_required
def home(request):
    cassettes_to_build = UnitProxy.objects.pending_cassettes([1, 2, 6, 7]).count()
    cassettes_to_process = Cassette.objects.filter(processed_at=None).count()
    differences_count = UnitDifference.objects.filter(status=0).count()
    slides_to_build = Cassette.objects.filter(
        slides=None, processed_at__isnull=False
    ).count()
    slides_to_release = Slide.objects.filter(released_at=None).count()
    return render(
        request,
        "home.html",
        {
            "cassettes_to_build": cassettes_to_build,
            "cassettes_to_process": cassettes_to_process,
            "cassettes_differences": differences_count,
            "cassettes_workload": cassettes_to_build
            + cassettes_to_process
            + differences_count,
            "slides_to_build": slides_to_build,
            "slides_to_release": slides_to_release,
            "slides_workload": slides_to_build + slides_to_release,
        },
    )


@login_required
def refresh_portal(request, pk):
    analysis = Analysis.objects.get(pk=pk)

    report_code_form = json.loads(request.body)
    if "report_code" in report_code_form:
        analysis.report_code = report_code_form["report_code"]
        analysis.save()

    entryform = analysis.entryform
    all_samples = entryform.sample_set.all()
    sample_exams = SampleExams.objects.filter(
        sample__in=all_samples, exam=analysis.exam, stain=analysis.stain
    )
    samples = Sample.objects.filter(
        pk__in=sample_exams.values_list("sample_id", flat=True)
    )
    identifications = Identification.objects.filter(
        pk__in=samples.values_list("identification_id", flat=True)
    )
    unit_organs = OrganUnit.objects.filter(
        pk__in=sample_exams.values_list("unit_organ_id", flat=True)
    )
    units = Unit.objects.filter(pk__in=unit_organs.values_list("unit_id", flat=True))

    errors = []
    status, response = create_or_update_analysisform_in_portal(entryform, analysis)

    if status == "ERROR":
        errors.append({
            "status": f"ERROR WHILE SAVING ANALYSIS",
            "message": response
        })

    for identification in identifications:
        status, response = create_or_update_identification_in_portal(
            identification, analysis.id
        )

        if status == "ERROR":
            errors.append(
                {
                    "status": f"ERROR WHILE SAVING IDENTIFICATION {identification.id}",
                    "message": response,
                }
            )

    for unit in units:
        status, response = create_or_update_unit_in_portal(unit)

        if status == "ERROR":
            errors.append(
                {
                    "status": f"ERROR WHILE SAVING UNIT {unit.id}",
                    "message": response,
                }
            )

    for sample in samples:
        status, response = create_or_update_sample_in_portal(sample)

        if status == "ERROR":
            errors.append(
                {
                    "status": f"ERROR WHILE SAVING SAMPLE {sample.id}",
                    "message": response,
                }
            )

    portal = settings.PORTAL_USER_SITE + str(analysis.id)
    return JsonResponse({"result": errors, "url": portal})


# Case related views


@method_decorator(login_required, name="dispatch")
class CaseReadSheet(DetailView):
    """Displays format for a :model:`lab.Case` read sheet.
    A read sheet contains information for a Case's :model:`lab.Slide`
    including that slide's :model:`backend.Organ` and :model:`backend.Stain`
    """

    model = Case
    template_name = "cases/read_sheet.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["slides"] = []

        units = Unit.objects.filter(Q(identification__entryform=self.get_object()))
        units_organs = OrganUnit.objects.filter(
            unit_id__in=units.values_list("id", flat=True)
        )
        sample_exams = SampleExams.objects.filter(
            unit_organ_id__in=units_organs.values_list("id", flat=True),
        ).exclude(stain_id=2)
        slides = (
            Slide.objects.filter(unit__in=units)
            .exclude(stain_id=2)
            .order_by("correlative")
        )

        sample_exams_count = sample_exams.count()
        slide_organs_count = 0

        for slide in slides:
            organ_exams = sample_exams.filter(stain=slide.stain)
            slide_organs = slide.organs.filter(
                pk__in=organ_exams.values_list("organ_id", flat=True)
            )

            slide_organs_count += slide_organs.count()
            row = {
                "identification": str(slide.unit.identification),
                "unit": slide.unit.correlative,
                "organs": ",".join(slide_organs.values_list("abbreviation", flat=True)),
                "stain": str(slide.stain),
                "slide": slide.correlative,
                "tag": slide.tag,
                "url": slide.get_absolute_url(),
                "released_at": slide.released_at,
            }
            if slide.cassette:
                row["observation"] = slide.cassette.observation
            context["slides"].append(row)


        context["organ_difference"] = sample_exams_count != slide_organs_count
        return context


@method_decorator(login_required, name="dispatch")
class AnalysisReadSheet(DetailView):
    """Displays format for a :model:`lab.Analysis` read sheet.
    A read sheet contains information for an Analysis's :model:`lab.Slide`
    including that slide's :model:`backend.Organ` and :model:`backend.Stain`
    """

    model = Analysis
    template_name = "cases/read_sheet.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["slides"] = []

        analysis = self.get_object()
        case = analysis.entryform
        context["case"] = case
        units = Unit.objects.filter(Q(identification__entryform=case))
        units_organs = OrganUnit.objects.filter(
            unit_id__in=units.values_list("id", flat=True)
        )
        sample_exams = SampleExams.objects.filter(
            unit_organ_id__in=units_organs.values_list("id", flat=True),
            exam=analysis.exam,
            stain=analysis.stain,
        ).exclude(stain_id=2)
        slides = (
            Slide.objects.filter(unit__in=units, stain=analysis.stain)
            .exclude(stain_id=2)
            .order_by("correlative")
        )

        sample_exams_count = sample_exams.count()
        slide_organs_count = 0

        for slide in slides:
            organ_exams = sample_exams.filter(stain=slide.stain)
            slide_organs = slide.organs.filter(
                pk__in=organ_exams.values_list("organ_id", flat=True)
            )

            if slide_organs.count() <= 0:
                continue

            slide_organs_count += slide_organs.count()

            row = {
                "identification": str(slide.unit.identification),
                "unit": slide.unit.correlative,
                "organs": ",".join(slide_organs.values_list("abbreviation", flat=True)),
                "stain": str(slide.stain),
                "slide": slide.correlative,
                "tag": slide.tag,
                "url": slide.get_absolute_url(),
                "released_at": slide.released_at,
            }
            if slide.cassette:
                row["observation"] = slide.cassette.observation
            context["slides"].append(row)


        context["organ_difference"] = sample_exams_count != slide_organs_count
        return context


@method_decorator(login_required, name="dispatch")
class CaseDetail(DetailView):
    """Displays detailed data of a Case.
    Data is displayed in a boilerplate template that can be
    embeded using javascript anywhere in a page as needed.
    """

    model = Case
    template_name = "cases/detail.html"


@login_required
def case_process_state(request, pk):
    """
    Displays general information, lab process state, and service reading availability
    for the provided pk's :model:`lab.Case`
    """

    case = get_object_or_404(Case, pk=pk)
    analysis = Analysis.objects.filter(entryform=case)
    identifications = case.identification_set.all()
    units = Unit.objects.filter(
        identification_id__in=identifications.values_list("id", flat=True)
    )
    units_id = units.values_list("id", flat=True)
    units_organs = OrganUnit.objects.filter(unit_id__in=units_id)
    sample_exams = SampleExams.objects.filter(
        unit_organ_id__in=units_organs.values_list("id", flat=True),
    ).exclude(stain_id=2)

    cassettes = Cassette.objects.filter(unit_id__in=units_id)
    cassettes_organs = CassetteOrgan.objects.filter(
        cassette_id__in=cassettes.values_list("id", flat=True)
    )

    cassettes_processed = Cassette.objects.filter(
        id__in=cassettes.values_list("id", flat=True), processed_at__isnull=False
    )

    groups = []
    names = []

    for identification in identifications:
        groups.append(identification.group)
        names.append(identification.cage)

    groups = " / ".join(set(groups))
    names = " / ".join(names)

    identification_tag = names
    group_tag = groups

    slides = (
        Slide.objects.filter(unit_id__in=units_id)
        .values("stain", "stain__abbreviation")
        .annotate(
            build=Count("stain"),
            available=Count("released_at", filter=Q(released_at__isnull=False)),
        )
        .order_by("stain")
    )

    return render(
        request,
        "cases/state.html",
        {
            "case": case,
            "analysis": analysis,
            "units": units.count(),
            "units_organs_count": units_organs.count(),
            "cassettes": cassettes.count(),
            "cassettes_organs_count": cassettes_organs.count(),
            "cassettes_processed": cassettes_processed.count(),
            "slides": slides,
            "identification_tag": identification_tag,
            "group_tag": group_tag,
        },
    )


@login_required
def case_select_options(request):
    """
    Returns a formatted JSON to be used in a Select2 input
    listing all :model:`lab.Case`

    **REQUEST**
        `search`: Search term to look for in case.no_caso.
        `page`: Paginator's current page.

    """
    search_term = request.GET.get("search")

    if not search_term:
        return JsonResponse({})

    cases = Case.objects.filter(no_caso__icontains=search_term)

    page = request.GET.get("page")

    cases_paginator = Paginator(cases, 20)
    cases_paginated = cases_paginator.get_page(page)

    response = {"results": [], "pagination": {"more": cases_paginated.has_next()}}

    for case in cases_paginated:
        response["results"].append(
            {
                "id": case.id,
                "text": case.no_caso,
            }
        )

    return JsonResponse(response)


# Organ related views


@login_required
def organ_list(request):
    """Returns a list of all :model:`backend.Organ`"""
    organs = Organ.objects.all()

    return HttpResponse(
        serializers.serialize("json", organs), content_type="application/json"
    )


# Stain related views


@login_required
def stain_list(request):
    """Returns a list of all :model:`backend.Stain`"""
    stains = Stain.objects.all()

    return HttpResponse(
        serializers.serialize("json", stains), content_type="application/json"
    )


# Unit related views


@login_required
def unit_select_options(request):
    """
    Returns a formatted JSON to be used in a Select2 input
    listing all Units with their Case.

    **REQUEST**
        `search`: Search term to look for in Units, Identifications, and Entryforms.
        `page`: Paginator's current page.

    """
    search_term = request.GET.get("search")

    if not search_term:
        return JsonResponse({})

    units = (
        Unit.objects.filter(identification__entryform__no_caso__icontains=search_term)
        .select_related("identification__entryform")
        .order_by("identification__entryform__no_caso")
    )

    includes_cassettes = request.GET.get("cassettes")

    cassettes = None

    if includes_cassettes:
        cassettes = (
            Cassette.objects.filter(
                unit__identification__entryform__no_caso__icontains=search_term
            )
            .select_related("unit__identification__entryform")
            .order_by("unit__identification__entryform__no_caso")
        )

    page = request.GET.get("page")

    units_paginator = Paginator(units, 20)
    units_paginated = units_paginator.get_page(page)

    response = {"results": [], "pagination": {"more": units_paginated.has_next()}}

    for unit in units_paginated:
        response["results"].append(
            {
                "id": unit.id,
                "text": f"""{unit.identification.entryform.no_caso} / {unit.identification} / {unit.correlative}""",
            }
        )

    if cassettes:
        cassettes_paginator = Paginator(cassettes, 20)
        cassettes_paginated = cassettes_paginator.get_page(page)

        for cassette in cassettes_paginated:
            response["results"].append(
                {
                    "id": f"""cassette.{cassette.id}""",
                    "text": f"""{cassette.unit.identification.entryform.no_caso} / {cassette.unit.identification} / {cassette.unit.correlative} / {cassette.correlative}""",
                }
            )

    return JsonResponse(response)


# Cassette related views


class CassetteHome(View):
    def get_context(self):
        """
        Returns common context for the class.
        """
        build_count = UnitProxy.objects.pending_cassettes([1, 2, 6, 7]).count()
        process_count = Cassette.objects.filter(processed_at=None).count()
        differences_count = UnitDifference.objects.filter(status=0).count()
        return {
            "build_count": build_count,
            "process_count": process_count,
            "differences_count": differences_count,
        }

    def report_created_cassettes(self, date_range, case=None, response=None):
        """
        Returns a list with :model:`lab.Cassette` which have been
        created within the given date range tuple (start, end).
        """

        cassettes = None
        if case:
            cassettes = Cassette.objects.filter(unit__identification__entryform_id=case)
        else:
            cassettes = Cassette.objects.filter(
                created_at__gte=date_range[0], created_at__lte=date_range[1]
            )

        response_data = []

        if response:
            csv_writer = csv.writer(response)
            csv_writer.writerow(
                [
                    "Caso",
                    "Identificacion",
                    "Unidad",
                    "Cassette",
                    "Organos",
                    "Codigo",
                    "Fecha de Armado",
                ]
            )

            for cassette in cassettes:
                organs_text = ",".join(
                    [organ.abbreviation for organ in cassette.organs.all()]
                )
                csv_writer.writerow(
                    [
                        cassette.unit.identification.entryform.no_caso,
                        str(cassette.unit.identification),
                        cassette.unit.correlative,
                        cassette.correlative,
                        organs_text,
                        cassette.tag,
                        cassette.created_at,
                    ]
                )

            return response

        return cassettes

    def report_differences_cassettes(
        self, date_range, include_solved, case=None, response=None
    ):
        """
        Returns a list with :model:`lab.UnitDifferences` which have been
        created withing the given date range tuple (start, end).
        """

        differences = None
        if case:
            differences = UnitDifference.objects.filter(
                unit__identification__entryform_id=case
            )
        else:
            differences = UnitDifference.objects.filter(
                created_at__gte=date_range[0], created_at__lte=date_range[1]
            )

        if not include_solved:
            differences = differences.filter(status=0)

        if response:
            csv_writer = csv.writer(response)
            csv_writer.writerow(
                ["Caso", "Identificacion", "Unidad", "Organo", "Cantidad"]
            )

            for difference in differences:
                csv_writer.writerow(
                    [
                        difference.unit.identification.entryform.no_caso,
                        str(difference.unit.identification),
                        difference.unit.correlative,
                        difference.organ,
                        difference.difference,
                    ]
                )

            return response

        return differences

    @method_decorator(login_required)
    def get(self, request):
        """Dashboard for Cassettes.

        Includes links to build, reports, and index.
        """
        context = self.get_context()

        return render(request, "cassettes/home.html", context)

    @method_decorator(login_required)
    def post(self, request):
        """
        Returns either a FileResponse or an HttpResponse
        from the given parameters.

        **REQUEST**
            ``report_name``: Name of the report that will be generated. ("created", "differences")
            ``from_date``: Earlier limit for the date range.
            ``to_date``: Latest limit for the date range. Defaults to current.
            ``include_solved``: Latest limit for the date range. Defaults to current.
            ``report_type``: boolean which determines if the response is a file or on-screen.
        """
        date_range = None

        case = request.POST.get("case")

        if not case:
            try:
                from_date = parse(request.POST.get("from_date"))
            except ParserError:
                raise Http404("Sin fecha de inicio.")
            try:
                to_date = request.POST.get("to_date")
            except ParserError:
                to_date = datetime.now()

            date_range = (from_date, to_date)

        report_name = request.POST.get("report_name")
        is_csv = int(request.POST.get("report_type"))

        if is_csv:
            response = HttpResponse(content_type="text/csv")
            filename = (
                "Cassettes creados"
                if report_name == "created"
                else "Diferencias en Unidades"
            )
            response[
                "Content-Disposition"
            ] = f"attachment; filename='Reporte {filename} {from_date} - {to_date}.csv'"

            if report_name == "created":
                return self.report_created_cassettes(date_range, case, response)
            elif report_name == "differences":
                return self.report_differences_cassettes(
                    date_range, case=case, response=response
                )

            raise Http404("Tipo de reporte invalido.")

        context = self.get_context()
        context["report_name"] = report_name
        if report_name == "created":
            context["rows"] = self.report_created_cassettes(date_range, case)
        elif report_name == "differences":
            include_solved = bool(request.POST.get("include_solved"))
            context["rows"] = self.report_differences_cassettes(
                date_range, include_solved, case
            )

        return render(request, "cassettes/home.html", context)


@login_required
def cassette_differences(request):
    """
    List of all :model:`lab.UnitDifference` generated during :view:`lab.CassetteBuild`
    that haven't been resolved (as in status=1).
    """
    units = Unit.objects.filter(cassettes__isnull=False)
    differences = UnitDifference.objects.filter(status=0)
    context = {"differences": differences}
    return render(request, "cassettes/differences.html", context)


@login_required
def redirect_to_workflow_edit(request, pk, step):
    """Redirects a case to it's workflow form according to the given step"""
    case, form = change_case_step(pk, step)
    units = case.units()
    differences = UnitDifference.objects.filter(
        unit_id__in=units.values_list("id", flat=True), status=0
    )

    for difference in differences:
        unit = difference.unit
        organ = difference.organ
        delta_difference = difference.difference

        if delta_difference > 0:
            for index in range(delta_difference):
                OrganUnit.objects.create(unit=unit, organ=organ)
        elif delta_difference < 0:
            abs_difference = abs(delta_difference)
            organ_units = OrganUnit.objects.filter(organ=organ, unit=unit)
            SampleExams.objects.filter(unit_organ__in=organ_units).delete()
            samples = Sample.objects.filter(unit_organs__in=organ_units).distinct()

            for sample in samples:
                for organ_unit in organ_units:
                    sample.unit_organs.remove(organ_unit)

                if sample.unit_organs.count() < 1:
                    sample.delete()

            organ_units_pk = list(organ_units.values_list("id", flat=True))
            to_delete = OrganUnit.objects.filter(pk__in=organ_units_pk[:abs_difference])
            to_delete.delete()

        difference.status = 1
        difference.save()

    return reverse("workflow_w_id", kwargs={"form_id": form.pk})


@login_required
def update_unit_difference(request, pk):
    """
    Toggle the state for the given :model:`lab.UnitDifference` between
    0 (Unreviewed) and 1 (reviewed).
    """
    difference = get_object_or_404(UnitDifference, pk=pk)
    log_message = request.POST.get("message")
    fix_differences = bool(int(request.POST.get("fix_differences")))
    if log_message:
        difference.status_change_log = f"{difference.status_change_log};{log_message}"

    if fix_differences:
        redirect = redirect_to_workflow_edit(
            request, difference.unit.identification.entryform.pk, step=2
        )
        return JsonResponse({"redirect": redirect})

    difference.status = not difference.status
    difference.save()
    return JsonResponse(model_to_dict(difference))


@login_required
def cassette_prebuild(request):
    """
    Receives a JSON with 2 keys: `selected` which is an array of unit ids;
    and `rules` which is a dictionary that dictates how the cassettes are build,

    * rules["unique"]
        Is an array of unit ids in which all of those units are to be put by themselves
        in their own Cassette.

    * rules["groups"]
        Is an array of arrays containing unit ids, in which all of those groups must be put
        together in their own Cassettes.

    * rules["max"]
        Is an integer greater than or equal to 0, and any Cassette can't have more organs than this
        number, unless is 0, then a Cassette can have as many Organs as available.


    This returns a JSON containing Cassette prototypes.
    """
    items = json.loads(request.body)
    units_id = items["selected"]
    rules = items["rules"]

    units = Unit.objects.filter(pk__in=units_id).order_by(
        "identification__correlative", "correlative"
    )

    response = []

    def response_format(unit, organs, count):
        return {
            "case": unit.identification.entryform.no_caso,
            "identification": str(unit.identification),
            "unit": unit.correlative,
            "unit_id": unit.id,
            "cassette": count,
            "organs": serializers.serialize("json", unit.organs.all()),
            "cassette_organs": serializers.serialize("json", organs),
        }

    for unit in units:
        case = unit.identification.entryform
        identifications = case.identification_set.all().values_list("id", flat=True)
        case_units = (
            Unit.objects.filter(identification_id__in=identifications)
            .values_list("id", flat=True)
            .order_by("identification_id", "correlative")
        )
        previous_cassette_highest_correlative = (
            Cassette.objects.filter(unit_id__in=case_units)
            .order_by("-correlative")
            .first()
        )
        cassette_count = 1
        if previous_cassette_highest_correlative:
            cassette_count = previous_cassette_highest_correlative.correlative + 1
        excludes = []

        if rules["uniques"] and len(rules["uniques"]) > 0:
            organs = unit.organs.filter(pk__in=rules["uniques"])

            if not organs.count() <= 0:
                for organ in organs:
                    response.append(response_format(unit, [organ], cassette_count))
                    cassette_count += 1

                excludes.extend([pk for pk in rules["uniques"]])

        if rules["groups"] and len(rules["groups"]) > 0:
            for group in rules["groups"]:
                organs = unit.organs.filter(pk__in=group).exclude(pk__in=excludes)

                if not organs.count() <= 0:
                    response.append(response_format(unit, organs, cassette_count))
                    cassette_count += 1
                    excludes.extend([pk for pk in group])

        organs = unit.organs.exclude(pk__in=excludes).order_by("-id")

        if rules["max"] and rules["max"] > 0:
            organs_pages = Paginator(organs, rules["max"], allow_empty_first_page=False)

            for page in organs_pages.page_range:
                try:
                    current_page = response_format(
                        unit, organs_pages.get_page(page), cassette_count
                    )
                except InvalidPage:
                    continue
                else:
                    response.append(current_page)
                    cassette_count += 1
        elif organs.count() > 0:
            response.append(response_format(unit, organs, cassette_count))

    return HttpResponse(json.dumps(response), content_type="application/json")


class CassetteBuild(View):
    
    @method_decorator(cache_page(60 * 5))  # Caché de 5 minutos
    @method_decorator(login_required)
    def get(self, request):
        """
        Displays list of available :model:`lab.Cassette` to build,
        from :model:`backend.Unit` where their :model:`backend.EntryForm`.entry_format
        is either (1, "Tubo"), (2, "Cassette"), (6, "Vivo"), (7, "Muerto").

        If the request is done through Ajax then response is a Json
        with the same list, this is used to update the table.

        **Context**
        ``units``
            A list of :model:`backend.EntryForm`
            with prefetched :model:`backend.Identification`
            and :model:`backend.Unit`

        **Template**
        ``lab/cassettes/build.html``
        """
        units = UnitProxy.objects.pending_cassettes([1, 2, 6, 7]).order_by(
            "identification__correlative", "correlative"
        )
        organs = serializers.serialize("json", Organ.objects.all())

        return render(
            request, "cassettes/build.html", {"units": units, "organs": organs}
        )

    @method_decorator(login_required)
    def post(self, request):
        """
        Creates a new Cassette storing build_at date and their correlative
        according to their :model:`backend.Unit` and :model:`backend.EntryForm`
        """

        request_input = json.loads(request.body)

        if "units" not in request_input or not request_input["units"]:
            return JsonResponse(
                {"status": "ERROR", "message": "units is empty"}, status=400
            )

        units = request_input["units"]

        try:
            build_at = parse(request_input["build_at"])
        except (KeyError, ParserError):
            build_at = datetime.now()

        created = []
        errors = []
        differences = False
        for row in units:
            try:
                unit = Unit.objects.get(pk=row["id"])
            except ObjectDoesNotExist:
                return JsonResponse(
                    {
                        "status": "ERROR",
                        "message": "Unit id %d does not exists" % row["id"],
                    },
                    status=400,
                )

            correlative = 1
            if "correlative" in row and row["correlative"]:
                correlative = row["correlative"]

            else:
                cassette_highest_correlative = unit.cassettes.order_by(
                    "-correlative"
                ).first()
                if cassette_highest_correlative:
                    correlative = cassette_highest_correlative.correlative

            observation = row["observation"] if "observation" in row else None

            cassette = unit.cassettes.create(
                build_at=build_at,
                correlative=correlative,
                observation=observation,
            )

            for organ_id in row["organs"]:
                try:
                    organ = Organ.objects.get(pk=organ_id)
                except Organ.DoesNotExist:
                    errors.append(
                        {
                            "status": "ERROR",
                            "message": "Organ id %d does not exists" % organ_id,
                        }
                    )
                else:
                    CassetteOrgan.objects.create(organ=organ, cassette=cassette)
                    created.append(cassette)

            current_difference = generate_differences(unit)

            if not differences:
                differences = current_difference

        return JsonResponse(
            {
                "created": serializers.serialize("json", created),
                "errors": errors,
                "differences": differences,
            },
            safe=False,
            status=201,
        )


@method_decorator(login_required, name="dispatch")
class CassetteIndex(ListView):
    """Displays a list of Cassettes.
    Render a template list with all Cassettes including access to edit and reprocess
    buttons.

        **Context**
        ``cassettes``
            A list of :model:`lab.Cassette`
            with prefetched :model:`backend.Organ`

        **Template**
        ``lab/cassettes/index.html``

    """

    template_name = "cassettes/index.html"
    context_object_name = "cassettes"

    def get_queryset(self):
        cassette_range = self.request.GET.get("range")
        now = datetime.now()

        time_delta = timedelta(days=7)
        if cassette_range == "2":
            time_delta = timedelta(days=30)
        elif cassette_range == "3":
            time_delta = timedelta(days=90)
        elif cassette_range == "4":
            time_delta = timedelta(days=180)
        elif cassette_range == "5":
            time_delta = timedelta(days=500)

        date_range = now - time_delta

        cassettes = (
            Cassette.objects.filter(
                created_at__gte=date_range,
                unit__identification__entryform__forms__cancelled=0,
                unit__identification__entryform__forms__form_closed=0,
            )
            .select_related("unit__identification__entryform")
            .prefetch_related("organs")
        )

        return cassettes


class CassetteDetail(View):
    def serialize_data(self, cassette):
        return {
            "cassette": serializers.serialize("json", [cassette]),
            "organs": serializers.serialize("json", cassette.organs.all()),
        }

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Returns a JSON detailing Cassette.

        **CONTEXT**

        ``cassette``
            Detailed data for the requested :model:`lab.Cassette`
        ``organs``
            List of :model:`backend.Organ` that belongs to requested Cassette.

        """
        cassette = get_object_or_404(Cassette, pk=kwargs["pk"])
        data = self.serialize_data(cassette)
        return HttpResponse(json.dumps(data), content_type="application/json")

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """Updates a Cassette.
        Returns serialized data of the updated Cassette.

        **REQUEST**

            ``build_at``
                Updated build_at date. Optional.
            ``correlative``
                Updated correlative. Optional.
            ``organs``
                List of :model:`backend.Organ`. This will set the current
                organs for this Cassette. Optional.

        """
        cassette = get_object_or_404(Cassette, pk=kwargs["pk"])

        request_input = json.loads(request.body)
        edited = False

        if "build_at" in request_input:
            try:
                build_at = parse(request_input["build_at"])
            except (ParserError):
                build_at = cassette.build_at
            else:
                cassette.build_at = build_at
        if "correlative" in request_input:
            cassette.correlative = request_input["correlative"]
            edited = True
        if "organs" in request_input:
            edited = True
            CassetteOrgan.objects.filter(cassette=cassette).delete()
            for organ_id in request_input["organs"]:
                try:
                    CassetteOrgan.objects.create(cassette=cassette, organ_id=organ_id)
                except IntegrityError:
                    raise Http404("Organ not found.")

        if "unit_id" in request_input:
            edited = True
            cassette.unit_id = request_input["unit_id"]

        if edited:
            cassette.save()

        data = self.serialize_data(cassette)

        differences = generate_differences(cassette.unit)

        return HttpResponse(json.dumps(data), content_type="application/json")


class CassetteProcess(View):
    @method_decorator(login_required)
    def get(self, request):
        """
        Displays a list of :model:`lab.Cassette` which ``processed_at`` date is null.
        """
        cassettes = Cassette.objects.filter(processed_at=None).select_related(
            "unit__identification__entryform"
        )

        min_date = None
        try:
            earliest_cassette = cassettes.earliest("build_at")
        except Cassette.DoesNotExist:
            min_date = datetime.now()
        else:
            min_date = earliest_cassette.build_at.isoformat()[:10]
        max_date = datetime.now().isoformat()[:10]
        return render(request, "cassettes/process.html", {"cassettes": cassettes, "min_date":min_date, "max_date": max_date})

    @method_decorator(login_required)
    def post(self, request):
        """
        Updates the given :model:`lab.Cassette` with the given date for `processed_at`.
        """
        request_data = json.loads(request.body)

        try:
            processed_at = parse(request_data["processed_at"])
        except (ParserError):
            processed_at = datetime.now()

        cassettes_updated = Cassette.objects.filter(
            pk__in=request_data["cassettes"]
        ).update(processed_at=processed_at)

        return JsonResponse(cassettes_updated, safe=False)


# Slide related views


class SlideHome(View):
    def get_context(self):
        """
        Returns common context for the class.
        """

        units_count = Unit.objects.filter(
            identification__entryform__entry_format=5,
            identification__entryform__forms__cancelled=0,
            identification__entryform__forms__form_closed=0,
        ).count()
        cassettes_count = Cassette.objects.filter(
            slides=None, processed_at__isnull=False
        ).count()
        build_count = units_count + cassettes_count
        release_count = Slide.objects.filter(released_at__isnull=True).count()

        return {
            "build_count": build_count,
            "release_count": release_count,
        }

    def report_created_slides(self, date_range, response=None):
        """
        Returns a list with :model:`lab.Cassette` which have been
        created within the given date range tuple (start, end).
        """
        slides = Slide.objects.filter(
            created_at__gte=date_range[0], created_at__lte=date_range[1]
        )

        response_data = []

        if response:
            csv_writer = csv.writer(response)
            csv_writer.writerow(
                [
                    "Caso",
                    "Identificacion",
                    "Unidad",
                    "Slide",
                    "Tincion",
                    "Organos",
                    "Codigo",
                    "Fecha de Armado",
                ]
            )

            for slide in slides:
                organs_text = ",".join([organ.abbreviation for organ in slide.organs])
                csv_writer.writerow(
                    [
                        slide.unit.identification.entryform.no_caso,
                        str(slide.unit.identification),
                        slide.unit.correlative,
                        slide.correlative,
                        slide.stain.abbreviation,
                        organs_text,
                        slide.tag,
                        slide.created_at,
                    ]
                )

            return response

        return slides

    @method_decorator(login_required)
    def get(self, request):
        """Dashboard for Slides.

        Includes links to build, reports, and index.
        """
        context = self.get_context()

        return render(request, "slides/home.html", context)

    @method_decorator(login_required)
    def post(self, request):
        """
        Returns either a FileResponse or an HttpResponse
        from the given parameters.

        **REQUEST**
            ``from_date``: Earlier limit for the date range.
            ``to_date``: Latest limit for the date range. Defaults to current.
            ``report_type``: boolean which determines if the response is a file or on-screen.
        """
        try:
            from_date = parse(request.POST.get("from_date"))
        except ParserError:
            raise Http404("Sin fecha de inicio.")
        try:
            to_date = parse(request.POST.get("to_date"))
        except ParserError:
            to_date = datetime.now()
        finally:
            to_date += timedelta(days=1)

        date_range = (from_date, to_date)

        is_csv = int(request.POST.get("report_type"))

        if is_csv:
            response = HttpResponse(content_type="text/csv")
            response[
                "Content-Disposition"
            ] = f"attachment; filename=Reporte Slides Generados {from_date} - {to_date}.csv"

            return self.report_created_slides(date_range, response)

        context = self.get_context()
        context["show_report"] = True
        context["rows"] = self.report_created_slides(date_range)

        return render(request, "slides/home.html", context)


def generate_slide_prototype(items):
    slides = []
    prev_case = None
    slide_correlative = 1
    for item in items:
        cassette = None
        unit = None
        organs_subject = None

        exclude_stain = [2]

        # Cassette is an optional parameter, Unit is required, if no Cassette is given
        # then use the unit_id to prototype the Slide
        if item["cassette"] > 0:
            cassette = Cassette.objects.get(pk=item["cassette"])
            unit = cassette.unit
            organs_subject = cassette.organs.all()
            previous_stains = Slide.objects.filter(cassette=cassette).values_list(
                "stain_id", flat=True
            )
            exclude_stain.extend(previous_stains)
        else:
            unit = Unit.objects.get(pk=item["unit"])
            organs_subject = unit.organs.all()
            previous_stains = Slide.objects.filter(unit=unit).values_list(
                "stain_id", flat=True
            )
            exclude_stain.extend(previous_stains)

        has_organ_group = organs_subject.filter(organ_type=2).count() > 0
        identification = unit.identification
        case = identification.entryform
        organ_unit = unit.organunit_set.values_list(
            "id", flat=True
        )

        if len(organ_unit) <= 0 and organs_subject.count() > 0:
            organ_unit = OrganUnit.objects.filter(unit=unit, organ__organ_type=2)
            if organ_unit.count() > 0:
                organ_unit.values_list("id", flat=True)

        organ_unit = organ_unit.filter(organ__in=organs_subject)

        sample_exams = (
            SampleExams.objects.filter(
                unit_organ__in=organ_unit,
                exam__service_id__in=[1, 2],
            )
            .exclude(stain_id__in=exclude_stain)
            .values("stain_id")
            .annotate(stain_count=Count("stain_id"))
            .order_by("stain_id")
        )

        if not has_organ_group:
            sample_exams.filter(organ__in=organs_subject)

        if prev_case != case:
            slide_correlative = cassette.correlative if cassette else unit.correlative
            prev_case = case

        for sample_exam in sample_exams:
            stain = Stain.objects.get(pk=sample_exam["stain_id"])
            row = {
                "case": model_to_dict(case, fields=["id", "no_caso"]),
                "identification": model_to_dict(
                    identification,
                    fields=["id", "cage", "group", "extra_features_detail"],
                ),
                "unit": model_to_dict(unit, fields=["id", "correlative"]),
                "stain": model_to_dict(stain, fields=["id", "abbreviation"]),
                "slide": slide_correlative,
            }
            if cassette:
                row["cassette"] = (
                    model_to_dict(cassette, fields=["id", "correlative"]),
                )
                row["organs"] = ",".join(
                    [organ.abbreviation for organ in cassette.organs.all()]
                )
            else:
                row["organs"] = ",".join(
                    [organ.abbreviation for organ in unit.organs.all()]
                )

            slides.append(row)
            slide_correlative += 1

    return slides


@login_required
def slide_prebuild(request):
    """
    Returns a JSON response detailing :model:`lab.Slide` prototypes that
    could be generated from the request's Cassette or Units list.
    """
    try:
        items = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({})

    slides = generate_slide_prototype(items)

    return JsonResponse(slides, safe=False)


@login_required
def slide_hide(request):
    """
    Creates slides and marks them as hidden, so they won't appear
    in release or read_sheet.
    """
    try:
        items = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({})

    message = items["message"]
    build_at = datetime.now()

    prototypes = generate_slide_prototype(items["slides"])
    slides = []

    for prototype in prototypes:
        attributes = {
            "correlative": prototype["slide"],
            "unit_id": prototype["unit"]["id"],
            "stain_id": prototype["stain"]["id"],
            "hidden": True,
            "hidden_message": message,
            "build_at": build_at,
        }

        if "cassette" in prototype:
            attributes["cassette_id"] = prototype["cassette"][0]["id"]

        slide = Slide.objects.create(**attributes)
        slides.append(slide)

    created = serializers.serialize("json", slides)

    return JsonResponse(created, safe=False)


class SlideBuild(View):

    def _get_slide_build_context(self, units, cassettes):
        stains = Stain.objects.all()

        slides = []

        if units.count() > 0:
            for unit in units:
                case = unit.identification.entryform
                identification = unit.identification

                unit_organs = OrganUnit.objects.filter(unit=unit).values_list(
                    "id", flat=True
                )
                previous_stains = Slide.objects.filter(unit=unit).values_list(
                    "stain_id", flat=True
                )
                exclude_stain = [2]
                exclude_stain.extend(previous_stains)

                sample_exams = (
                    SampleExams.objects.filter(
                        unit_organ_id__in=unit_organs,
                        exam__service_id__in=[1, 2],
                    )
                    .exclude(stain_id__in=exclude_stain)
                    .distinct()
                    .select_related("stain")
                )

                if sample_exams.count() <= 0:
                    continue

                row = {
                    "case": EntryformSerializer(case).data,
                    "identification": IdentificationSerializer(identification).data,
                    "unit": UnitSerializer(unit).data
                }

                stains = sample_exams.values_list("stain__abbreviation", flat=True)
                dates = []

                for sample_exam in sample_exams:
                    analysis = Analysis.objects.filter(entryform=case, stain=sample_exam.stain)
                    for current_analysis in analysis:
                        time_format = current_analysis.created_at.strftime("%d-%m-%Y")
                        stain_name = current_analysis.stain.abbreviation
                        dates.append(f"{time_format} ({stain_name})")

                stain_text = ", ".join(list(stains))
                dates_text = ", ".join(dates)

                row["stain_text"] = stain_text
                row["dates_text"] = dates_text
                slides.append(row)

        if cassettes.count() > 0:
            for cassette in cassettes:
                case = cassette.unit.identification.entryform
                identification = cassette.unit.identification
                unit = cassette.unit
                cassette_organs = cassette.organs.all()
                unit_organs = OrganUnit.objects.filter(
                    unit=unit
                )
                if len(unit_organs) <= 0 and cassette_organs.count() > 0:
                    unit_organs = OrganUnit.objects.filter(unit=unit, organ__organ_type=2)
                    # if unit_organs.count() > 0:
                    #     unit_organs.values_list("id", flat=True)
                previous_stains = Slide.objects.filter(cassette=cassette).values_list(
                    "stain_id", flat=True
                )

                exclude_stain = [2]
                exclude_stain.extend(previous_stains)

                unit_organs = unit_organs.filter(organ__in=cassette_organs)

                sample_exams = (
                        SampleExams.objects.filter(
                            unit_organ_id__in=unit_organs,
                            exam__service_id__in=[1, 2],
                        )
                        .exclude(stain_id__in=exclude_stain)
                        .distinct()
                        .select_related("stain")
                    )

                if sample_exams.count() <= 0:
                    continue

                row = {
                    "case": EntryformSerializer(case).data,
                    "identification": IdentificationSerializer(identification).data,
                    "unit": UnitSerializer(unit).data,
                    "cassette": CassetteSerializer(cassette).data
                }

                stains = sample_exams.values_list("stain__abbreviation", flat=True)
                dates = []

                analysis = Analysis.objects.filter(entryform=case).exclude(stain_id__in=exclude_stain)
                for current_analysis in analysis:
                    time_format = current_analysis.created_at.strftime("%d-%m-%Y")
                    stain_name = current_analysis.stain.abbreviation
                    dates.append(f"{time_format} ({stain_name})")

                stain_text = ", ".join(list(stains))
                dates_text = ", ".join(dates)

                row["stain_text"] = stain_text
                row["dates_text"] = dates_text
                slides.append(row)

        return slides

    @method_decorator(login_required)
    def get(self, request):
        """
        Displays list of available :model:`lab.Slide` to build,
        from :model:`lab.Cassettte` where they don't already
        have at least one slide built.

        **Context**
        ``cassettes``
            A list of :model:`lab.Cassette`

        **Template**
        ``lab/slides/build.html``
        """

        units = (
            Unit.objects.filter(
                identification__entryform__entry_format=5,
                identification__entryform__forms__cancelled=0,
                identification__entryform__forms__form_closed=0,
            )
            .distinct()
            .select_related("identification__entryform")
        )

        cassettes = (
            Cassette.objects.filter(
                unit__identification__entryform__forms__cancelled=0,
                unit__identification__entryform__forms__form_closed=0,
            )
            .distinct()
            .select_related("unit__identification__entryform")
        )


        units_pks = units.values_list("identification__entryform__id", flat=True)
        cassettes_pks = cassettes.values_list("unit__identification__entryform__id", flat=True)

        entryforms = (EntryForm.objects.filter(pk__in=cassettes_pks) | EntryForm.objects.filter(pk__in=units_pks)).distinct().order_by("-no_caso")


        if request.is_ajax():
            date_range = request.GET.get("range")
            no_caso = request.GET.get("no_caso", '')

            start = datetime.today() - timedelta(days=7)
            end = datetime.today()
            if date_range == "1":
                start = datetime.today() - timedelta(days=15)
                end = datetime.today() - timedelta(days=7)
            if date_range == "2":
                start = datetime.today() - timedelta(days=30)
                end = datetime.today() - timedelta(days=15)
            if date_range == "3":
                start = datetime.today() - timedelta(days=180)
                end = datetime.today() - timedelta(days=30)

            units = units.filter(identification__entryform__created_at__gte=start, identification__entryform__created_at__lte=end, identification__entryform__no_caso__icontains=no_caso)
            cassettes = cassettes.filter(unit__identification__entryform__created_at__gte=start, unit__identification__entryform__created_at__lte=end, unit__identification__entryform__no_caso__icontains=no_caso)
            slides = self._get_slide_build_context(units, cassettes)

            return JsonResponse(slides, safe=False)

        return render(
            request, "slides/build.html", {"entryforms": entryforms}
        )




    @method_decorator(login_required)
    def post(self, request):
        """
        Creates a new Slide storing build_at date and their correlative
        according to their :model:`backend.Unit` and :model:`backend.EntryForm`
        """

        request_input = json.loads(request.body)

        if not "slides" in request_input or not request_input["slides"]:
            return JsonResponse(
                {"status": "ERROR", "message": "slides is empty"}, status=400
            )

        slides = request_input["slides"]

        try:
            build_at = parse(request_input["build_at"])
        except (KeyError, ParserError):
            build_at = datetime.now()

        created = []
        errors = []

        for slide in slides:
            parameters = {}

            if "stain_id" not in slide:
                return JsonResponse(
                    {"status": "ERROR", "message": "Stain not found"},
                    status=400,
                )
            else:
                try:
                    stain = Stain.objects.get(pk=slide["stain_id"])
                except Stain.DoesNotExist:
                    return JsonResponse(
                        {"status": "ERROR", "message": "Stain not found"},
                        status=400,
                    )

            # If not unit is received use the Cassette's unit,
            # if neither Cassette nor Unit is given return error
            if "unit_id" not in slide:
                if "cassette_id" not in slide:
                    return JsonResponse(
                        {"status": "ERROR", "message": "Unit/Cassette not found"},
                        status=400,
                    )
                else:
                    try:
                        cassette = Cassette.objects.get(pk=slide["cassette_id"])
                    except Cassette.DoesNotExist:
                        return JsonResponse(
                            {"status": "ERROR", "message": "Cassette not found"},
                            status=400,
                        )
                    else:
                        unit = cassette.unit
                        parameters["cassette"] = cassette
            else:
                try:
                    unit = Unit.objects.get(pk=slide["unit_id"])
                except Unit.DoesNotExist:
                    if "cassette" not in parameters:
                        return JsonResponse(
                            {"status": "ERROR", "message": "Unit not found"},
                            status=400,
                        )
                    else:
                        unit = cassette.unit

            parameters = {
                "unit": unit,
                "stain": stain,
                "build_at": build_at,
            }

            if "correlative" in slide:
                parameters["correlative"] = slide["correlative"]
            else:
                parameters["correlative"] = unit.correlative

            if (
                "cassette_id" in slide and slide["cassette_id"]
            ) and "cassette" not in parameters:
                try:
                    cassette = Cassette.objects.get(pk=slide["cassette_id"])
                except Cassette.DoesNotExist:
                    return JsonResponse(
                        {"status": "ERROR", "message": "Cassette not found"},
                        status=400,
                    )
                parameters["cassette"] = cassette
                parameters["correlative"] = cassette.correlative

            try:
                slide = Slide.objects.create(**parameters)
            except IntegrityError:
                errors.append(parameters)
            else:
                created.append(slide)

        return JsonResponse(
            {"created": serializers.serialize("json", created), "errors": errors},
            safe=False,
        )


@method_decorator(login_required, name="dispatch")
class SlideIndex(ListView):
    """Displays a list of Slides.
    Render a template list with all Slides including access to edit and reprocess
    buttons.

        **Context**
        ``slides``
            A list of :model:`lab.Slide`

        **Template**
        ``lab/slides/index.html``

    """

    template_name = "slides/index.html"
    context_object_name = "slides"

    def get_queryset(self):
        slide_range = self.request.GET.get("range")
        now = datetime.now()

        time_delta = timedelta(days=7)
        if slide_range == "2":
            time_delta = timedelta(days=30)
        elif slide_range == "3":
            time_delta = timedelta(days=90)
        elif slide_range == "4":
            time_delta = timedelta(days=180)

        date_range = now - time_delta

        slides = Slide.objects.filter(
            created_at__gte=date_range,
            unit__identification__entryform__forms__cancelled=0,
            unit__identification__entryform__forms__form_closed=0,
        ).select_related("unit__identification__entryform")

        return slides


class SlideDetail(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Returns a JSON detailing Slide.

        **CONTEXT**

        ``slide``
            Detailed data for the requested :model:`lab.Slide`
        ``organs``
            List of :model:`backend.Organ` that belongs to requested Slide.

        """
        slide = get_object_or_404(Slide, pk=kwargs["pk"])

        return HttpResponse(
            serializers.serialize("json", [slide]), content_type="application/json"
        )

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """Updates a Slide.
        Returns serialized data of the updated Slide.

        **REQUEST**

            ``build_at``
                Updated build_at date. Optional.
            ``correlative``
                Updated correlative. Optional.
            ``stain``
                Related :model:`backend.Stain`.

        """
        slide = get_object_or_404(Slide, pk=kwargs["pk"])

        request_input = json.loads(request.body)

        if "build_at" in request_input:
            try:
                build_at = parse(request_input["build_at"])
            except (ParserError):
                build_at = slide.build_at
            else:
                slide.build_at = build_at

        if "correlative" in request_input:
            slide.correlative = request_input["correlative"]
        if "stain_id" in request_input:
            slide.stain_id = request_input["stain_id"]

        try:
            slide.save()
        except IntegrityError:
            return JsonResponse(
                {"status": "ERROR", "message": "Couldn't save Slide"}, status=400
            )

        return HttpResponse(
            serializers.serialize("json", [slide]), content_type="application/json"
        )


class SlideRelease(View):
    @method_decorator(login_required)
    def get(self, request):
        """
        Displays a list of :model:`lab.Slide` which ``processed_at`` date is null.
        """
        if request.is_ajax():
            slides = Slide.objects.filter(released_at__isnull=True, hidden=False)

            draw = int(request.GET.get("draw"))
            length = int(request.GET.get("length"))
            search = request.GET.get("search[value]")
            page = int(request.GET.get("start")) + 1

            case_stain = search.split(",")

            if len(case_stain) > 1:
                slides = slides.filter(
                    Q(unit__identification__entryform__no_caso__icontains=case_stain[0]),
                    Q(stain__abbreviation__icontains=case_stain[1])
                )
            else:
                slides = slides.filter(
                    Q(unit__identification__entryform__no_caso__icontains=search)
                )

            slide_paginator = Paginator(slides, length)

            context = {
                "draw": draw + 1,
                "recordsTotal": slides.count(),
                "recordsFiltered": slides.count(),
                "data": [],
            }


            slide_page = slide_paginator.get_page(page)

            #Slide Email notification
            template = "app/template_slide.html"
            correos = []
            caseContainer=[]
            email_contexts={
                "data":[]
            }

            for slide in slide_page.object_list:
                url = slide.get_absolute_url()
                no_caso=slide.tag[:4]

                if url:
                    analysisForm= AnalysisForm.objects.filter(
                        entryform__no_caso__icontains=no_caso,
                        stain=slide.stain
                    ).exclude(process_status="Anulado")

                    for analysis in analysisForm:
                        if analysis.patologo != None:
                            email = analysis.patologo.email
                            if email not in correos:
                                correos.append(analysis.patologo.email)
                                email_contexts["data"].append({
                                    "correo":analysis.patologo.email,
                                })

                        for data in email_contexts["data"]:
                            if data["correo"] == email:
                                if no_caso not in data:
                                    data[no_caso]=[]

                            if data["correo"] == email:
                                if analysis.stain.abbreviation not in data[no_caso]:
                                    data[no_caso].append(analysis.stain.abbreviation)

                context["data"].append(
                    {
                        "id": slide.id,
                        "tag": slide.tag,
                        "url": url,
                        "created_at": slide.created_at,
                    }
                )

            #Send Slide Email notification
            connection = mail.get_connection(username="derivacion@vehice.com", password="DerVeh159")
            for data in email_contexts["data"]:
                message = get_template(template).render(context={"data":data})
                no_caso_subject =""

                for id, casos in data.items():
                    if id != "correo":
                        no_caso_subject=no_caso_subject+"/V"+id

                subject = (
                    "Slide disponibles"+no_caso_subject
                )

                email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email='"VeHiCe"<derivacion@vehice.com>',
                to=[data["correo"]],
                connection=connection
                )
                email.content_subtype = "html"

                try:
                    email.send()
                except (BadHeaderError, SMTPException):
                        return JsonResponse({"status": "ERR", "code": 2})
                connection.close()

            return JsonResponse(context, safe=False)

        return render(request, "slides/release.html")

    @method_decorator(login_required)
    def post(self, request):
        """
        Updates the given :model:`lab.Slide` with the given date for `released_at`.
        """
        request_data = json.loads(request.body)

        try:
            released_at = parse(request_data["released_at"])
        except (ParserError):
            released_at = datetime.now()

        slides_updated = Slide.objects.filter(pk__in=request_data["slides"]).update(
            released_at=released_at
        )

        #Slide Email notification
        slides = Slide.objects.filter(pk__in=request_data["slides"])
        template = "app/template_slide.html"
        no_caso_subject=""
        correos = []
        caseContainer=[]
        email_contexts={
            "data":[]
        }

        for slide in slides:
            no_caso=slide.tag[:4]


            if no_caso not in caseContainer:
                caseContainer.append(no_caso)
                no_caso_subject=no_caso_subject+"/V"+no_caso

            analysisForm= AnalysisForm.objects.filter(
                entryform__no_caso__icontains=no_caso,
                stain=slide.stain
            ).exclude(process_status="Anulado")

            for analysis in analysisForm:
                if analysis.patologo != None:
                    email = analysis.patologo.email
                    if email not in correos:
                        correos.append(analysis.patologo.email)
                        email_contexts["data"].append({
                            "correo":analysis.patologo.email,
                        })

                for data in email_contexts["data"]:
                    if data["correo"] == email:
                        if no_caso not in data:
                            data[no_caso]=[]

                    if data["correo"] == email:
                        if analysis.stain.abbreviation not in data[no_caso]:
                            data[no_caso].append(analysis.stain.abbreviation)

        #Send Slide Email notification
        connection = mail.get_connection(username="derivacion@vehice.com", password="DerVeh159")
        for data in email_contexts["data"]:
            message = get_template(template).render(context={"data":data})

            subject = (
                "Slide disponibles"+no_caso_subject
            )

            email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email='"VeHiCe"<derivacion@vehice.com>',
            to=[data["correo"]],
            connection=connection
            )
            email.content_subtype = "html"

            try:
                email.send()
            except (BadHeaderError, SMTPException):
                    return JsonResponse({"status": "ERR", "code": 2})
            connection.close()

        return JsonResponse(slides_updated, safe=False)


class SlideStain(View):
    @method_decorator(login_required)
    def get(self, request):

        if request.is_ajax():
            draw = int(request.GET.get("draw"))
            length = int(request.GET.get("length"))
            search = request.GET.get("search[value]")
            start = int(request.GET.get("start")) + 1

            cassettes = Cassette.objects.all()
            if search:
                cassettes = Cassette.objects.filter(
                    Q(unit__identification__entryform__no_caso__icontains=search)
                    | Q(unit__identification__cage__icontains=search)
                    | Q(unit__identification__group__icontains=search)
                )
            cassettes_paginator = Paginator(cassettes, length)

            context = {
                "draw": draw + 1,
                "recordsTotal": cassettes_paginator.count,
                "recordsFiltered": cassettes_paginator.count,
                "data": [],
            }

            for page in cassettes_paginator.page_range:
                page_start = cassettes_paginator.get_page(page).start_index()
                if page_start == start:
                    cassettes_page = cassettes_paginator.get_page(page).object_list
                    for cassette in cassettes_page:
                        row = {
                            "id": cassette.id,
                            "name": str(cassette),
                            "build_at": cassette.build_at,
                        }

                        context["data"].append(row)

            return JsonResponse(context)

        stains = Stain.objects.all()

        return render(request, "slides/stain.html", {"stains": stains})


# Process related views


class ProcessList(View):
    def get(self, request):
        process_types = Process.ProcessType
        entryforms = EntryForm.objects.filter(pk__gte=2660).order_by("-no_caso")
        exams_group = "Radiology"
        exams = Exam.objects.filter(group_en=exams_group)
        progress = []

        for entryform in entryforms:
            samples = Sample.objects.filter(entryform=entryform)
            sample_exams = SampleExams.objects.filter(exam__in=exams, sample__in=samples)

            if sample_exams.count() <= 0:
                continue

            unit_organs_pk = set(sample_exams.values_list("unit_organ_id", flat=True))
            unit_organs_count = len(unit_organs_pk)
            morphometry = Process.objects.filter(type=1, unit_organ_id__in=unit_organs_pk).distinct().count()
            macro = Process.objects.filter(type=2, sample_exam__in=sample_exams).count()
            rx = Process.objects.filter(type=3, sample_exam__in=sample_exams).count()
            lab = Process.objects.filter(type=4, sample_exam__in=sample_exams).count()
            last_assignment = None
            if lab > 0:
                last_assignment = Process.objects.filter(type=4, sample_exam__in=sample_exams).latest("done_at")
                last_assignment = last_assignment.done_at

            row = {
                "entryform": entryform.no_caso,
                "created_at": entryform.created_at,
                "samples_count": sample_exams.count(),
                "unit_organs_count": unit_organs_count,
                "morphometry_count": morphometry,
                "macro_count": macro,
                "rx_count": rx,
                "lab_count": lab,
                "last_assignment": last_assignment
            }

            progress.append(row)

        return render(request, "process/index.html", {"process_types": process_types, "radiology_progress": progress})

class ProcessBuild(View):
    def get(self, request, process_type):
        RX = [1, 2, 3, 4]
        PATOLOGIA_CLINICA = []

        # TODO filter by case id

        process_name = Process.ProcessType.get_label(process_type)
        entryforms = EntryForm.objects.filter(pk__gte=2660)
        samples = Sample.objects.filter(entryform__in=entryforms)

        if process_type in RX:
            exams_group = "Radiology"
            exams = Exam.objects.filter(group_en=exams_group)
            sample_exams = SampleExams.objects.filter(exam__in=exams, sample__in=samples)

            if process_type == 1:
                processed_unit_organs = Process.objects.filter(type=process_type).values_list("unit_organ_id", flat=True)
                sample_exams = sample_exams.exclude(unit_organ_id__in=processed_unit_organs).values_list("unit_organ", flat=True)
                unit_organs = OrganUnit.objects.filter(pk__in=sample_exams).distinct()
                return render(request, "process/build-morphometry.html", {"unit_organs": unit_organs, "process_name": process_name})

            if process_type == 4:
                available = []
                for sample_exam in sample_exams:
                    unit_organ = sample_exam.unit_organ
                    has_morphometry = Process.objects.filter(type=1, unit_organ=unit_organ).count() > 0
                    has_macro = Process.objects.filter(type=2, sample_exam=sample_exam).count() > 0
                    has_rx = Process.objects.filter(type=3, sample_exam=sample_exam).count() > 0
                    has_derivacion = Process.objects.filter(type=4, sample_exam=sample_exam).count() > 0

                    if has_morphometry and has_macro and has_rx and not has_derivacion:
                        available.append(sample_exam)

                return render(request, "process/build.html", {"sample_exams": available, "process_name": process_name})


            processed_sample_exams = Process.objects.filter(type=process_type).values_list("sample_exam_id", flat=True)
            sample_exams = sample_exams.exclude(pk__in=processed_sample_exams)

            return render(request, "process/build.html", {"sample_exams": sample_exams, "process_name": process_name})

        if process_type in PATOLOGIA_CLINICA:
            pass

        return redirect(reverse("process_index"))

    def post(self, request, process_type):
        prototypes = json.loads(request.body)

        done_at = prototypes["done_at"]
        created = []
        for pk in prototypes["keys"]:
            if process_type != 1:
                sample_exam = SampleExams.objects.get(pk=pk)
                attributes = {
                    "sample_exam": sample_exam,
                    "unit_organ": sample_exam.unit_organ,
                    "done_at": done_at,
                    "type": process_type
                }
                process = Process.objects.create(**attributes)
                created.append(process.id)
            else:
                unit_organ = OrganUnit.objects.get(pk=pk)
                attributes = {
                    "unit_organ": unit_organ,
                    "done_at": done_at,
                    "type": process_type
                }
                process = Process.objects.create(**attributes)
                created.append(process.id)

        return JsonResponse(created, safe=False)


def template_resumen_report(request, entryform_pk, user_pk, language):
    user = User.objects.get(pk=user_pk)
    entryform = EntryForm.objects.values().get(pk=entryform_pk)
    entryform_object = EntryForm.objects.get(pk=entryform_pk)

    subflow = entryform_object.get_subflow
    entryform["subflow"] = subflow
    entryform["entry_format"] = entryform_object.get_entry_format_display()
    identifications = list(
        Identification.objects.filter(entryform=entryform["id"]).values()
    )

    samples = Sample.objects.filter(entryform=entryform["id"]).order_by("index")

    samples_as_dict = []
    for s in samples:
        s_dict = model_to_dict(
            s, exclude=["organs", "sampleexams", "exams", "identification"]
        )
        organs = []
        sampleexams = s.sampleexams_set.all()
        sampleExa = {}

        for sE in sampleexams:
            analysis_form = entryform_object.analysisform_set.filter(
                exam_id=sE.exam_id
            ).first()
            try:
                a_form = analysis_form.forms.get()
                is_cancelled = a_form.cancelled
                is_closed = a_form.form_closed
            except:
                is_cancelled = False
                is_closed = False

            if not is_cancelled:
                try:
                    sampleExa[sE.exam_id]["organ_id"].append(
                        {
                            "name": sE.organ.name
                            if language == 'es'
                            else sE.organ.name_en
                            if sE.organ.name_en
                            else sE.organ.name,
                            "id": sE.organ.id,
                        }
                    )
                except:
                    sampleExa[sE.exam_id] = {
                        "exam_id": sE.exam_id,
                        "exam_name": sE.exam.name,
                        "exam_type": sE.exam.service_id,
                        "stain": sE.stain.abbreviation.upper() if sE.stain else "N/A",
                        "sample_id": sE.sample_id,
                        "organ_id": [
                            {
                                "name": sE.organ.name,
                                "id": sE.organ.id,
                            }
                        ],
                    }
                if sE.exam.service_id == 1:
                    try:
                        organs.index(model_to_dict(sE.organ))
                    except:
                        organs.append(model_to_dict(sE.organ))
        s_dict["organs_set"] = organs
        s_dict["sample_exams_set"] = sampleExa
        s_dict["identification"] = model_to_dict(
            s.identification, exclude=["organs", "organs_before_validations"]
        )
        samples_as_dict.append(s_dict)

    entryform["identifications"] = []
    for ident in entryform_object.identification_set.all():
        ident_json = model_to_dict(
            ident, exclude=["organs", "organs_before_validations"]
        )
        ident_json["organs_set"] = list(ident.organs.all().values())
        ident_json["unit_count"] = ident.unit_set.count()
        entryform["identifications"].append(ident_json)

    entryform["analyses"] = list(
        entryform_object.analysisform_set.filter(exam__isnull=False).values(
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
        model_to_dict(entryform_object.customer, exclude=['center']) if entryform_object.customer else None
    )
    entryform["larvalstage"] = (
        model_to_dict(entryform_object.larvalstage)
        if entryform_object.larvalstage
        else None
    )
    entryform["fixative"] = (
        model_to_dict(entryform_object.fixative) if entryform_object.fixative else None
    )
    entryform["watersource"] = (
        model_to_dict(entryform_object.watersource)
        if entryform_object.watersource
        else None
    )
    entryform["specie"] = (
        model_to_dict(entryform_object.specie) if entryform_object.specie else None
    )

    patologos = list(User.objects.filter(userprofile__profile_id__in=[4, 5]).values())

    for item in entryform["identifications"]:
        servicios = {}
        for item2 in samples_as_dict:
            if item2["identification"]["id"] == item["id"]:

                for key, value in item2["sample_exams_set"].items():
                    if value["exam_name"] in servicios:
                        if value["stain"] in servicios[value["exam_name"]]:
                            for aux in value["organ_id"]:
                                servicios[value["exam_name"]][value["stain"]].append(
                                    aux["name"]
                                )
                        else:
                            servicios[value["exam_name"]][value["stain"]] = []
                            for aux in value["organ_id"]:
                                servicios[value["exam_name"]][value["stain"]].append(
                                    aux["name"]
                                )
                    else:
                        servicios[value["exam_name"]] = {value["stain"]: []}

                        for aux in value["organ_id"]:
                            servicios[value["exam_name"]][value["stain"]].append(
                                aux["name"]
                            )

        serv = {}
        for key, value in servicios.items():
            stains = {}
            for key2, value2 in value.items():

                organs = {}
                for k in value2:
                    if k in organs:
                        organs[k] += 1
                    else:
                        organs[k] = 1

                stains[key2] = organs

            new_key = key + " ("
            organs_amount_by_stain = {}
            for stain in value.keys():
                for org, cant in stains[stain].items():
                    if org in organs_amount_by_stain:
                        organs_amount_by_stain[org].append(cant)
                    else:
                        organs_amount_by_stain[org] = [cant]

                new_key += stain + " - "

            serv[new_key[:-3] + ")"] = organs_amount_by_stain

        item["servicios"] = serv

    doc_data = {
        "created_at": datetime.now(),
        "version": "1"
    }

    data = {
        "doc_data": doc_data,
        "entryform": entryform,
        "center": entryform_object.company_center.center.name if entryform_object.company_center != None else ( entryform_object.company_laboratory if entryform_object.company_laboratory != None else '' ),
        "identifications": identifications,
        "case_created_by": User.objects.get(
            pk=entryform["created_by_id"]
        ).get_full_name(),
        "report_generated_by": User.objects.get(pk=user_pk).get_full_name(),
        "patologos": patologos,
    }

    if language == 'en':
        return render(request, "app/template_resumen_report_en.html", data)

    return render(request, "app/template_resumen_report_es.html", data)
