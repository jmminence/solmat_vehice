import json

from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Group, Permission, User
from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers

from accounts.models import UserProfile
from backend.models import *
from lab.models import Cassette
from mb.models import Pool
from vehice import settings


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class PermissionSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = Permission
        fields = ["codename", "name", "natural_key"]


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["is_pathologist", "is_reviewer", "phone", "profile", "role"]


class UserSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    permissions = PermissionSerializer(many=True, read_only=True)
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "groups",
            "permissions",
            "profile",
        ]


class CaseFileSerializer(serializers.ModelSerializer):
    filename = serializers.SerializerMethodField()

    class Meta:
        model = CaseFile
        fields = ["id", "file", "loaded_by", "created_at", "filename"]

    def get_filename(self, obj):
        return obj.file.name


class LaboratorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratory
        fields = ["id", "name"]


class EntryFormTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntryForm_Type
        fields = ["id", "name"]


class OrganSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organ
        fields = ["id", "name", "abbreviation", "organ_type"]


class StainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stain
        fields = ["id", "name", "abbreviation", "description"]


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"


class ExamSerializer(serializers.ModelSerializer):
    pricing_unit = serializers.CharField(source="get_pricing_unit_display")

    class Meta:
        model = Exam
        fields = [
            "id",
            "name",
            "stain",
            "pathologists_assignment",
            "pricing_unit",
            "service",
            "description",
            "unit_price",
            "chargeable",
            "group",
        ]


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "company", "type_customer", "rut", "inter_lab"]


class CenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Center
        fields = ["id", "name", "company_name", "created_at", "updated_at"]


class FixativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fixative
        fields = ["id", "name"]


class WaterSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterSource
        fields = ["id", "name"]


class SpecieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specie
        fields = ["id", "name"]


class LarvalStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LarvalStage
        fields = ["id", "name"]


class CustomerCenterSerializer(serializers.ModelSerializer):
    class Meta: 
        model = CustomerCenter
        fields = ['id', 'customer']
    
    def to_representation(self, instance):
        return {
            'id': instance.id,
            'center': CenterSerializer(instance.center).data
        }

class EntryformSerializer(serializers.ModelSerializer):
    anamnesis = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    attached_files = CaseFileSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField()
    created_by = serializers.SlugRelatedField(slug_field="first_name", read_only=True)
    
    customer = CustomerSerializer(allow_null=True, required=False)
    company_index = CustomerSerializer(allow_null=True, required=False)
    company_center = CustomerCenterSerializer(allow_null=True, required=False)
    company_laboratory = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    
    company = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    center = serializers.CharField(allow_blank=True, required=False)
    
    
    entry_format = serializers.ChoiceField(choices=ENTRY_FORMAT_OPTIONS, default=1)
    entryform_type = EntryFormTypeSerializer(allow_null=True, required=False)
    fixative = FixativeSerializer(allow_null=True, required=False)
    laboratory = LaboratorySerializer(allow_null=True, required=False)
    larvalstage = LarvalStageSerializer(allow_null=True, required=False)
    no_caso = serializers.CharField(allow_blank=True, required=False)
    no_order = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    no_request = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    observation = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    sampled_at = serializers.DateTimeField(allow_null=True, required=False)
    specie = SpecieSerializer(allow_null=True, required=False)
    transfer_order = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    responsible = serializers.CharField(allow_null=True, allow_blank=True)
    watersource = WaterSourceSerializer(allow_null=True, required=False)
    reception_file = serializers.SerializerMethodField()
    resumen_file = serializers.SerializerMethodField()
    
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        center_txt = ''
        if instance.company_center is not None:
            center_txt = instance.company_center.center.name
        elif instance.company_laboratory is not None:
            center_txt = instance.company_laboratory
        else:
            center_txt = ''
            
        representation['center'] = center_txt

        return representation
    def get_reception_file(self, entryform):
        return reverse("download_reception", args=[entryform.id])

    def get_resumen_file(self, entryform):
        return reverse("download_report", args=[entryform.form.id])

    def create(self, validated_data):
        entryforms_count = EntryForm.objects.count()
        no_caso = settings.CASE_NUMBER_START_INDEX + entryforms_count + 1
        validated_data["no_caso"] = f"V{no_caso}"

        if "customer" in validated_data and validated_data["customer"]:
            customer_data = validated_data.pop("customer")
            customer = Customer.objects.get(**customer_data)
            validated_data["customer_id"] = customer.id

        entryform = EntryForm.objects.create(**validated_data)
        form = Form.objects.create(
            content_object=entryform, flow_id=1, state_id=4, reception_finished=1, reception_finished_at=timezone.now()
        )

        return entryform

    def update(self, instance, validated_data):
        instance.anamnesis = validated_data.get("anamnesis", instance.anamnesis)
        instance.center = validated_data.get("center", instance.center)
        instance.company = validated_data.get("company", instance.company)
        instance.created_at = validated_data.get("created_at", instance.created_at)
        instance.entry_format = validated_data.get(
            "entry_format", instance.entry_format
        )
        instance.no_order = validated_data.get("no_order", instance.no_order)
        instance.no_request = validated_data.get("no_request", instance.no_request)
        instance.observation = validated_data.get("observation", instance.observation)
        instance.sampled_at = validated_data.get("sampled_at", instance.sampled_at)
        instance.transfer_order = validated_data.get(
            "transfer_order", instance.transfer_order
        )
        instance.responsible = validated_data.get("responsible", instance.responsible)
        instance.sampled_at = validated_data.get("sampled_at", instance.sampled_at)

        if "customer" in validated_data and validated_data["customer"]:
            customer_data = validated_data.pop("customer")
            customer = Customer.objects.get(**customer_data)
            instance.customer = customer

        if "entryform_type" in validated_data and validated_data["entryform_type"]:
            entryform_type_data = validated_data.pop("entryform_type")
            entryform_type = EntryForm_Type.objects.get(**entryform_type_data)
            instance.entryform_type = entryform_type

        if "fixative" in validated_data and validated_data["fixative"]:
            fixative_data = validated_data.pop("fixative")
            fixative = Fixative.objects.get(**fixative_data)
            instance.fixative = fixative

        if "laboratory" in validated_data and validated_data["laboratory"]:
            laboratory_data = validated_data.pop("laboratory")
            laboratory = Laboratory.objects.get(**laboratory_data)
            instance.laboratory = laboratory

        if "larvalstage" in validated_data and validated_data["larvalstage"]:
            larvalstage_data = validated_data.pop("larvalstage")
            larvalstage = LarvalStage.objects.get(**larvalstage_data)
            instance.larvalstage = larvalstage

        if "specie" in validated_data and validated_data["specie"]:
            specie_data = validated_data.pop("specie")
            specie = Specie.objects.get(**specie_data)
            instance.specie = specie

        if "watersource" in validated_data and validated_data["watersource"]:
            watersource_data = validated_data.pop("watersource")
            watersource = WaterSource.objects.get(**watersource_data)
            instance.watersource = watersource

        instance.save()

        return instance


    class Meta:
        model = EntryForm
        exclude = ["sampled_at_am_pm", "sampled_at_hour", "flag_subflow"]

class ResponsibleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Responsible
        fields = ["id", "name", "email", "phone", "job", "active"]


class EmailTemplateSerializer(serializers.ModelSerializer):
    cc = serializers.SlugRelatedField(many=True, read_only=True, slug_field="email")

    class Meta:
        model = EmailTemplate
        fields = ["id", "name", "body", "cc"]


class AnalysisFormSerializer(serializers.ModelSerializer):
    entryform = EntryformSerializer(read_only=True)
    exam = ExamSerializer(read_only=True)
    patologo = UserSerializer(read_only=True)
    stain = StainSerializer(read_only=True)

    samples_amount = serializers.SerializerMethodField()
    studies = serializers.SerializerMethodField()

    invoice_status = serializers.SerializerMethodField()
    process_status = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisForm
        fields = "__all__"

    def get_invoice_status(self, obj):
        return obj.get_invoice_status()

    def get_process_status(self, obj):
        return obj.status

    def get_samples_amount(self, obj):
        samples_count = obj.get_samples_amount()
        samples_count += Pool.objects.filter(identification__entryform=obj.entryform, exams=obj.exam).count()

        return samples_count

    def get_studies(self, obj):
        studies = obj.research_set.all().values_list("code", flat=True)
        return " / ".join(studies)


class PreinvoiceSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    preinvoice_file = serializers.SerializerMethodField()
    

    def get_preinvoice_file(self, preinvoice):
        return reverse("download_preinvoice", args=[preinvoice.id])
        
    class Meta:
        model = Preinvoice
        fields = "__all__"


class AnalysisPreinvoiceSerializer(serializers.ModelSerializer):
    preinvoice = PreinvoiceSerializer(read_only=True, many=False)
    analysis = AnalysisFormSerializer(read_only=True, many=False)
    samples_studied = serializers.IntegerField()

    class Meta:
        model = AnalysisPreinvoice
        fields = ["preinvoice", "analysis", "samples_studied", "id"]


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ["name"]


class AnalysisFormPreinvoiceSerializer(AnalysisFormSerializer):
    preinvoices = serializers.SerializerMethodField()
    # invoices = serializers.SerializerMethodField()
    # exchange_rate = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisForm
        fields = "__all__"

    def get_preinvoices(self, obj):
        preinvoices = AnalysisPreinvoice.objects.filter(analysis=obj)
        serialized = AnalysisPreinvoiceSerializer(preinvoices, many=True)
        return serialized.data


class IdentificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Identification
        fields = "__all__"


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = "__all__"


class CassetteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cassette
        fields = "__all__"


class LogEntrySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    model_name = serializers.SerializerMethodField()

    class Meta:
        model = LogEntry
        fields = "__all__"

    def get_user(self, obj):
        user = obj.user
        return user.first_name + " " + user.last_name

    def get_model_name(self, obj):
        content_type = obj.content_type
        return content_type.model


class ResponsibleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Responsible
        fields = '__all__'

class QuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = '__all__'
    
    def to_representation(self, instance):
        return {
            'id': instance.id,
            'created_at': instance.created_at,
            'responsible': ResponsibleSerializer(instance.responsible).data,
            'customer': CustomerSerializer(instance.customer).data,
            'comment': instance.comment,
            'title': instance.title,
            'expiration_date': instance.expiration_date,
            'created_by_id': instance.created_by.id,
            'quoteExams': QuoteExamSerializer(QuoteExam.objects.filter(quote_id = instance.id), many=True).data
        }

class QuoteExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteExam
        fields = '__all__'


class PreListedSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreListed
        fields = '__all__'
    
    def to_representation(self, instance):
        return {
            'id': instance.id,
            'name': instance.name,
            'exams': [group.exam_id for group in instance.prelistedgroup_set.all()]
        }
        

class OutsourceAttachedFilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutsourceAttachedFiles
        fields = '__all__'
    
    def to_representation(self, instance):
        caseFile = EntryformAttachedFiles.objects.get(pk=instance.attachedFiles_id).caseFile;
        
        path = str(caseFile.file).replace('\\', '/')
        split_name = path.split('/')
        file_name = split_name[-1]
        
        return {
            'id': instance.id,
            'caseFile_id':caseFile.id,
            'name': file_name,
            'url': caseFile.file.url,
        }
class OutsourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outsource
        fields = '__all__'
    
    def to_representation(self, instance):
        return {
            'id': instance.id,
            'analysis_id': instance.analysis_id,
            'created_at': instance.created_at,
            'customer_id': instance.customer_id,
            'comment': ServiceComment.objects.get(pk=instance.comment_id).text,
            'created_by_id': instance.created_by.id,
            'files': OutsourceAttachedFilesSerializer(OutsourceAttachedFiles.objects.filter(outsource_id = instance.id), many=True).data
        }

