from datetime import datetime

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from numpy import busday_count
from django_cleanup import cleanup

from accounts.models import User
from workflows.models import Form


def entry_files_directory_path(instance, filename):
    return "uploads/template/{0}/{1}".format(instance.template.name, filename)


class Specie(models.Model):
    """Details information about the sample's species."""

    name = models.CharField(max_length=250, null=True, blank=True)
    common_name = models.CharField(max_length=250, null=True, blank=True)
    category = models.CharField(max_length=120, null=True, blank=True, verbose_name="categoria")

    def __str__(self):
        return str(self.name)

class WaterSource(models.Model):
    """Details information about the sample's water source."""

    name = models.CharField(max_length=250, null=True, blank=True)
    name_en = models.CharField(max_length=250, null=True, blank=True)
    type_of_water = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return str(self.name)


class LarvalStage(models.Model):
    """Details information about the sample's growth stage."""

    name = models.CharField(max_length=250, null=True, blank=True)
    name_en = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return str(self.name)


class Fixative(models.Model):
    """Stores information about the unit's used fixative."""

    name = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="nombre"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "fijador"
        verbose_name_plural = "fijadores"


class Service(models.Model):
    """
    Service defines the workflow to be followed,
    and the analysis availables.
    """

    name = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="nombre"
    )
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "servicio"
        verbose_name_plural = "servicios"


RESEARCH_TYPE_OPTIONS = [(1, "Estudio Vehice"), (2, "Seguimiento de rutina")]


class Research(models.Model):
    """
    Research encapsulates multiple :model:`backend.Entryform`
    with their common data.
    """

    code = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="código"
    )
    name = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="nombre"
    )
    description = models.TextField(null=True, blank=True, verbose_name="descripción")
    type = models.IntegerField(
        default=1, choices=RESEARCH_TYPE_OPTIONS, verbose_name="tipo"
    )
    init_date = models.DateTimeField(null=True, blank=True)
    clients = models.ManyToManyField("Customer", verbose_name="clientes")
    services = models.ManyToManyField(
        "AnalysisForm", verbose_name="servicios Asociados"
    )
    status = models.BooleanField(default=False, verbose_name="¿activo?")

    # Copy of user full name to avoid empty data if user is removed
    external_responsible = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="responsable externo"
    )
    internal_responsible = models.ForeignKey(
        User, null=True, on_delete=models.PROTECT, verbose_name="responsable interno"
    )

    def __str__(self):
        return self.code + " " + self.name

    class Meta:
        verbose_name = "estudio"
        verbose_name_plural = "estudios"


class Stain(models.Model):
    """
    A stain dyes a sample which allows the Pathologist
    to study certain chemicals reactions on it.

    Certain services :model:`backend.Stain` use a speficic Stain.
    """

    name = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="nombre"
    )
    abbreviation = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="abreviación"
    )
    description = models.TextField(null=True, blank=True, verbose_name="descripción")

    def __str__(self):
        return self.abbreviation

    class Meta:
        verbose_name = "tinción"
        verbose_name_plural = "tinciones"


PRICING_UNIT = ((1, "Por órgano"), (2, "Por pez"))


class Exam(models.Model):
    """Stores basic information about services done by the company."""

    name = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="nombre"
    )
    name_en = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="name"
    )
    group = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="grupo"
    )
    group_en = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="group"
    )
    description = models.TextField(null=True, blank=True)
    abbreviation = models.CharField(max_length=5, null=True, blank=True, verbose_name="abreviacion")
    stain = models.ForeignKey(
        Stain, null=True, on_delete=models.SET_NULL, verbose_name="tinción"
    )
    pathologists_assignment = models.BooleanField(
        default=True, verbose_name="asignación de patólogo"
    )
    pricing_unit = models.IntegerField(
        default=1, choices=PRICING_UNIT, verbose_name="unidad de cobro"
    )
    unit_price = models.FloatField(default=None, null=True, blank=True)
    service = models.ForeignKey(
        Service,
        null=True,
        default=1,
        on_delete=models.SET_NULL,
        verbose_name="tipo de Servicio",
    )
    subclass = models.CharField(max_length=30, null=True, blank=True, verbose_name="subclase")
    subclass_abbreviation = models.CharField(max_length=5, null=True, blank=True)
    laboratory_deadline = models.FloatField(default=None, null=True, blank=True)
    pathologist_deadline = models.FloatField(default=None, null=True, blank=True)
    review_deadline = models.FloatField(default=None, null=True, blank=True)
    chargeable = models.BooleanField(default=True, verbose_name="cobrable")
    factor_HE = models.FloatField(default=None, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "exámen"
        verbose_name_plural = "exámenes"


ORGAN_TYPE = ((1, "Órgano por sí solo"), (2, "Conjunto de órganos"), (3, "Órganos de un conjunto"))


class Organ(models.Model):
    """
    An Organ stores information about the organ itself
    but also helps as a pivot to bind different Findings to it.
    """

    name = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="nombre (ESP)"
    )
    abbreviation = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="abreviatura (ESP)"
    )
    name_en = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="nombre (EN)"
    )
    abbreviation_en = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="abreviatura (EN)"
    )
    organ_type = models.IntegerField(default=1, choices=ORGAN_TYPE, verbose_name="tipo")

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name, self.abbreviation)

    class Meta:
        verbose_name = "órgano"
        verbose_name_plural = "órganos"



TYPE_CUSTOMER = (("l", "Laboratorio"), ("e", "Empresa"))

class Center(models.Model):
    """
    A physical location where fishes are cultivated.
    """
    
    name = models.CharField(max_length=120)
    company_name = models.CharField(max_length=120, null=True, blank=True) # Borrar
    
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    country = models.CharField(max_length=250, null=True)
    region = models.CharField(max_length=250, null=True)
    location = models.CharField(max_length=250, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return str(self.name)
    class Meta:
        verbose_name = "centro"
    
    
        

class Customer(models.Model):
    """
    Stores detailed information about a Customer that request Services.
    """

    name = models.CharField(max_length=250, null=True, blank=True, verbose_name="nombre")
    company = models.CharField(max_length=250, null=True, blank=True, verbose_name="empresa")
    corporate_name = models.CharField(max_length=250, null=True, blank=True, verbose_name="razon_social")
    country = models.CharField(max_length=250, null=True, blank=True, verbose_name="pais")
    type_customer = models.CharField(max_length=250, null=True, blank=True, verbose_name="Tipo de Cliente")
    inter_lab = models.BooleanField(default=False)
    rut = models.CharField(max_length=250, null=True, blank=True, verbose_name="rut")
    
    center = models.ManyToManyField(Center, through='CustomerCenter' , blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "cliente"

class CustomerCenter(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    center = models.ForeignKey(Center, on_delete=models.CASCADE)

class Laboratory(models.Model):
    """
    Entrance Laboratory for Entryform.
    """

    name = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="nombre"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Laboratorio de Ingreso"


class EntryForm_Type(models.Model):
    """
    Stores information a about a entry type, this defines the subsequent
    flow the process will take, as different types require different
    processes.
    """

    name = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "tipo de Ingreso"
        verbose_name_plural = "tipos de Ingreso"

@cleanup.select
class CaseFile(models.Model):
    """Stores information about file uploads related to Cases"""

    file = models.FileField(upload_to="vehice_case_files")
    loaded_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


ENTRY_FORMAT_OPTIONS = [
    (1, "Tubo"),
    (2, "Cassette"),
    (3, "Bloque"),
    (4, "Slide s/teñir"),
    (5, "Slide teñido"),
    (6, "Vivo"),
    (7, "Muerto"),
]


class EntryForm(models.Model):
    """
    Stores information about a new Case, this is detailed data for the services
    to be done.
    """

    specie = models.ForeignKey(Specie, null=True, on_delete=models.SET_NULL)
    watersource = models.ForeignKey(
        WaterSource,
        null=True,
        on_delete=models.SET_NULL,
    )
    larvalstage = models.ForeignKey(
        LarvalStage,
        null=True,
        on_delete=models.SET_NULL,
    )
    fixative = models.ForeignKey(
        Fixative,
        null=True,
        on_delete=models.SET_NULL,
    )
    laboratory = models.ForeignKey(
        Laboratory,
        null=True,
        on_delete=models.SET_NULL,
    )
    customer = models.ForeignKey(Customer, null=True, on_delete=models.SET_NULL, related_name='customer')
    company_index = models.ForeignKey(Customer, null=True, on_delete=models.SET_NULL, related_name='company_index')
    
    company = models.CharField(max_length=250, null=True, blank=True)
    center = models.CharField(max_length=250, null=True, blank=True)

    company_center = models.ForeignKey(CustomerCenter, null=True, on_delete=models.SET_NULL)
    company_laboratory = models.CharField(max_length=250, null=True, blank=True)
    
    observation = models.TextField(null=True, blank=True)
    no_order = models.CharField(max_length=250, null=True, blank=True)
    no_caso = models.CharField(max_length=250, null=True, blank=True)

    created_at = models.DateTimeField(null=True, blank=True)
    sampled_at = models.DateTimeField(null=True, blank=True)
    sampled_at_hour = models.CharField(max_length=5, null=True, blank=True)
    sampled_at_am_pm = models.CharField(max_length=2, null=True, blank=True)
    forms = GenericRelation(Form)
    flag_subflow = models.BooleanField(default=False)
    responsible = models.CharField(max_length=250, null=True, blank=True)
    no_request = models.CharField(max_length=250, null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    anamnesis = models.TextField(null=True, blank=True)
    entryform_type = models.ForeignKey(
        EntryForm_Type,
        null=True,
        on_delete=models.SET_NULL,
    )
    attached_files = models.ManyToManyField(CaseFile, through='EntryformAttachedFiles' , blank=True)
    transfer_order = models.CharField(max_length=250, null=True, blank=True)
    entry_format = models.IntegerField(choices=ENTRY_FORMAT_OPTIONS, default=1)

    def __str__(self):
        return f"#{self.pk} - {self.no_caso}"

    @property
    def form(self):
        return self.forms.get()

    @property
    def delay(self):
        """Returns an integer despicting the ongoing days counts"""
        days = 0
        try:
            days = busday_count(
                self.created_at.date(), datetime.now().date(), weekmask="1111110"
            )
        except AttributeError:
            days = 0
        return days

    @property
    def get_subflow(self):
        # Este algoritmo no tiene sentido, no pueden existir mas de un EntryForm para un mismo Caso.
        # subflows = EntryForm.objects.filter(
        #     no_caso=self.no_caso, forms__cancelled=0
        # ).order_by("id")
        # if subflows.count() > 1:            
        #     for i in range(len(subflows)):
        #         if subflows[i].pk == self.pk:
        #             return str(i + 1)
        # else:
        return "N/A"


class Identification(models.Model):
    """
    Details information about a group of :model:`backend.Sample` that share the same origin.
    """

    entryform = models.ForeignKey(EntryForm, null=True, on_delete=models.SET_NULL)
    correlative = models.IntegerField(default=1, null=True, blank=True)
    cage = models.CharField(max_length=250, default="", null=True, blank=True)
    quantity = models.IntegerField(default="0", null=True, blank=True)
    client_case_number = models.CharField(
        max_length=250, default="", null=True, blank=True
    )
    weight = models.FloatField(default="0", null=True, blank=True)
    extra_features_detail = models.TextField(default="", null=True, blank=True)
    is_optimum = models.BooleanField(null=True)
    observation = models.TextField(default="", null=True, blank=True)
    group = models.CharField(default="", max_length=250, null=True, blank=True)
    removable = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    samples_are_correlative = models.BooleanField(default=False)

    # deprecated attr
    temp_id = models.CharField(default="", max_length=250, null=True, blank=True)
    no_fish = models.IntegerField(default="0", null=True, blank=True)
    no_container = models.IntegerField(default="0", null=True, blank=True)
    organs = models.ManyToManyField(Organ)
    organs_before_validations = models.ManyToManyField(
        Organ, related_name="organs_before_validations"
    )

    def natural_key(self):
        return (self.cage)

    def __str__(self):
        return f"{self.cage} {self.group} {self.extra_features_detail}"


class Unit(models.Model):
    correlative = models.IntegerField(default=1, null=True, blank=True)
    organs = models.ManyToManyField("Organ", through="OrganUnit")
    identification = models.ForeignKey(
        Identification, null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return str(self.correlative)


class OrganUnit(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    organ = models.ForeignKey(Organ, on_delete=models.CASCADE)

    def __str__(self):
        try:
            return f"{self.unit.identification.entryform.no_caso}-{self.unit.identification}-{self.unit.correlative}: {self.organ.abbreviation}"
        except AttributeError:
            return f"Unidad: {self.unit.id}; Organo: {self.organ.id}"


class ServiceComment(models.Model):
    """
    Stores comments done by a User related to a specific service in a :model:`backend.AnalysisForm`
    """

    text = models.TextField(blank=True, null=True)
    done_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

@cleanup.select
class ExternalReport(models.Model):
    """
    Stores files uploaded by a User related to a specific service in a :model:`backend.AnalysisForm`

    Files uploaded are stored in the MEDIA_ROOT/vehice_external_reports folder
    """

    file = models.FileField(upload_to="vehice_external_reports")
    loaded_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


# Service
class AnalysisForm(models.Model):
    """
    An Analysis is the process in which a Pathologists User can store Findings related to a specific service,
    it details the time it took to complete, and serves as a pivot to other models.
    """

    entryform = models.ForeignKey(EntryForm, null=True, on_delete=models.SET_NULL)
    exam = models.ForeignKey(Exam, null=True, on_delete=models.SET_NULL)
    forms = GenericRelation(Form)
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    patologo = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, blank=True)
    service_comments = models.ManyToManyField(ServiceComment, blank=True)
    external_reports = models.ManyToManyField(ExternalReport, blank=True)
    assignment_done_at = models.DateTimeField(default=None, blank=True, null=True)
    assignment_deadline = models.DateTimeField(default=None, blank=True, null=True)
    assignment_comment = models.TextField(default="", blank=True, null=True)
    manual_closing_date = models.DateTimeField(default=None, blank=True, null=True)
    manual_cancelled_date = models.DateTimeField(default=None, blank=True, null=True)
    manual_cancelled_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="cancelled_by",
        blank=True,
    )
    manual_reopened_date = models.DateTimeField(default=None, blank=True, null=True)
    manual_reopened_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="reopened_by", blank=True)
    pre_report_started = models.BooleanField(default=False)
    pre_report_started_at = models.DateTimeField(default=None, blank=True, null=True)
    pre_report_ended = models.BooleanField(default=False)
    pre_report_ended_at = models.DateTimeField(default=None, blank=True, null=True)
    report_code = models.CharField(max_length=250, null=True, blank=True)
    researches = models.ManyToManyField(Research, blank=True)
    score_diagnostic = models.FloatField(default=None, null=True, blank=True)
    score_report = models.FloatField(default=None, null=True, blank=True)
    stain = models.ForeignKey(
        Stain, null=True, on_delete=models.SET_NULL, verbose_name="tinción", blank=True
    )

    samples = models.ManyToManyField(OrganUnit, related_name="analysis")

    unit_value = models.FloatField(verbose_name="valor unitario", null=True, blank=True)
    currency = models.CharField(verbose_name="moneda", max_length=6, default="UF")
    exchange_rate = models.FloatField(verbose_name="tipo de cambio", null=True, blank=True)

    on_hold = models.DateTimeField(null=True)
    on_standby = models.DateTimeField(null=True)

    process_status = models.CharField(max_length=120, null=True, blank=True)
    invoice_status = models.CharField(max_length=120, null=True, blank=True, default="NO EMITIDO")

    samples_charged = models.CharField(max_length=3, null=True, blank=True)


    def __str__(self):
        exam = self.exam.name if self.exam else "N/A"
        return f"{self.entryform.no_caso} - {exam}"

    @property
    def status(self):
        form = list(self.forms.all())[0]
        is_form_closed = form.form_closed
        is_form_cancelled = form.cancelled
        in_progress = self.exam and self.exam.pathologists_assignment and self.pre_report_started
        
        if is_form_closed:
            status = "Finalizado"
        elif is_form_cancelled: status = "Anulado"
        elif in_progress and not self.pre_report_ended:
            if self.on_hold:
                status = "En Espera"
            elif self.on_standby:
                status = "Pausado"
            else:
                status = "Lectura Iniciada"
        elif in_progress and self.pre_report_ended:
            if self.on_hold:
                status = "En Espera"
            elif self.on_standby:
                status = "Pausado"
            else:
                status = "Pre-Informe Terminado"
        else:
            if self.on_hold:
                status = "En Espera"
            elif self.on_standby:
                status = "Pausado"
            else:
                status = "En Curso"
        if self.process_status != status:
            self.process_status = status
            self.save()
        return status

    def get_invoice_status(self):
        has_preinvoices = self.preinvoice_set.count() > 0
        has_invoices = self.preinvoice_set.filter(analysispreinvoice__isnull=False).count() > 0

        STATUS = ["NO EMITIDO", "PREFACTURA", "EMITIDO"]

        if self.invoice_status in STATUS:
            status = "NO EMITIDO"
            if has_preinvoices:
                status = "PREFACTURA"
            elif has_invoices:
                status = "EMITIDO"

            if status != self.invoice_status:
                self.invoice_status = status
                self.save()

        return self.invoice_status

    def get_samples_amount(self):
        samples_count = self.samples.count()

        if samples_count > 0:
            return samples_count

        entryform = self.entryform
        samples = Sample.objects.filter(entryform=entryform)
        sample_exams = SampleExams.objects.filter(sample__in=samples, stain=self.stain, exam=self.exam)

        return sample_exams.count()

class Sample(models.Model):
    """
    A Sample also known as Individual, is the lowest level subject of study in a Case, (Tube, Fish, Cassette, ...),
    to this Unit is the lab process applied to and it's its Slide what Pathologist users study.
    """

    entryform = models.ForeignKey(EntryForm, null=True, on_delete=models.SET_NULL)
    index = models.IntegerField(null=True, blank=True)  # correlative
    identification = models.ForeignKey(
        Identification, null=True, on_delete=models.CASCADE
    )
    unit_organs = models.ManyToManyField(OrganUnit)

    def natural_key(self):
        return (self.id, self.index)

    def __str__(self):
        return f"{self.entryform.no_caso}-{self.identification}({self.index})"


class SampleExams(models.Model):
    """
    Pivot model to bind Samples :model:`backend.Sample` to the services applied to them :model:`backend.Exam`
    and the :model:`backend.Organ` that will be studied using a specific :model:`backend.Stain`
    """

    sample = models.ForeignKey(Sample, null=True, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, null=True, on_delete=models.CASCADE)
    organ = models.ForeignKey(Organ, null=True, on_delete=models.CASCADE)
    stain = models.ForeignKey(
        Stain, null=True, on_delete=models.SET_NULL, verbose_name="tinción"
    )
    unit_organ = models.ForeignKey(
        OrganUnit, null=True, on_delete=models.CASCADE, blank=True
    )

    def natural_key(self):
        return (self.organ.name, self.sample.index)

    def __str__(self):
        return str(self.sample)


class Responsible(models.Model):
    """
    Stores detailed information about a the individual responsible
    in a :model:`backend.Customer` side to keep track of a :model:`backend.Entryform`
    """

    name = models.CharField(max_length=250, null=True, blank=True)
    email = models.CharField(max_length=250, null=True, blank=True)
    phone = models.CharField(max_length=250, null=True, blank=True)
    job = models.CharField(max_length=250, null=True, blank=True)
    customer = models.ForeignKey(Customer, null=True, on_delete=models.SET_NULL)
    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = "responsable"
        verbose_name_plural = "responsables"


class EmailCcTo(models.Model):
    """
    Stores information a email address to send a copy :model:`backend.EmailTemplate`.
    """

    email = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="correo Electrónico"
    )

    def __str__(self):
        return str(self.email)

    class Meta:
        verbose_name = "destinatario copiado en Plantilla Email"
        verbose_name_plural = "destinatarios copiados en Plantilla Email"


class EmailTemplate(models.Model):
    """Stores information about reusable email template."""

    LANGUAGES = (
        ('en', 'English'),
        ('es', 'Spanish')
    )

    name = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Nombre"
    )
    body = models.TextField(
        max_length=1000, null=True, blank=True, verbose_name="Mensaje"
    )
    cc = models.ManyToManyField(EmailCcTo, verbose_name="Copia para", blank=True)
    language = models.CharField(max_length=4, verbose_name="idioma", choices=LANGUAGES, default='es')
    subject = models.CharField(max_length=70, verbose_name="sujeto", null=True, blank=True)

    class Meta:
        verbose_name = "Plantilla Email"
        verbose_name_plural = "Plantillas Emails"

    class Meta:
        verbose_name = "email Adjunto"
        verbose_name_plural = "email Adjuntos"


class CaseVersion(models.Model):
    """
    Stores information about a Case study is current version, as changes are generated over time revisions can be added.
    """

    entryform = models.ForeignKey(EntryForm, null=True, on_delete=models.SET_NULL)
    version = models.IntegerField(null=True, blank=True)
    generated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    generated_at = models.DateTimeField(auto_now_add=True)


RESUME_DOCUMENT_LANG = (
    (1, "es"),
    (2, "en"),
)

@cleanup.select
class DocumentCaseResume(models.Model):
    """
    Details information about a file upload to attach to a :model:`backend.EntryForm`
    """

    entryform = models.ForeignKey(EntryForm, null=True, on_delete=models.SET_NULL)
    filename = models.CharField(max_length=250, null=True, blank=True)
    file = models.FileField(upload_to="pdfs", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    lang = models.IntegerField(choices=RESUME_DOCUMENT_LANG, default=1)
    case_version = models.ForeignKey(CaseVersion, null=True, on_delete=models.SET_NULL)
    version = models.IntegerField(null=True, blank=True)
    generated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.filename


class DocumentResumeActionLog(models.Model):
    """
    Logs information about actions performed on a :model:`backend.DocumentCaseResume`
    """

    document = models.ForeignKey(
        DocumentCaseResume, null=True, on_delete=models.SET_NULL
    )
    mail_action = models.BooleanField(default=False)
    download_action = models.BooleanField(default=False)
    action_date = models.DateTimeField(auto_now_add=True)
    done_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

class Preinvoice(models.Model):
    """A prototype invoice delivered to a customer prior to being paid."""
    number = models.CharField(verbose_name="folio", max_length=24)
    customer = models.ForeignKey(Customer, models.CASCADE, related_name="preinvoices", verbose_name="cliente")
    date = models.DateField(verbose_name="fecha")
    amount = models.FloatField(verbose_name="monto", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)

    analysis = models.ManyToManyField(to=AnalysisForm, through="AnalysisPreinvoice")
    pay_person = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return self.number

class AnalysisPreinvoice(models.Model):
    analysis = models.ForeignKey(AnalysisForm, models.CASCADE)
    preinvoice = models.ForeignKey(Preinvoice, models.CASCADE)
    samples_studied = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{self.analysis} #{self.preinvoice}"


class Currency(models.Model):
    name = models.CharField(max_length=5)

    def __str__(self):
        return self.name


class TypeDeadline(models.Model):
    name = models.CharField(max_length=250, null=True, blank=True, verbose_name="name")

    def __str__(self):
        return self.name

class AnalysisTimes(models.Model):
     analysis = models.ForeignKey(AnalysisForm, null=True, on_delete=models.SET_NULL, verbose_name="analysis")
     exam = models.ForeignKey(Exam, null=True, on_delete=models.SET_NULL, verbose_name="exam")
     deadline = models.DateField(default=None, blank=True, null=True)
     changeDeadline = models.BooleanField(default=False)
     type_deadline = models.ForeignKey(TypeDeadline, null=True, on_delete=models.SET_NULL)
     created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, blank=True)
     service_comments = models.ForeignKey(ServiceComment, on_delete=models.SET_NULL, blank=True, null=True)

     def __str__(self):
        return f"{self.exam} {self.deadline}({self.type_deadline})"

class TypeResult(models.Model):
    name = models.CharField(max_length=250, null=True, blank=True, verbose_name="name")

class Result(models.Model):
    name = models.CharField(max_length=250, null=True, blank=True, verbose_name="name")
    type_result = models.ForeignKey(TypeResult, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="type_result")
    organ = models.ManyToManyField(to=Organ, through="ResultOrgan")

    def natural_key(self):
        return (self.id, self.name)

    def __str__(self):
        return self.name

class ResultOrgan(models.Model):
    organ = models.ForeignKey(Organ, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="organ")
    result = models.ForeignKey(Result, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="result")

    def natural_key(self):
        return (self.id, self.result.name, self.organ.name)

class SampleExamResult(models.Model):
    sample_exam = models.ForeignKey(SampleExams, null=True, blank=True, on_delete=models.SET_NULL)
    result_organ = models.ForeignKey(ResultOrgan, null=True, on_delete=models.SET_NULL)
    value = models.IntegerField(null=True, blank=True)
    distribution = models.CharField(max_length=250, null=True, blank=True, verbose_name="distribution")
    analysis = models.ManyToManyField(to=AnalysisForm, through="AnalysisSampleExmanResult")

class AnalysisSampleExmanResult(models.Model):
    analysis = models.ForeignKey(AnalysisForm, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="analysis")
    sample_exam_result = models.ForeignKey(SampleExamResult, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'({self.id}) {self.sample_exam_result.result_organ.result.name} - {self.sample_exam_result.result_organ.organ.name}'

class AnalysisOptionalResult(models.Model):
    analysis = models.ForeignKey(AnalysisForm, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="analysis")
    result = models.ForeignKey(Result, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="result")
    resultOrgan = models.ForeignKey(ResultOrgan, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="result")

class Methodology(models.Model):
    name = models.CharField(max_length=250, null=True, blank=True, verbose_name="name")
    description = models.TextField(null=True, blank=True)
    exam = models.ForeignKey(Exam, null=True, on_delete=models.SET_NULL, verbose_name="exam")

@cleanup.select
class MethodologyImage(models.Model):
    methodology = models.ForeignKey(Methodology, null=True, blank=True, on_delete=models.CASCADE)
    imagen = models.ImageField(null=True, blank=True,upload_to="MethodologyImage")
    index = models.IntegerField(null=True, blank=True)
    size = models.CharField(max_length=25 ,null=True, blank=True)
    comment = models.CharField(max_length=500, null=True, blank=True)

class AnalysisReport(models.Model):
    analysis = models.ForeignKey(AnalysisForm, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="analysis")
    report_date = models.DateField(null=True, blank=True)
    anamnesis = models.CharField(max_length=2000, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    correlative = models.IntegerField(null=True, blank=True)
    etiological_diagnostic = models.CharField(max_length=2000, null=True, blank=True)
    methodology = models.ForeignKey(Methodology, null=True, blank=True, on_delete=models.SET_NULL)

@cleanup.select
class ReportImages(models.Model):
    analysis_report = models.ForeignKey(AnalysisReport, null=True, blank=True, on_delete=models.SET_NULL)
    imagen = models.ImageField(null=True, blank=True,upload_to="AnalysisReport")
    index = models.IntegerField(null=True, blank=True)
    size = models.CharField(max_length=25 ,null=True, blank=True)
    comment = models.CharField(max_length=500, null=True, blank=True)

class Quote(models.Model):
    created_at = models.DateField(auto_now_add=True)
    responsible = models.ForeignKey(Responsible, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    comment = models.TextField(null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Quote {self.id} by {self.created_by.get_full_name if self.created_by else 'Unknown User'}"
    
class QuoteExam(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=3)
    quantity = models.IntegerField()
    isRecommended = models.BooleanField(default= False)

    def __str__(self):
       return f"Quote #{self.quote.id} - Exam {self.exam.name}"

class PreListed(models.Model):
    name = models.CharField(max_length=30, unique=True)
    
    def __str__(self):
        return f"PreListed: {self.name}"

class PreListedGroup(models.Model):
    preListed = models.ForeignKey(PreListed, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)

class EntryformAttachedFiles(models.Model):
    entryform = models.ForeignKey(EntryForm, on_delete=models.CASCADE)
    caseFile = models.ForeignKey(CaseFile, on_delete=models.CASCADE)

    class Meta:
        db_table = 'backend_entryform_attached_files'
    
class Outsource(models.Model):
    created_at = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    analysis = models.ForeignKey(AnalysisForm, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    comment = models.ForeignKey(ServiceComment, on_delete=models.CASCADE)
    
class OutsourceAttachedFiles(models.Model):
    outsource = models.ForeignKey(Outsource, on_delete=models.CASCADE)
    attachedFiles = models.ForeignKey(EntryformAttachedFiles, on_delete=models.CASCADE)

class WeightGeneralScore(models.Model):
    resultOrgan = models.ForeignKey(ResultOrgan, on_delete=models.CASCADE)
    watersource = models.ForeignKey(WaterSource, on_delete=models.CASCADE)
    intensity = models.IntegerField()
    weight = models.IntegerField()
    