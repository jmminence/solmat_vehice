import json
from django.forms import model_to_dict
from django.http import JsonResponse, QueryDict
from django.views import View
from backend.models import AnalysisForm, Unit

from mb.models import *
from workflows.models import Flow, Form

def list_organs(request,id):

    identification = Identification.objects.get(id=id)
    units = Unit.objects.filter(identification=identification.id)

    context = {
        "identification": {
            "id": identification.id,
            "cage": identification.cage,
            "group": identification.group
        },
        "units":[]
    }
    
    for unit in units:

        context["units"].append({
            "unit_id": unit.id,
            "correlative": unit.correlative,
            "organs":[]
        })

        organs_unit = OrganUnit.objects.filter(unit=unit)
        # for organ_unit in organs_unit:
        #     context["units"][unit.id]["organs"][organ_unit.id] = {
        #         "organ": organ_unit.organ.name
        #     }

        for unit in context["units"]:
            for organ_unit in organs_unit:
                if unit["unit_id"] == organ_unit.unit.id:
                    unit["organs"].append({
                        "organ_unit_id":organ_unit.id,
                        "organ": organ_unit.organ.name
                    })
    
    context = json.dumps(context, ensure_ascii=False)

    return JsonResponse({"context":context})


class Pools(View):

    def get(self, request,id, *args, **kwargs):
        pool_id = request.GET.get("pool")

        if pool_id != None:

            pool = Pool.objects.get(id=pool_id)
            organ_units = pool.organ_unit.all()
            organ_units_list = []

            for organ_unit in organ_units:
                organ_units_list.append(organ_unit.id)

            return JsonResponse({"organ_units": organ_units_list,
                                 "pool": model_to_dict(pool, exclude=["organ_unit","exams"])
                                 })

        else:
            pools = Pool.objects.filter(identification_id = id)
            pools_list = []

            for pool in pools:
                pool_organunit_list=[]
                organunits = pool.organ_unit.all()
                for organunit in organunits:
                    pool_organunit = {
                        "organ": organunit.organ.name,
                        "correlativo": organunit.unit.correlative,
                        "organunit_id": organunit.id
                    }

                    pool_organunit_list.append(pool_organunit)

                data = {
                    "pool": model_to_dict(pool, fields=["id","name","identification"]),
                    "pool_organunit_list":pool_organunit_list
                }
                data["pool_organunit_list"] = sorted(data["pool_organunit_list"], key=lambda x: x["correlativo"])

                pools_list.append(data)

            return JsonResponse({"data": pools_list})
    
    def post(self, request, *args, **kwargs):
        pool_organunit_list = []

        identification_id = request.POST.get("identification_id")
        organs_selected = request.POST.getlist("organs_selected[]")
        poolName = request.POST.get("name")

        pool = Pool.objects.create(name=poolName, identification_id = identification_id)
        
        for organ_selected in organs_selected:
            pool_organunit = PoolOrganUnit.objects.create(pool=pool, organ_unit_id=int(organ_selected))
            pool_organunit = {
                "organ": pool_organunit.organ_unit.organ.name,
                "correlativo": pool_organunit.organ_unit.unit.correlative,
                "organunit_id": pool_organunit.organ_unit.id
            }

            pool_organunit_list.append(pool_organunit)


        context = {
            "pool": model_to_dict(pool, fields=["id","name","identification"]),
            "pool_organunit_list":pool_organunit_list
        }

        return JsonResponse({"context": context})
    
    def put(self, request, id, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)

        pool = Pool.objects.get(id=id)

        organs_selected = body_data["organs_selected"]

        organs_units = pool.organ_unit.all()

        organ_unit_removed = []
        for organ_unit in organs_units:
            if organ_unit.id not in organs_selected:
                organ_unit_removed.append(organ_unit.id)
                PoolOrganUnit.objects.get(pool=pool, organ_unit=organ_unit).delete()

        organ_unit_adds = []
        for organ in organs_selected:
            try:
                PoolOrganUnit.objects.get(pool=pool, organ_unit=organ)
            except:
                poolOrganUnit = PoolOrganUnit.objects.create(pool=pool, organ_unit_id=organ)
                poolOrganUnit = {
                "id": poolOrganUnit.organ_unit.id,
                "organ": poolOrganUnit.organ_unit.organ.name,
                "correlativo": poolOrganUnit.organ_unit.unit.correlative,
                }

                organ_unit_adds.append(poolOrganUnit)

        return JsonResponse({
            "organ_unit_removed":organ_unit_removed,
            "organ_unit_adds":organ_unit_adds
        })


def deletePool(request, id):
    pool = Pool.objects.get(id=id)
    id=pool.id
    pool.delete()

    return JsonResponse({"data": id})


def casePools(request, id):

    pools_list = []
    pools = Pool.objects.filter(identification__entryform__id=id)
    for pool in pools:
        organ_unit_list = []
        exams_list = []
        pool_dict = model_to_dict(pool)
        identification = Identification.objects.get(id=pool_dict["identification"])
        pool_dict["identification"] = {
            "id":identification.id,
            "cage":identification.cage,
            "group":identification.group,
            "extra_features_detail":identification.extra_features_detail,
        }
        for organ_unit in pool_dict["organ_unit"]:
            organ_unit_data = {
                "id": organ_unit.id,
                "organ": organ_unit.organ.name,
                "correlative": organ_unit.unit.correlative,
            }
            organ_unit_list.append(organ_unit_data)
        
        pool_dict["organ_unit"] = organ_unit_list
        pool_dict["organ_unit"] = sorted(pool_dict["organ_unit"], key=lambda x: x["correlative"])

        for exam in pool_dict["exams"]:
            analysis = AnalysisForm.objects.get(entryform__id=id, exam=exam)
            exam_data = {
                "id":exam.id,
                "name":exam.name,
                "status":analysis.process_status
            }
            exams_list.append(exam_data)
        
        pool_dict["exams"] = exams_list
        pool_dict["exams"] = sorted(pool_dict["exams"], key=lambda x: x["id"])

        pools_list.append(pool_dict)


    return JsonResponse({"pools": pools_list})


def addPoolExams(request,id):
    request = request.POST
    exam_pool = request["exam_pool"]
    pools = request.getlist("pools[]")
    pools_list = []

    try:
        analysis = AnalysisForm.objects.get(entryform_id=id, exam_id=exam_pool)
    except:
        analysis = AnalysisForm.objects.create(entryform_id=id, exam_id=exam_pool, stain_id=2, process_status="En Curso")

        flow = Flow.objects.get(pk=2)

        Form.objects.create(
                content_object=analysis,
                flow=flow,
                state=flow.step_set.all()[0].state,
                parent_id=analysis.entryform.forms.first().id,
            )
    
    for id in pools:
        pool = Pool.objects.get(id=id)
        pool.exams.add(exam_pool)
        pool.save()
        pools_list.append({
            "id":pool.id,
            "name":pool.name
        })
    
    exam = Exam.objects.get(id=exam_pool)
    exam_dict = {
        "id": exam.id,
        "name":exam.name,
        "status":analysis.process_status,
    }

    return JsonResponse({"pools": pools_list,
                         "exam":exam_dict})


def deleteExamPool(request):

    request = QueryDict(request.body)
    pool_id = request.get("pool")
    exam_id = request.get("exam")

    pool = Pool.objects.get(id=pool_id)
    pool.exams.remove(exam_id)
    pool.save()

    return JsonResponse({"ok": True})


def deleteExamPools(request):

    request = QueryDict(request.body)
    pools_id = request.getlist("pools[]")
    exam_id = request.get("exam_pool")
    
    for id in pools_id:
        pool = Pool.objects.get(id=id)
        pool.exams.remove(exam_id)
        pool.save()

    return JsonResponse({"ok": True})