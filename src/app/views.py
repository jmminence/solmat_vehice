import json
from random import sample
import pdfkit
import io
import locale
import tempfile, os
from PyPDF2 import PdfReader, PdfWriter
from decimal import Decimal



from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q, Count
from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View
from django.views.decorators.cache import never_cache
from django.urls import reverse
from django.template.loader import render_to_string


from accounts.models import *
from backend.models import *
from mb.models import Pool
from workflows.models import *


@login_required
def home(request):
    """
    Display website homepage with a list of services and report data

    **Context**

    ``services``
        A list of :model:`backend.Service`
    ``years``
        A list of dates according to all :model:`backend.EntryForm`
    ``top_10``
        Count of last 10 :model:`backend.Exam`

    **Template**

    :template:`app/home.html`
    """
    services = Exam.objects.values("id", "name")
    dates = (
        EntryForm.objects.all()
        .values_list("created_at", flat=True)
        .order_by("-created_at")
        .distinct()
    )
    years = []
    for d in dates:
        if d and not d.year in years:
            years.append(d.year)
    cursor1 = connection.cursor()
    data1 = cursor1.execute(
        """
        SELECT e.id, e.`name`, COUNT(*) as count
        FROM backend_sample s
        INNER JOIN backend_analysisform a ON s.entryform_id = a.entryform_id
        INNER JOIN backend_exam e ON a.exam_id = e.id
        INNER JOIN workflows_form f ON a.entryform_id = f.object_id
        WHERE f.flow_id = 1 AND f.cancelled = 0
        GROUP BY e.`name`, e.id
        ORDER BY count DESC;
    """
    )
    top_10 = cursor1.fetchmany(10)
    top_10 = json.dumps(top_10)
    return render(
        request,
        "app/home.html",
        {"services": services, "years": years, "top_10": top_10},
    )


@login_required
def show_users(request):
    """
    Display a listing of Users

    **Context**

    ``user_list``
        A list of :model:`auth.User`

    **Template**

    :template:`app/users.html`
    """
    users = User.objects.all()
    usuarios = []
    for usuario in users:
        aux = {
            "user": usuario.first_name.title() + " " + usuario.last_name.title(),
            "email": usuario.email,
            "id": usuario.id,
            "estado": usuario.is_active,
            "admin": usuario.is_superuser,
        }
        usuarios.append(aux)
    return render(request, "app/users.html", {"user_list": usuarios})


@login_required
def show_clientes(request):
    """
    Display a listing of Customer

    **Context**

    ``customer_list``
        A list of :model:`backend.Customer`

    **Template**

    :template:`app/clientes.html`
    """
    customers = Customer.objects.all()
    return render(request, "app/clientes.html", {"customer_list": customers})


@login_required
def show_analisis(request):
    """
    Display a listing of Exam

    **Context**

    ``exam_list``
        A list of :model:`backend.Exam`

    **Template**

    :template:`app/analisis.html`
    """
    exams = Exam.objects.all()
    return render(request, "app/analisis.html", {"exam_list": exams})


@login_required
def show_ingresos(request):
    """
    Display a listing of EntryForm

    **Context**

    ``entryForm_list``
        A list of :model:`backend.EntryForm`
    ``edit``
        A boolean value to check if the current user can or cannot edit EntryForms
    ``eliminar``
        A boolean value to check if the current user can or cannot delete EntryForms

    **Template**

    :template:`app/ingresos.html`
    """
    up = UserProfile.objects.filter(user=request.user).first()
    editar = up.profile_id in (1, 3) or request.user.is_superuser
    eliminar = request.user.is_superuser
    check_forms = Form.objects.filter(content_type__model="entryform", state__id=1)

    return render(
        request,
        "app/ingresos.html",
        {"edit": editar, "eliminar": eliminar},
    )


@login_required
def tabla_ingresos(request):
    up = UserProfile.objects.filter(user=request.user).first()
    form = Form.objects.filter(content_type__model="entryform").order_by("-object_id")

    draw = int(request.GET.get("draw"))
    length = int(request.GET.get("length"))
    search = request.GET.get("search[value]")
    start = int(request.GET.get("start")) + 1

    if up.profile_id in (4, 5):
        assigned_areas = UserArea.objects.filter(user=request.user, role=0)
        pks = [request.user.id]

        for user_area in assigned_areas:
            users = (
                UserArea.objects.filter(area=user_area.area)
                .exclude(user=request.user)
                .values_list("user", flat=True)
            )
            pks.extend(users)

        pathologists = User.objects.filter(
            Q(userprofile__profile_id__in=(4, 5)) | Q(userprofile__is_pathologist=True)
        ).filter(pk__in=pks)

        ids = EntryForm.objects.filter(
            analysisform__patologo_id__in=pathologists
        ).values_list("id")
        form_ids = form.filter(object_id__in=ids).values_list("id")
        state_ids = Form.objects.filter(
            content_type__model="analysisform", parent_id__in=form_ids
        ).values_list("parent_id")
        form = form.filter(id__in=state_ids)

    if search:
        cases = EntryForm.objects.filter(
            Q(pk__in=form.values_list("object_id", flat=True)),
            Q(no_caso__icontains=search)
            | Q(customer__name__icontains=search)
            | Q(center__icontains=search)
            | Q(no_request__icontains=search),
        )

        form = form.filter(object_id__in=cases.values_list("id", flat=True))

    form_paginator = Paginator(form, length)

    context = {
        "draw": draw + 1,
        "recordsTotal": form_paginator.count,
        "recordsFiltered": form_paginator.count,
        "data": [],
    }

    for page in form_paginator.page_range:
        page_start = form_paginator.get_page(page).start_index()
        if page_start == start:
            form_page = form_paginator.get_page(page).object_list
            for form in form_page:
                row = {
                    "DT_RowId": f"form-{form.pk}",
                    "case":
                        {
                            'id': form.content_object.id,
                            'no_request': form.content_object.no_request,
                            'no_caso': form.content_object.no_caso,
                            'center': form.content_object.company_center.center.name if  form.content_object.company_center != None else form.content_object.company_laboratory,
                            'customer': form.content_object.customer_id,
                            'created_at': form.content_object.created_at,
                        } 
                    ,
                    "form": model_to_dict(form),
                    "step": model_to_dict(form.state.step, fields=["name", "tag"]),
                }

                # If no customer is assigned to the entryform
                if form.content_object.customer:
                    row.update(
                        {"customer": model_to_dict(form.content_object.customer, exclude=['center'])}
                    )

                # Get current analysis progress for the entryform

                analysis_pk = form.content_object.analysisform_set.all().values_list(
                    "id", flat=True
                )
                analysis_forms = Form.objects.filter(
                    content_type__model="analysisform",
                    object_id__in=analysis_pk,
                    form_closed=False,
                    cancelled=False,
                )
                has_in_progress = analysis_forms.count() > 0

                row.update({"progress": has_in_progress})
                context["data"].append(row)

            break

    return JsonResponse(context)


@login_required
def show_estudios(request):
    """
    Display a listing of Research

    **Context**

    ``research_list``
        A list of :model:`backend.Research`
    ``edit``
        A boolean value to check if the current user can or cannot edit EntryForms
    ``eliminar``
        A boolean value to check if the current user can or cannot delete EntryForms

    **Template**

    :template:`app/ingresos.html`
    """
    up = UserProfile.objects.filter(user=request.user).first()
    editar = 1
    eliminar = editar and request.user.is_superuser
    estudios = Research.objects.all()
    clients_available = Customer.objects.all()
    users_available = User.objects.all()

    form = Form.objects.filter(content_type__model="entryform").order_by("-object_id")

    return render(
        request,
        "app/estudios.html",
        {
            "research_list": estudios,
            "can_edit": editar,
            "can_delete": eliminar,
            "clients_available": clients_available,
            "users_available": users_available,
        },
    )


@login_required
def show_ingresos_by_id(request, form_id):
    """
    Display a listing of Research

    **Context**

    ``research_list``
        A list of :model:`backend.Research`
    ``edit``
        A boolean value to check if the current user can or cannot edit EntryForms
    ``eliminar``
        A boolean value to check if the current user can or cannot delete EntryForms

    **Template**

    :template:`app/ingresos.html`
    """
    up = UserProfile.objects.filter(user=request.user).first()

    if up.user.is_staff:
        form = Form.objects.filter(content_type__model="entryform")
    else:
        form = Form.objects.filter(
            content_type__model="entryform", state__step__actors__profile=up.profile
        )

    return render(request, "app/ingresos.html", {"entryForm_list": form})


@login_required
def new_ingreso(request):
    """
    Creates a new :model:`backend.EntryForm` storing the current user and the case number which
    is generated from the count of all :model:`backend.Form` in the initial process with no Parent
    process.

    Redirects to :view:`workflows.flow`
    """
    flow = Flow.objects.get(pk=1)
    entryform = EntryForm.objects.create(created_by=request.user)
    no_caso_initial = 10000

    last_form=Form.objects.filter(flow_id=1, parent_id=None).last()
    last_entry=EntryForm.objects.get(id=last_form.object_id)
    last_no_caso=int(last_entry.no_caso[1:])

    new_no_caso = 10000 + (last_no_caso - 10000) +1
    #no_caso = "{:05}".format(new_no_caso) 

    """folio = (
        "000000"
        + str(last_no_caso + 1)
    )[-5:]"""
    no_caso = "V{0}".format(new_no_caso)
    #no_caso = "V{0}".format(folio)
    entryform.no_caso = no_caso
    entryform.save()
    form = Form.objects.create(
        content_object=entryform, flow=flow, state=flow.step_set.first().state
    )
    return redirect("/workflow/" + str(form.id))


@login_required
def new_research(request):
    """
    Accepts POST request to create or update a :model:`backend.Research`
    if not id is given it will create a new Research, if an id is given then it will
    search for that Research and update it.
    """
    var_post = request.POST.copy()
    clients = var_post.getlist("clients", [])
    id = var_post.get("id", None)
    name = var_post.get("name")
    init_date = var_post.get("init_date")
    external_responsible = var_post.get("external_responsible")
    internal_responsible = var_post.get("internal_responsible")
    type = var_post.get("type")
    description = var_post.get("description")
    status = int(var_post.get("status"))

    if not id:
        start_counter_research = 59
        research_counter = Research.objects.count()
        next_code = str(start_counter_research + research_counter + 1)

        if len(next_code) == 2:
            code = "E00" + next_code
        elif len(next_code) == 3:
            code = "E0" + next_code
        else:
            code = "E" + next_code

        study = Research.objects.create(
            code=code,
            name=name,
            description=description,
            type=int(type),
            init_date=datetime.strptime(init_date, "%d/%m/%Y %H:%M"),
            status=status,
            external_responsible=external_responsible,
            internal_responsible_id=internal_responsible,
        )
        clients_obj = Customer.objects.filter(id__in=clients)
        for cl in clients_obj:
            study.clients.add(cl)

        return redirect("/research/" + str(study.id))
    else:
        study = Research.objects.get(pk=id)
        study.name = name
        study.description = description
        study.type = int(type)
        study.init_date = datetime.strptime(init_date, "%d/%m/%Y %H:%M")
        study.status = status
        study.external_responsible = external_responsible
        study.internal_responsible_id = internal_responsible
        study.save()

        # Quitando servicios de clientes eliminados
        for c in study.clients.all():
            if str(c.id) not in clients:
                for s in study.services.filter(entryform__customer_id=c):
                    study.services.remove(s)

        study.clients.clear()

        clients_obj = Customer.objects.filter(id__in=clients)
        for cl in clients_obj:
            study.clients.add(cl)

        return redirect("/research/" + str(study.pk))


@login_required
def show_workflow_main_form(request, form_id):
    """
    Display a resource form for :model:`workflow.Form`

    **Context**

    ``form``
        An instance of :model:`workflow.Form`
    ``form_id``
        A pk to a :model:`workflow.Form`
    ``entryform_id``
        A pk to a :model:`backend.EntryForm`
    ``edit``
        A boolean value that's true if the current User can edit the current Form
    ``edit_case``
        A boolean value that's true if the current User can edit the Form's Case

    **Template**

    :template:`app/workflow_main.html`
    """
    form = Form.objects.get(pk=form_id)
    entryform_id = form.content_object.id
    up = UserProfile.objects.filter(user=request.user).first()
    edit_case = not form.form_closed and (
        up.profile.id in (1, 2, 3) or request.user.is_superuser
    )
    actor = Actor.objects.filter(profile_id=request.user.userprofile.profile_id).first()
    edit = (
        1
        if actor.permission.filter(from_state_id=1, type_permission="w").first()
        else 0
    )
    if not edit:
        return show_ingresos(request)

    return render(
        request,
        "app/workflow_main.html",
        {
            "form": form,
            "form_id": form_id,
            "entryform_id": entryform_id,
            "edit": edit,
            "closed": 0,
            "edit_case": edit_case,
        },
    )


def make_pdf_file(id, url):
    import os

    import pdfkit
    from django.conf import settings

    d = datetime.today().strftime("%Y%m%d%H%M%S")
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))

    options = {
        "quiet": "",
        "page-size": "A4",
        "encoding": "UTF-8",
        "margin-top": "5mm",
        "margin-left": "5mm",
        "margin-right": "5mm",
        "margin-bottom": "10mm",
        "load-error-handling": "ignore",
        "disable-javascript": "",
        "footer-center": "[page]",
        # 'footer-html': 'www.google.com'
    }

    urlsitio = settings.SITE_URL + url + str(id)
    pdf = pdfkit.from_url(urlsitio, False, options=options)
    return pdf


def make_pdf_file2(id, url, filename, userId):
    import pdfkit

    d = datetime.today().strftime("%Y%m%d%H%M%S")

    options = {
        "quiet": "",
        "page-size": "A4",
        "encoding": "UTF-8",
        "margin-top": "5mm",
        "margin-left": "15mm",
        "margin-right": "15mm",
        "margin-bottom": "10mm",
        "load-error-handling": "ignore",
        "disable-javascript": "",
        "footer-center": "[page]",
        # 'footer-html': 'www.google.com'
    }

    if settings.DEBUG:
        file_path = settings.BASE_DIR + settings.MEDIA_URL + "pdfs/" + filename
    else:
        file_path = settings.MEDIA_ROOT + "/pdfs/" + filename

    urlsitio = settings.SITE_URL + url + str(id) + "/" + str(userId)
    pdfkit.from_url(urlsitio, file_path, options=options)


@login_required
def download_report(request, id):
    """
    Creates a PDF file from a template, and generates a file download for it
    """
    pdf = make_pdf_file(id, "/template-report/")
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="informe.pdf"'

    return response


def template_report(request, id):
    """
    Generates the template to be converted to PDF and downloaded

    **Parameters**
    ``id``
        A pk to an instance of :model:`backend.AnalysisForm`

    **Context**

    ``analisis``
        An instance of :model:`backend.AnalysisForm`
    ``report``
        A list of :model:`backend.Report` related to the :model:`backend.AnalysisForm`
    ``report_final``
        The last item for :model:`backend.ReportFinal` related to the :model:`backend.AnalysisForm`

    **Template**

    :template:`app/template_report.html`
    """
    analisis = AnalysisForm.objects.get(id=int(id))
    return render(
        request,
        "app/template_report.html",
        {"analisis": analisis},
    )


@login_required
def download_reception(request, id):
    """Generates a PDF file for a Reception form to be downloaded"""
    pdf = make_pdf_file("{0}/{1}".format(id, request.user.id), "/template-reception/")
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="comprobante.pdf"'

    return response


@login_required
def quotes(request):
    quotes = Quote.objects.filter(active=True)
    return render(request, 'app/quotes.html', {'quotes': quotes})

@login_required
def add_quote(request):
    return render(request, 'app/quote/form_quote.html', {'title': 'NUEVA COTIZACIÓN'})

@login_required
def edit_quote(request, id):
    get_object_or_404(Quote, pk=id)
    return render(request, 'app/quote/form_quote.html', {'quote_id': id, 'title': 'MODIFICAR COTIZACIÓN'})


def get_resume_file(user, formId, lang):
    """Return the pdf file with an overview of the current state of a :model:`backend.AnalysisForm`"""
    form = Form.objects.get(pk=formId)
    entryForm = EntryForm.objects.get(id=form.content_object.id)
    last_case_version = (
        CaseVersion.objects.filter(entryform=entryForm)
        .order_by("-generated_at")
        .first()
    )

    lang_option = 1
    for n, l in RESUME_DOCUMENT_LANG:
        if l == lang:
            lang_option = n
    last_doc = (
        DocumentCaseResume.objects.filter(
            entryform=entryForm,
        )
        .order_by("-created_at")
        .first()
    )

    doc_final = None

    # Primero valido si existe un documento que este al dia con la version del caso,
    # si no existe entonce si o si creo un documento nuevo
    if last_doc:
        if last_doc.case_version.version < last_case_version.version:
            # Caso desactualizado, se debe crear uno nuevo si o si
            # porque aun nadie ha creado un documento con la ultima version del caso
            new_version = last_doc.version + 1
            file_base_name = (
                "Resumen_"
                + str(entryForm.no_caso)
                + "_"
                + lang.upper()
                + "_v"
                + str(new_version)
                + "_"
                + str(int(datetime.now().timestamp()))
                + ".pdf"
            )
            file_name = (
                "Resumen_"
                + str(entryForm.no_caso)
                + "_"
                + lang.upper()
                + "_v"
                + str(new_version)
                + ".pdf"
            )

            doc_final = DocumentCaseResume.objects.create(
                entryform=entryForm,
                filename=file_name,
                file=file_base_name,
                lang=lang_option,
                case_version=last_case_version,
                version=new_version,
                generated_by=user,
            )
            make_pdf_file2(
                entryForm.pk, "/template-resumen-report/", file_base_name, user.pk
            )

        else:
            # Caso actualizado, se debe verificar si existe un documento
            # del usuario generado con la ultima version y con el lenguaje solicitado
            temp_doc = DocumentCaseResume.objects.filter(
                entryform=entryForm,
                generated_by=user,
                lang=lang_option,
                case_version=last_case_version,
                version=last_doc.version,
            ).first()
            if temp_doc:
                doc_final = temp_doc
            else:
                file_base_name = (
                    "Resumen_"
                    + str(entryForm.no_caso)
                    + "_"
                    + lang.upper()
                    + "_v"
                    + str(last_doc.version)
                    + "_"
                    + str(int(datetime.now().timestamp()))
                    + ".pdf"
                )
                file_name = (
                    "Resumen_"
                    + str(entryForm.no_caso)
                    + "_"
                    + lang.upper()
                    + "_v"
                    + str(last_doc.version)
                    + ".pdf"
                )
                doc_final = DocumentCaseResume.objects.create(
                    entryform=entryForm,
                    filename=file_name,
                    file=file_base_name,
                    lang=lang_option,
                    case_version=last_case_version,
                    version=last_doc.version,
                    generated_by=user,
                )
                make_pdf_file2(
                    entryForm.pk, "/template-resumen-report/", file_base_name, user.pk
                )
    else:
        # Creo el primer documento del caso
        file_base_name = (
            "Resumen_"
            + str(entryForm.no_caso)
            + "_"
            + lang.upper()
            + "_v1_"
            + str(int(datetime.now().timestamp()))
            + ".pdf"
        )

        file_name = "Resumen_" + str(entryForm.no_caso) + "_" + lang.upper() + "_v1.pdf"

        if not last_case_version:
            last_case_version = CaseVersion.objects.create(
                entryform_id=entryForm.id, version=1, generated_by_id=user.pk
            )

        doc_final = DocumentCaseResume.objects.create(
            entryform=entryForm,
            filename=file_name,
            file=file_base_name,
            lang=lang_option,
            case_version=last_case_version,
            version=1,
            generated_by=user,
        )

        make_pdf_file2(
            entryForm.pk, "/template-resumen-report/", file_base_name, user.pk
        )

    return doc_final


@never_cache
def download_resumen_report(request, id):
    """Downloads a PDF file for a :model:`backend.AnalysisForm` resume"""
    var_get = request.GET.copy()
    lang = var_get.get("lang", "es")
    form = Form.objects.get(pk=id)
    entryform = form.content_object

    options = {
        "quiet": "",
        "page-size": "A4",
        "encoding": "UTF-8",
        "margin-top": "5mm",
        "margin-left": "5mm",
        "margin-right": "5mm",
        "margin-bottom": "10mm",
        "footer-center": "[page]",
    }
    url = reverse("template_resumen_report", kwargs={"id": entryform.id, "userId": request.user.id}) + "?lang={}".format(lang)
    pdf = pdfkit.from_url(settings.SITE_URL + url, False, options=options)
    binary_pdf = io.BytesIO(pdf)
    response = HttpResponse(binary_pdf.read(), content_type="application/pdf")
    response["Content-Disposition"] = "inline;filename=" + f"Resumen_{id}.pdf"
    return response

def show_log_actions(request, id):
    from django.http import JsonResponse

    actions = DocumentResumeActionLog.objects.filter(document__entryform_id=id)
    action_list = []

    for action in actions:
        action_dict = {}
        action_dict["done_by"] = action.done_by.get_full_name().title()
        type_v = ""
        if action.mail_action:
            type_v = "Envío por Mail"
        else:
            type_v = "Descarga Directa"
        action_dict["type"] = type_v
        action_dict["version"] = action.document.version
        action_dict["action_date"] = action.action_date.strftime("%d/%m/%Y %H:%M")
        action_list.append(action_dict)
    return JsonResponse({"ok": True, "data": action_list})


def template_reception(request, id, userId):
    entryform = EntryForm.objects.values().get(pk=id)
    entryform_object = EntryForm.objects.get(pk=id)

    subflow = entryform_object.get_subflow
    entryform["subflow"] = subflow
    identifications = list(
        Identification.objects.filter(entryform=entryform["id"]).values()
    )

    samples = Sample.objects.filter(entryform=entryform["id"]).order_by("index")
    entryform["entryform_type"] = (
        entryform_object.entryform_type.name if entryform_object.entryform_type else ""
    )
    entryform["entry_format"] = (
        entryform_object.get_entry_format_display
        if entryform_object.entry_format
        else ""
    )
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
                        {"name": sE.organ.name, "id": sE.organ.id}
                    )
                except:
                    sampleExa[sE.exam_id] = {
                        "exam_id": sE.exam_id,
                        "exam_name": sE.exam.name,
                        "exam_type": sE.exam.service_id,
                        "stain": sE.stain.abbreviation.upper() if sE.stain else "N/A",
                        "sample_id": sE.sample_id,
                        "organ_id": [{"name": sE.organ.name, "id": sE.organ.id}],
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
        model_to_dict(entryform_object.customer) if entryform_object.customer else None
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

    data = {
        "entryform": entryform,
        "center": entryform_object.company_center.center.name if entryform_object.company_center != None else ( entryform_object.company_laboratory if entryform_object.company_laboratory != None else '' ),
        "identifications": identifications,
        "case_created_by": User.objects.get(
            pk=entryform["created_by_id"]
        ).get_full_name(),
        "requested": datetime.now(),
        "report_generated_by": User.objects.get(pk=userId).get_full_name(),
        "patologos": patologos,
    }

    return render(request, "app/template_reception.html", data)


def template_resumen_report(request, id, userId):
    lang = request.GET.get("lang", None)
    entryform = EntryForm.objects.get(pk=id)
    created_at = AnalysisForm.objects.filter(entryform_id=id).last().created_at
    analysisforms = AnalysisForm.objects.filter(entryform = entryform).exclude(exam__chargeable=False)
    exams_active = []

    for analysisform in analysisforms:
        if(analysisform.process_status != "Anulado"):
            exams_active.append(analysisform)

    # We must obtain the services in which each identification has a sample for.
    # Thus we loop over all identifications, get the related sample exam, grouping
    # Exam, Stains, and Organs.

    exams = {}
    for identification in entryform.identification_set.all():
        samples = Sample.objects.filter(entryform=entryform, identification=identification)
        sample_exams_all = (
            SampleExams
            .objects
            .filter(sample__in=samples)
            .values("exam_id", "stain_id", "organ_id")
            .annotate(
                exam_count=Count("exam_id"),
                stain_count=Count("stain_id"),
                organ_count=Count("organ_id")
            ).order_by()
        )

        # Filter samples active
        sample_exams = []
        for exam_active in exams_active:
            for sample_exam in sample_exams_all:
                if sample_exam["exam_id"] == exam_active.exam.id and sample_exam["stain_id"] == exam_active.stain_id:
                    sample_exams.append(sample_exam)

        exams[identification.id] = {
            "identification": identification,
            "unit_count": identification.unit_set.count(),
            "services": {}
        }
        for sample_exam in sample_exams:
            key = (sample_exam["exam_id"], sample_exam["stain_id"])
            if not key in exams[identification.id]["services"]:
                exam = Exam.objects.get(pk=sample_exam["exam_id"])
                stain = Stain.objects.get(pk=sample_exam["stain_id"])
                row = {
                    "exam": exam,
                    "stain": stain,
                    "organs": {}
                }

                exams[identification.id]["services"][key] = row

            if not sample_exam["organ_id"] in exams[identification.id]["services"][key]["organs"]:
                organ = Organ.objects.get(pk=sample_exam["organ_id"])
                exams[identification.id]["services"][key]["organs"][organ.id] = {
                    "organ": organ,
                    "count": sample_exam["organ_count"]
                }

        pools = Pool.objects.filter(identification=identification)
        organ = ""
        for pool in pools:
            organ_list = []
            for organ_unit in pool.organ_unit.all():
                organ_list.append(organ_unit.organ.name)

            organ = "/".join(organ_list)

            for exam in pool.exams.all():
                key = (exam.id,exam.stain.id)
                if not key in exams[identification.id]["services"]:
                    row = {
                        "exam": exam,
                        "stain": exam.stain,
                        "organs": {}
                    }

                    exams[identification.id]["services"][key] = row

                if organ not in exams[identification.id]["services"][key]["organs"]:
                    exams[identification.id]["services"][key]["organs"][organ] = {
                    "organ": organ,
                    "count": 1
                    }
                else:
                    count = exams[identification.id]["services"][key]["organs"][organ]["count"]
                    count += 1
                    exams[identification.id]["services"][key]["organs"][organ]["count"] = count

    try:
        created_by = entryform.created_by.get_full_name()
        generated_by = entryform.created_by.get_full_name()
    except AttributeError:
        pass

    context = {
        "entryform": entryform,
        "center": entryform.company_center.center.name if entryform.company_center != None else ( entryform.company_laboratory if entryform.company_laboratory != None else '' ),
        "entry_format": entryform.get_entry_format_display(),
        "date":  created_at,
        "exams": exams,
        "created_by": created_by,
        "generated_by": generated_by
    }

    if lang and lang == "en":
        return render(request, "app/template_resumen_report_en.html", context)
    return render(request, "app/template_resumen_report_es.html", context)


@login_required
def show_patologos(request, all):
    """
    Lists :model:`backend.AnalysisForm` according to the current user,
    allowing different filters to be used to display detailed data related
    to all items.

    **Parameters**
    ``all``
        A pk to an instance of :model:`backend.AnalysisForm`

    **Context**

    ``casos``
        A list of Dictionaries containing detailed information about Cases
    ``patologos``
        A list of :model:`auth.User` filtered by Pathologist role
    ``edit``
        A permision check if the current User can or cannot edit Cases
    ``all``

    **Template**

    :template:`app/patologos.html`
    """
    up = UserProfile.objects.filter(user=request.user).first()
    data = []
    patologos = list(
        User.objects.filter(
            Q(is_active=True) & (Q(userprofile__profile_id__in=[4, 5]) | Q(userprofile__is_pathologist=True))
        ).values()
    )
    editar = up.profile_id in (1, 2, 3)

    return render(
        request,
        "app/patologos.html",
        {"patologos": patologos, "edit": editar, "all": all},
    )


@login_required
def tabla_patologos(request):
    up = UserProfile.objects.filter(user=request.user).first()

    draw = int(request.GET.get("draw"))
    length = int(request.GET.get("length"))
    search = request.GET.get("search[value]")
    start = int(request.GET.get("start")) + 1

    lower_open_day_limit = request.GET.get("lower_open_day_limit")
    upper_open_day_limit = request.GET.get("upper_open_day_limit")

    lower_tardy_day_limit = request.GET.get("lower_tardy_day_limit")
    upper_tardy_day_limit = request.GET.get("upper_tardy_day_limit")

    selected_pathologists = request.GET.get("selected_pathologists")

    unassigned = request.GET.get("unassigned")

    if selected_pathologists and unassigned == 'false':
        selected_pathologists = selected_pathologists.split(",")

    all = int(request.GET.get("included_closed_cases") or 0)

    # Get AnalysisForm according to user permissions
    if request.user.is_superuser or up.profile_id in (1, 2, 3):
        analysis = (
            AnalysisForm.objects.filter(exam__isnull=False)
            .select_related("entryform", "exam")
            .order_by("-created_at")
        )
    elif up.profile_id in (4, 5):
        assigned_areas = UserArea.objects.filter(user=request.user, role=0)
        pks = [request.user.id]

        for user_area in assigned_areas:
            users = (
                UserArea.objects.filter(area=user_area.area)
                .exclude(user=request.user)
                .values_list("user", flat=True)
            )
            pks.extend(users)

        pathologists = User.objects.filter(
            Q(userprofile__profile_id__in=(4, 5)) | Q(userprofile__is_pathologist=True)
        ).filter(pk__in=pks)

        analysis = (
            AnalysisForm.objects.filter(patologo__in=pathologists, exam__isnull=False)
            .select_related("entryform", "exam")
            .order_by("-created_at")
        )

    else:
        analysis = (
            AnalysisForm.objects.filter(exam__isnull=False)
            .select_related("entryform", "exam")
            .order_by("-created_at")
        )

    patologos = list(
        User.objects.filter(
            Q(userprofile__profile_id__in=[4, 5]) | Q(userprofile__is_pathologist=True)
        ).values()
    )
    editar = up.profile_id in (1, 2, 3)

    if search:
        analysis = analysis.filter(
            Q(entryform__no_caso__icontains=search)
            | Q(entryform__customer__name__icontains=search)
            | Q(entryform__center__icontains=search)
            | Q(exam__name__icontains=search)
        )

    if selected_pathologists and unassigned == 'false':
        analysis = analysis.filter(patologo_id__in=selected_pathologists)
    elif unassigned == 'true':
        analysis = analysis.filter(patologo_id=None)


    selected_analysis = []

    analysis_paginator = Paginator(analysis, length)

    context = {
        "draw": draw + 1,
        "recordsTotal": analysis_paginator.count,
        "recordsFiltered": analysis_paginator.count,
        "data": [],
    }

    for page in analysis_paginator.page_range:
        page_start = analysis_paginator.get_page(page).start_index()
        if page_start == start:
            analysis_page = analysis_paginator.get_page(page).object_list
            for a in analysis_page:
                entryform_form = a.entryform.forms.first()
                analysisform_form = a.forms.first()

                if int(all):
                    if (
                        entryform_form
                        and not entryform_form.cancelled
                        and analysisform_form
                        and a.exam.pathologists_assignment
                        and not analysisform_form.cancelled
                    ):
                        selected_analysis.append(
                            {
                                "analysis": a,
                                "entryform_form": entryform_form,
                                "analysisform_form": analysisform_form,
                            }
                        )
                else:
                    if (
                        entryform_form
                        and not entryform_form.cancelled
                        and a.exam.pathologists_assignment
                        and analysisform_form
                        and not analysisform_form.cancelled
                        and not entryform_form.form_closed
                    ):
                        selected_analysis.append(
                            {
                                "analysis": a,
                                "entryform_form": entryform_form,
                                "analysisform_form": analysisform_form,
                            }
                        )

    for a in selected_analysis:
        days_open = 0
        days_late = 0

        deadline = AnalysisTimes.objects.filter(analysis_id=a["analysis"].id, type_deadline_id=2).last()

        if not a["analysisform_form"].form_closed:
            # Analisis en curso

            current_date = datetime.now().date()
            if deadline:
                if a["analysis"].pre_report_started and a["analysis"].pre_report_ended:
                    days_late = (
                        a["analysis"].pre_report_ended_at.date()
                        - deadline.deadline
                    ).days
                elif current_date > deadline.deadline:
                    days_late = (current_date - deadline.deadline).days

            days_open = (current_date - a["analysis"].created_at.date()).days
        else:
            # Analisis cerrado
            if a["analysis"].assignment_deadline and a["analysis"].pre_report_ended_at:
                if (
                    a["analysis"].pre_report_ended_at
                    > a["analysis"].assignment_deadline
                ):
                    days_late = (
                        a["analysis"].pre_report_ended_at
                        - a["analysis"].assignment_deadline
                    ).days

            if a["analysis"].manual_closing_date:
                days_open = (
                    a["analysis"].manual_closing_date - a["analysis"].created_at
                ).days
            else:
                days_open = (
                    a["analysisform_form"].closed_at - a["analysis"].created_at
                ).days

        if upper_open_day_limit:
            if days_open >= int(upper_open_day_limit):
                continue

        if lower_open_day_limit:
            if days_open <= int(lower_open_day_limit):
                continue

        if upper_tardy_day_limit:
            if days_late >= int(upper_tardy_day_limit):
                continue

        if lower_tardy_day_limit:
            if days_late <= int(lower_tardy_day_limit):
                continue

        samples = Sample.objects.filter(entryform=a["analysis"].entryform).values_list(
            "id", flat=True
        )
        sampleExams_counter = 0
        sampleExams = SampleExams.objects.filter(
            sample__in=samples, exam=a["analysis"].exam, stain=a["analysis"].stain
        ).select_related("organ")
        organ_types = []
        organs = []
        for se in sampleExams:
            sampleExams_counter += 1
            organs.append(se.organ.abbreviation)
            if se.organ.organ_type not in organ_types:
                organ_types.append(se.organ.organ_type)
        organ_types = set(organ_types)
        organs_text = ""
        organs_set = set(organs)

        if not None in organs_set:
            organs_text = ", ".join(list(organs_set))

        unit = ""
        if len(organ_types) > 1:
            unit = "Multiple"
        elif len(organ_types) == 1:
            if list(organ_types)[0] == 1:
                unit = "Órgano"
            else:
                unit = sampleExams.first().organ.name
        else:
            unit = "Órgano"

        parte = a["analysis"].entryform.get_subflow
        if parte == "N/A":
            parte = ""
        else:
            parte = " (Parte " + parte + ")"

        if a["analysis"].exam.group != "Otros":


            context["data"].append(
            {
                "analisis": a["analysis"].id,
                "patologo": a["analysis"].patologo_id
                if a["analysis"].patologo
                else None,
                "patologo_name": a["analysis"].patologo.first_name
                + " "
                + a["analysis"].patologo.last_name
                if a["analysis"].patologo
                else "No Asignado",
                "closed": 1 if a["analysisform_form"].form_closed else 0,
                "cancelled": 1 if a["analysisform_form"].cancelled else 0,
                "edit": not a["entryform_form"].form_closed
                and up.profile.id in (1, 2, 3)
                or request.user.is_superuser,
                "no_caso": a["analysis"].entryform.no_caso + parte,
                "exam": a["analysis"].exam.name,
                "cliente": a["analysis"].entryform.customer.name,
                "centro": a["analysis"].entryform.company_center.center.name if a["analysis"].entryform.company_center != None else ( a["analysis"].entryform.company_laboratory if a["analysis"].entryform.company_laboratory != None else ""),
                "fecha_ingreso": a["analysis"].created_at.strftime("%d/%m/%Y"),
                "dias_abierto": days_open,
                "nro_organos": sampleExams_counter,
                "entryform": a["analysis"].entryform.id,
                "entryform_form_closed": a["entryform_form"].form_closed,
                "entryform_cancelled": a["entryform_form"].cancelled,
                "organos": organs_text,
                "fecha_derivacion": a["analysis"].assignment_done_at.strftime(
                    "%d/%m/%Y"
                )
                if a["analysis"].assignment_done_at
                else "",
                "fecha_plazo": deadline.deadline.strftime("%d/%m/%Y")
                if deadline
                else "",
                "dias_atraso": days_late,
                "estado": a["analysis"].status,
                "nota_diagnostico": str(a["analysis"].score_diagnostic).replace(
                    ",", "."
                )
                if a["analysis"].score_diagnostic
                else "",
                "nota_informe": str(a["analysis"].score_report).replace(",", ".")
                if a["analysis"].score_report
                else "",
            }
        )

    return JsonResponse(context)


class ChangeLanguage(View):
    """
    Switches in the language enum in :model:`accounts.UserProfile`
    the current language for localization
    """

    def get(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
        if user_profile.language == 2:
            user_profile.language = 1
        else:
            user_profile.language = 2
        user_profile.save()
        return JsonResponse({"error": 0})

# Genera el PDF para preinvoice
def template_preinvoice(request, id):
    locale.setlocale( locale.LC_ALL, '' )
    lang = request.GET.get("lang", None)
    preinvoice = Preinvoice.objects.get(id=id)
    analysisPreinvoices = AnalysisPreinvoice.objects.filter(preinvoice_id=id)
    subtotal=0


    analysis={}
    for analysisPreinvoice in analysisPreinvoices:

        if analysisPreinvoice.analysis.exam.pricing_unit == 1:
                    samples_count = analysisPreinvoice.samples_studied
        else:
            samples = Sample.objects.filter(entryform=analysisPreinvoice.analysis.entryform).values_list("id", flat=True)
            sampleExams = SampleExams.objects.filter(sample__in=samples, exam=analysisPreinvoice.analysis.exam, stain=analysisPreinvoice.analysis.stain).values_list("sample_id", flat=True)
            samples_count = len(list(set(sampleExams)))

        total_value = round((samples_count * analysisPreinvoice.analysis.unit_value),2)
        subtotal+=total_value
        identifications=[]

        analysis[analysisPreinvoice.analysis.id] = {
            "entryform": analysisPreinvoice.analysis.entryform,
            "exam": analysisPreinvoice.analysis.exam,
            "created_at": analysisPreinvoice.analysis.created_at,
            "manual_closing_date": analysisPreinvoice.analysis.manual_closing_date,
            "samples_studied": samples_count,
            "report_code":analysisPreinvoice.analysis.report_code,
            "unit_value": analysisPreinvoice.analysis.unit_value,
            "total_value": total_value,
            "currency": analysisPreinvoice.analysis.currency,
            "identifications": {},
        }


        for identification in analysisPreinvoice.analysis.entryform.identification_set.all():
            sample_exams_all=[]

            samples = Sample.objects.filter(entryform=analysisPreinvoice.analysis.entryform, identification=identification)

            for sample in samples:
                if SampleExams.objects.filter(sample=sample.id, exam=analysisPreinvoice.analysis.exam.id, stain=analysisPreinvoice.analysis.stain.id):
                    sample_exams_all=SampleExams.objects.filter(sample=sample.id, exam=analysisPreinvoice.analysis.exam.id, stain=analysisPreinvoice.analysis.stain.id)

            for sample_exam in sample_exams_all:
                if sample_exam.exam.id == analysisPreinvoice.analysis.exam.id and sample_exam.stain.id == analysisPreinvoice.analysis.stain.id:
                    if identification.client_case_number not in analysis[analysisPreinvoice.analysis.id]["identifications"]:
                        identifications.append(identification.client_case_number)
                        analysis[analysisPreinvoice.analysis.id]["identifications"] = identifications

        if preinvoice.customer.id == 68:
            subtotal=round(subtotal,2)
            iva="-10%"
            total=round((subtotal*0.9),2)
        else:
            subtotal=round(subtotal,2)
            iva=round((subtotal*0.19),2)
            total=round((subtotal+iva),2)

    context = {
        "preinvoice": preinvoice,
        "analysis": analysis,
        "currency": analysisPreinvoices[0].analysis.currency,
        "responsible": analysisPreinvoices[0].analysis.entryform.responsible if preinvoice.pay_person == None else preinvoice.pay_person,
        "subtotal": subtotal,
        "iva": iva,
        "total": total,
    }

    if analysisPreinvoice.analysis.currency != "UF":
        lang = "en"

    if lang and lang == "en":
        return render(request, "app/template_en_preinvoice.html", context)
    return render(request, "app/template_es_preinvoice.html", context)

# Descarga el PDF para preinvoice
@never_cache
def download_preinvoice(request, id):
    """Downloads a PDF file for a :model:`backend.Preinvoice` resume"""
    var_get = request.GET.copy()
    lang = var_get.get("lang", "es")
    preinvoice = Preinvoice.objects.get(id=id)

    options = {
        "quiet": "",
        "page-size": "A4",
        "encoding": "UTF-8",
        "margin-top": "5mm",
        "margin-left": "5mm",
        "margin-right": "5mm",
        "margin-bottom": "10mm",
    }
    url = reverse("template_preinvoice", kwargs={"id": id}) + "?lang={}".format(lang)
    pdf = pdfkit.from_url(settings.SITE_URL + url, False, options=options)
    binary_pdf = io.BytesIO(pdf)
    response = HttpResponse(binary_pdf.read(), content_type="application/pdf")
    response["Content-Disposition"] = "inline;filename=" + f"Prefactura N°{preinvoice.number} {preinvoice.customer} {preinvoice.updated_at.strftime('%d-%m-%Y')}.pdf"

    return response


def download_quote(request, id):
    additional_image = request.FILES.get('additional_image')
    additional_image_url = _save_temoral_image(request, additional_image)
    
    cover_image = request.FILES.get('cover_image')
    cover_image_url = _save_temoral_image(request, cover_image)
    
    cover_image_url_default = "https://storage.googleapis.com/vehice-media/quote_background.png"
    logo_image_url =  settings.SITE_URL + "/static/assets/images/logo/vehice-logo-white.svg"
    blue_logo_image_url =  settings.SITE_URL + "/static/assets/images/logo/vehice-logo-blue.svg"
    facebook_logo_url = settings.SITE_URL + '/static/assets/images/social/facebook.svg'
    instagram_logo_url = settings.SITE_URL + '/static/assets/images/social/instagram.svg'
    linkedin_logo_url = settings.SITE_URL + '/static/assets/images/social/linkedin.svg'
    youtube_logo_url = settings.SITE_URL + '/static/assets/images/social/youtube.svg'
    
    
    quote = Quote.objects.get(pk=id)
    quote_exams = QuoteExam.objects.filter(quote_id=id)
    quote_exams_recommended = list(filter(lambda element: element.isRecommended, quote_exams))
    quote_exams_not_recommended = list(filter(lambda element: not element.isRecommended, quote_exams))
    
    # Totals to pay
    total_not_recommended = 0
    for qe in quote_exams_not_recommended:
        total_not_recommended += qe.price * qe.quantity
    
    total_recommended = 0
    for qe in quote_exams_recommended:
        total_recommended += qe.price * qe.quantity
    
    # Cover page
    options_cover = {
        "quiet": "",
        "page-size": "A4",
        "encoding": "UTF-8",
        "margin-top": "0mm",
        "margin-left": "0mm",
        "margin-right": "0mm",
        "margin-bottom": "26mm",
        "enable-local-file-access": None,
        "footer-html": settings.SITE_URL + "/static/templates-quotes/footer_template.html",
    }
    template_cover = render_to_string('app/quote/template_quote/template_quote_cover.html', {'cover_image_url_default': cover_image_url_default, 'responsible': quote.responsible, 'hast_title': len(quote.title) > 0,'title': quote.title, 'has_cover_image': cover_image_url != None, 'cover_image_url': cover_image_url})
    cover_quote = pdfkit.from_string(template_cover, False, options=options_cover,)
    
    
    # Content pages
    header_html = render_to_string("app/quote/template_quote/template_quote_header.html", {'quote_number': str(quote.id)+'-'+str(quote.created_at.year)[-2:], 'logo_image_url': logo_image_url, 'responsible': quote.responsible, 'email': quote.responsible.email.split(';')[0], 'created_at': quote.created_at})
    header_temp_file_routes = _create_temporal_file(header_html) # create temporal file
    options_content = {
        "quiet": "",
        "page-size": "A4",
        "encoding": "UTF-8",
        "margin-top": "30mm",
        "margin-left": "0mm",
        "margin-right": "0mm",
        "margin-bottom": "26mm",
        "enable-local-file-access": None,
        "header-html": settings.SITE_URL + header_temp_file_routes['relative'], # Lo que no se encuentra no es la imagen, sino la propia url que estoy asignando ya que no es publica.
        "footer-html": settings.SITE_URL + "/static/templates-quotes/footer_template.html",
    }
        # Not recommended exams
    context = {'title': 'PROPUESTA ECONÓMICA', 'additional_image_url': additional_image_url, 'services': [{'exam': qe.exam, 'quantity': qe.quantity, 'price': qe.price, 'total': (qe.quantity * qe.price).quantize(Decimal('1.000'))} for qe in quote_exams_not_recommended], 'total_to_pay': total_not_recommended, 'comment': quote.comment, 'hasComment': len(quote.comment)>0, 'hasImage': additional_image_url != None}
    template_content = render_to_string('app/quote/template_quote/template_quote_content.html', context)
    content_not_recommended = pdfkit.from_string(template_content, False, options=options_content,)
        # Recommended Exams
    if len(quote_exams_recommended) > 0:
        context = {'title': 'ANÁLISIS OPCIONALES', 'services': [{'exam': qe.exam, 'quantity': qe.quantity, 'price': qe.price, 'total': (qe.quantity * qe.price).quantize(Decimal('1.000'))} for qe in quote_exams_recommended], 'total_to_pay': total_recommended, 'hasComment': False, 'hasImage': False}
        template_content = render_to_string('app/quote/template_quote/template_quote_content.html', context)
        content_recommended = pdfkit.from_string(template_content, False, options=options_content,)
    
    
    
    
    # Back cover page
    options_back_cover = {
        "quiet": "",
        "page-size": "A4",
        "encoding": "UTF-8",
        "margin-top": "30mm",
        "margin-left": "0mm",
        "margin-right": "0mm",
        "margin-bottom": "26mm",
        "enable-local-file-access": None,
        "header-html": settings.SITE_URL + header_temp_file_routes['relative'], # Lo que no se encuentra no es la imagen, sino la propia url que estoy asignando ya que no es publica.
        "footer-html": settings.SITE_URL + "/static/templates-quotes/footer_template.html",
    }
    difference = quote.expiration_date - datetime.now().date()
    context = {'days_available': difference.days, 'blue_logo_image_url': blue_logo_image_url,
               'facebook_logo_url': facebook_logo_url, 'instagram_logo_url': instagram_logo_url,
               'linkedin_logo_url': linkedin_logo_url, 'youtube_logo_url': youtube_logo_url,
               }
    template_back_cover = render_to_string('app/quote/template_quote/template_quote_back_cover.html', context)
    back_cover_quote = pdfkit.from_string(template_back_cover, False, options=options_back_cover,)
    
    
    
    # Merge all pages
    if len(quote_exams_recommended) > 0:
        merged_pdf = merge_pdfs([cover_quote, content_not_recommended, content_recommended, back_cover_quote])
    else:
        merged_pdf = merge_pdfs([cover_quote, content_not_recommended, back_cover_quote])
    pdf_filename = f"quote_2.pdf"
    
    # Delete temporals files:
    if additional_image != None:
        delete_image(additional_image.name)
    if cover_image != None:
        delete_image(cover_image.name)
    os.remove(header_temp_file_routes['absolute']) # delete temporal-files;


    response = HttpResponse( content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
    response.write(merged_pdf)    
    return response

def merge_pdfs(pdfs):
    output = io.BytesIO()
    pdf_writer = PdfWriter()

    for pdf in pdfs:
        pdf_reader = PdfReader(io.BytesIO(pdf))
        pdf_writer.append(pdf_reader)

    pdf_writer.write(output)

    return output.getvalue()

@login_required
def services(request):
    services = list(Exam.objects.all().values())
    
    return JsonResponse(services, safe=False)

def _create_temporal_file(html_content):
    # Crear un archivo temporal
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', dir=settings.BASE_DIR + '/static/templates-quotes/')
    temp_file.write(html_content.encode('utf-8'))
    temp_file.close()
    
    path = temp_file.name.replace('\\', '/')
    split_name = path.split('/')
    
    return {'relative': '/static/templates-quotes/' + split_name[-1], 'absolute': temp_file.name}
    # return temp_file.name

def _save_temoral_image(request, additional_image):
     # Manejar la imagen adicional si se proporciona
    additional_image_path = None
    if additional_image:
        # Guardar la imagen temporalmente en MEDIA_ROOT
        additional_image_path = os.path.join(settings.MEDIA_ROOT, additional_image.name)
        with open(additional_image_path, 'wb+') as destination:
            for chunk in additional_image.chunks():
                destination.write(chunk)
        # Convertir la ruta de la imagen a una URL accesible
        additional_image_url = f"{request.scheme}://{request.get_host()}/media/{additional_image.name}"
    else:
        additional_image_url = None
    
    return additional_image_url

def delete_image(image_name):
    url_to_delete = settings.BASE_DIR + '\\public\\media\\'+image_name
    if os.path.exists(url_to_delete):
        os.remove(url_to_delete)
        return True
    return False