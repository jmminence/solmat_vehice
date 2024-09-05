import json
import urllib

from django.conf import settings
from django.db.models import Count
from django.shortcuts import get_object_or_404

from backend.models import Organ, SampleExams, Sample, Identification
from lab.models import Case, CassetteOrgan, UnitDifference


def generate_differences(unit):
    """
    Creates :model:`lab.CassetteDifference` for any
    :model:`backend.Organ` that it's present in a Unit
    but not in any of its :model:`lab.Cassette`.
    Returns True if any difference is generated.
    """
    cassettes_pk = unit.cassettes.all().values_list("id", flat=True)
    cassettes_organs = list(
        CassetteOrgan.objects.filter(cassette_id__in=cassettes_pk)
        .values("organ")
        .annotate(organ_count=Count("organ"))
        .order_by()
    )
    unit_organs = list(
        unit.organunit_set.values("organ")
        .annotate(organ_count=Count("organ"))
        .order_by()
    )

    organ_groups = Organ.objects.filter(organ_type=2).values_list("pk", flat=True)
    has_organ_group = unit.organunit_set.filter(organ_id__in=organ_groups).count() > 0

    unit_organs = {
        unit_organ["organ"]: unit_organ["organ_count"] for unit_organ in unit_organs
    }
    cassettes_organs = {
        cassettes_organ["organ"]: cassettes_organ["organ_count"]
        for cassettes_organ in cassettes_organs
    }

    organs = Organ.objects.all()

    has_differences = False
    for organ in organs:
        if organ.id in cassettes_organs or organ.id in unit_organs:
            current_difference = 0
            if organ.id in cassettes_organs and not organ.id in unit_organs:
                if not has_organ_group:
                    current_difference = cassettes_organs[organ.id]
            elif organ.id in unit_organs and not organ.id in cassettes_organs:
                current_difference = -(unit_organs[organ.id])
            else:
                current_difference = cassettes_organs[organ.id] - unit_organs[organ.id]

            difference = current_difference

            if difference > 0 or difference < 0:
                has_differences = True
                unit_difference, created = UnitDifference.objects.update_or_create(
                    unit=unit, organ=organ, defaults={"difference": difference}
                )

    return has_differences


def change_case_step(case_pk, step):
    """
    Updates the given :model:`workflow.Form` to the given
    step, regardless of current state.
    """

    case = get_object_or_404(Case, pk=case_pk)
    form = case.forms.first()

    if form.reception_finished and int(step) in (2, 3):
        form.reception_finished = False
        form.reception_finished_at = None
    form.state_id = step
    form.save()

    return (case, form)


def make_request_to_portal(endpoint, context, method="POST"):
    URL = f"{settings.PORTAL_BASE_ENDPOINT}/{endpoint}"
    headers = {
        "Authorization": settings.PORTAL_TOKEN,
        "Accept": "application/json",
        "Application-Accept": "application/json",
        "Content-Type": "application/json",
    }
    data = str(json.dumps(context)).encode("utf-8")
    request = urllib.request.Request(URL, data=data, headers=headers, method=method)

    try:
        response = urllib.request.urlopen(request)
    except urllib.error.HTTPError as e:
        return ("ERROR", e.code)
    else:
        data = json.loads(
            response.read().decode(response.info().get_param("charset") or "utf-8")
        )
        return ("OK", data)


def get_data_from_portal(endpoint):
    URL = f"{settings.PORTAL_BASE_ENDPOINT}/{endpoint}"
    headers = {
        "Authorization": settings.PORTAL_TOKEN,
        "Accept": "application/json",
        "Application-Accept": "application/json",
        "Content-Type": "application/json",
    }
    request = urllib.request.Request(URL, headers=headers, method="GET")


    try:
        response = urllib.request.urlopen(request)
    except urllib.error.HTTPError as e:
        return ("ERROR", e.code)
    else:
        data = json.loads(
            response.read().decode(response.info().get_param("charset") or "utf-8")
        )
        return ("OK", data)


def create_or_update_analysisform_in_portal(entryform, analysisform):
    identifications = entryform.identification_set.all().order_by("id")
    samples = entryform.sample_set.all()
    sample_exams = SampleExams.objects.filter(stain=analysisform.stain, exam=analysisform.exam, sample__in=samples)

    samples_for_analysisform = Sample.objects.filter(pk__in=sample_exams.values_list("sample_id", flat=True))
    identifications_for_analysisform = (
        Identification.objects.filter(
            pk__in=samples_for_analysisform.values_list("identification_id", flat=True)
        ).order_by("id")
    )

    groups = []
    names = []
    for identification in identifications_for_analysisform:
        groups.append(identification.group)
        names.append(identification.cage)

    groups = " / ".join(set(groups))
    names = " / ".join(names)

    researches = list(analysisform.research_set.all().values_list("code", flat=True))
    users = {
        "approver": "Carlos Sandoval Hurtado M.V, MSc",
        "assigned": analysisform.patologo.userprofile.signing,
    }


    context = {
        "idREPORT": analysisform.id,
        "REPORT_NUMBER": analysisform.report_code,
        "ENTRY_NUMBER": entryform.no_caso,
        "Company": entryform.customer.name,
        "idSITE": entryform.center,
        "idSPECIE": entryform.specie_id,
        "idLARVALSTAGE": entryform.larvalstage_id,
        "TANK_CAGE": names,
        "IDENTIF_GROUP": groups,
        "idSOURCE_WATER": entryform.watersource_id,
        "idREPORT_ANALYSIS_TYPE": analysisform.exam_id,
        "sampleDate": entryform.sampled_at.isoformat()
        if entryform.sampled_at
        else entryform.created_at.isoformat(),
        "entryDate": entryform.created_at.isoformat(),
        "VERSION": 1,
        "study_group": json.dumps(researches),
        "users": users,
    }
    ENDPOINT = "reports"
    exists_in_portal = get_data_from_portal(f"{ENDPOINT}/{analysisform.id}")

    if exists_in_portal[0] == "OK" and not exists_in_portal[1]["idREPORT"] is None:
        return make_request_to_portal(
            f"{ENDPOINT}/{analysisform.id}", context, method="PATCH"
        )
    else:
        return make_request_to_portal(ENDPOINT, context)


def create_or_update_identification_in_portal(identification, analysisform_id):
    context = {
        "idIDENTIFICATIONS": identification.id,
        "idREPORT": analysisform_id,
        "NAME": identification.cage,
    }

    ENDPOINT = "identifications"
    exists_in_portal = get_data_from_portal(f"{ENDPOINT}/{identification.id}")

    if (
        exists_in_portal[0] == "OK"
        and not exists_in_portal[1]["idIDENTIFICATIONS"] is None
    ):
        return make_request_to_portal(
            f"{ENDPOINT}/{identification.id}", context, method="PATCH"
        )
    else:
        return make_request_to_portal(ENDPOINT, context)


def create_or_update_unit_in_portal(unit):
    context = {
        "idUNITS": unit.id,
        "correlative": unit.correlative,
        "identification_id": unit.identification_id,
    }

    ENDPOINT = "units"
    exists_in_portal = get_data_from_portal(f"{ENDPOINT}/{unit.id}")

    if exists_in_portal[0] == "OK" and not exists_in_portal[1]["idUNITS"] is None:
        return make_request_to_portal(f"{ENDPOINT}/{unit.id}", context, method="PATCH")
    else:
        return make_request_to_portal(ENDPOINT, context)


def create_or_update_sample_in_portal(sample, slide_id=None):
    context = {
        "idSAMPLES": sample.id,
        "idIDENTIFICATIONS": sample.identification_id,
        "NAME": f"{sample.identification.cage} ({sample.index})",
        "slideId": slide_id,
    }

    ENDPOINT = "samples"
    exists_in_portal = get_data_from_portal(f"{ENDPOINT}/{sample.id}")

    if exists_in_portal[0] == "OK" and not exists_in_portal[1]["idSAMPLES"] is None:
        return make_request_to_portal(
            f"{ENDPOINT}/{sample.id}", context, method="PATCH"
        )
    else:
        return make_request_to_portal(ENDPOINT, context)
