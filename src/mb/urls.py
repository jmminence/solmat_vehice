from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from mb import views

urlpatterns = [
    path("pool/list-organs/<int:id>", csrf_exempt(views.list_organs), name="pool_list_organs"),
    path("pool", views.Pools.as_view(), name="createPool"),
    path("pool/<int:id>", views.Pools.as_view(), name="Pools"),
    path("getPool/<int:id>", views.Pools.as_view(), name="pool_id"),
    path("pool/<int:id>", views.Pools.as_view(), name="edit_pool"),
    path("deletePool/<int:id>", csrf_exempt(views.deletePool), name="deletePool"),
    path("casePools/<int:id>", csrf_exempt(views.casePools), name="casePools"),
    path("addPoolExams/<int:id>", csrf_exempt(views.addPoolExams), name="addPoolExams"),
    path("deleteExamPool/", csrf_exempt(views.deleteExamPool), name="deleteExamPool"),
    path("deleteExamPools/", csrf_exempt(views.deleteExamPools), name="deleteExamPools"),
]