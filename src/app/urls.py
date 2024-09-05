from django.conf.urls import re_path
from django.views.decorators.csrf import csrf_exempt

from app import views

urlpatterns = [    
    # Templates views
    re_path(r"^$", views.home, name="home"),
    re_path(r"^ingresos$", views.show_ingresos, name="ingresos"),
    re_path(r"^ingresos/tabla$", views.tabla_ingresos, name="tabla_ingresos"),
    re_path(r"^ingresos/new$", views.new_ingreso, name="ingresos_new"),
    re_path(r"^estudios$", views.show_estudios, name="estudios"),
    re_path(r"^research/new$", csrf_exempt(views.new_research), name="research_new"),
    re_path(r"^derivacion/(?P<all>\d+)$", views.show_patologos, name="patologos"),
    re_path(r"^quotes$", views.quotes, name="quotes"),
    re_path(r"^quotes/add", views.add_quote, name="quote_new"),
    re_path(r"^quotes/edit/(?P<id>\d+)$", views.edit_quote, name="quote_edit"),
    re_path(r"^quotes/download-quote/(?P<id>\d+)$", views.download_quote, name="download_quote"),
    
    
    
    
    # PDFs
    re_path(r"^template-reception/(?P<id>\d+)/(?P<userId>\d+)$",views.template_reception,name="template_reception",),
    re_path(r"^download-reception/(?P<id>\d+)$",views.download_reception,name="download_reception",),
    re_path(r"^download-preinvoice/(?P<id>\d+)$",views.download_preinvoice,name="download_preinvoice",),
    re_path(r"^template-preinvoice/(?P<id>\d+)$",views.template_preinvoice,name="template_preinvoice",),
    re_path(r"^template-resumen-report/(?P<id>\d+)/(?P<userId>\d+)$",views.template_resumen_report,name="template_resumen_report",),    
    re_path(r"^download-resumen-report/(?P<id>\d+)$",views.download_resumen_report,name="download_report",),
        # Is not working well
    re_path(r"^template-report/(?P<id>\d+)$", views.template_report, name="template_report"),
        # Is not working well
    re_path(r"^download-report/(?P<id>\d+)$", views.download_report, name="download_report"),
    

    # Jsons
    re_path(r"^control/tabla$", views.tabla_patologos, name="tabla_patologos"),
    re_path(r"^logactions/(?P<id>\d+)$", views.show_log_actions, name="logactions"),
    re_path(r"^change_language$", views.ChangeLanguage.as_view(), name="change_language"),
    
    
    # Not used templates views
    # re_path(r"^clientes$", views.show_clientes, name="clientes"),
    # re_path(r"^users$", views.show_users, name="users"),
    # re_path(r"^analisis$", views.show_analisis, name="analisis"),
]