from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from backend import views

urlpatterns = [
    # path("block-timing", csrf_exempt(views.save_block_timing), name="save_block_timing"),                               Deprecated
    # path("cassettes-entry-form/<int:entry_form>",csrf_exempt(views.CASSETTE.as_view()),name="cassette_entryform_id",),  Deprecated
    
    # path("fix-missing-units",csrf_exempt(views.fix_missing_units),name="fix_missing_units",),                        # No tiene Referencia
    # path("workform/<int:form_id>/complete",csrf_exempt(views.completeForm),name="complete_form",),                   # No tiene Referencia
    
    # path("analysis/<int:analysisform_id>",csrf_exempt(views.set_analysis_comments),name="set_analysis_comments",),   # Post (Json) DELETED
    # path("stain-timing", csrf_exempt(views.save_stain_timing), name="save_stain_timing"),                            # Json        DELETED
    # path("scan-timing", csrf_exempt(views.save_scan_timing), name="save_scan_timing"),                               # Json        DELETED
    # path("sendNotification",csrf_exempt(views.sendEmailNotification),name="sendNotification",),                      # Json        DELETED
    
    
    path("exam", csrf_exempt(views.EXAM.as_view()), name="exam"),                                                    # Post (Json)
    path("customer", csrf_exempt(views.CUSTOMER.as_view()), name="customer"),                                        # Post (Json)
    
    path("entryform", csrf_exempt(views.ENTRYFORM.as_view()), name="entryform"),                                     # Get (Json)
    path("entryform/<int:id>",csrf_exempt(views.ENTRYFORM.as_view()),name="entryform_id",),                          # Get (Json)
    path("workflow/<int:form_id>/<slug:step_tag>",csrf_exempt(views.WORKFLOW.as_view()),name="workflow_open_step",), # Get (Render), Post(JSON), Delete(Json)
    path("workflow", csrf_exempt(views.WORKFLOW.as_view()), name="workflow"),                                        # Get (Render), Post(JSON), Delete(Json)
    path("workflow/<int:form_id>",csrf_exempt(views.WORKFLOW.as_view()),name="workflow_w_id",),                      # Get (Render), Post(JSON), Delete(Json)
    path("responsible", csrf_exempt(views.RESPONSIBLE.as_view()), name="responsible"),                               # Get (Json), Post(JSON), Delete(Json)
    path("responsible/<int:id>",csrf_exempt(views.RESPONSIBLE.as_view()),name="responsible_detail",),                # Get (Json), Post(JSON), Delete(Json)
    path("emailTemplate",csrf_exempt(views.EMAILTEMPLATE.as_view()),name="emailTemplate",),                          # Get (Json), Post(JSON)
    path("emailTemplate/<int:id>",csrf_exempt(views.EMAILTEMPLATE.as_view()),name="emailTemplate_detail",),          # Get (Json), Post(JSON)
    path("analysis-entry-form/<int:entry_form>",csrf_exempt(views.ANALYSIS.as_view()),name="analysis_entryform_id",),# Get (Json), Put(Json)
    path("service_reports/<int:analysis_id>",csrf_exempt(views.SERVICE_REPORTS.as_view()),name="service_reports",),  # Get (Json), Post(JSON), Delete(Json)
    path("service_reports/<int:analysis_id>/<int:id>",csrf_exempt(views.SERVICE_REPORTS.as_view()),name="service_reports_id",), # Get (Json), Post(JSON), Delete(Json)
    path("service_comments/<int:analysis_id>",csrf_exempt(views.SERVICE_COMMENTS.as_view()),name="service_comments",), # Get (Json), Post(JSON), Delete(Json)
    path("service_comments/<int:analysis_id>/<int:id>",csrf_exempt(views.SERVICE_COMMENTS.as_view()),name="service_comments_id",), # Get (Json), Post(JSON), Delete(Json)
    path("service_researches/<int:analysis_id>",csrf_exempt(views.SERVICE_RESEARCHES.as_view()),name="service_researches",), # Get (Json), Post(JSON), Delete(Json)
    path("service_researches/<int:analysis_id>/<int:id>",csrf_exempt(views.SERVICE_RESEARCHES.as_view()),name="service_researches_id",), # Get (Json), Post(JSON), Delete(Json)
    path("case_files/<int:entryform_id>",csrf_exempt(views.CASE_FILES.as_view()),name="case_files",),                # Get (Json), Post(JSON), Delete(Json)
    path("case_files/<int:entryform_id>/<int:id>",csrf_exempt(views.CASE_FILES.as_view()),name="case_files_id",),    # Get (Json), Post(JSON), Delete(Json)
    
           
    path("generalData/<int:id>", csrf_exempt(views.save_generalData), name="generalData"),                           # Json
    path("workform/<int:form_id>/finish-reception",csrf_exempt(views.finishReception),name="finish_reception",),     # Json
    path("workform/<int:form_id>/save_step1",csrf_exempt(views.save_step1),name="save_step1",),                      # Json
    path("service_assigment/",csrf_exempt(views.service_assignment),name="service_assignment",),                     # Json
    path("dashboard_analysis",csrf_exempt(views.dashboard_analysis),name="dashboard_analysis",),                     # Json
    path("dashboard_reports",csrf_exempt(views.dashboard_reports),name="dashboard_reports",),                        # Json
    path("dashboard_lefts", csrf_exempt(views.dashboard_lefts), name="dashboard_lefts"),                             # Json


    path("close_service/<int:form_id>/<str:closing_date>",csrf_exempt(views.close_service),name="close_service",),   # Json
    path("cancel_service/<int:form_id>",csrf_exempt(views.cancel_service),name="cancel_service",),                   # Json
    path("reopen_form/<int:form_id>", csrf_exempt(views.reopen_form), name="reopen_form"),                           # Json
    path("delete-sample/<int:id>", csrf_exempt(views.delete_sample), name="delete-sample"),                          # Json
    path("list-identification/<int:entryform_id>",csrf_exempt(views.list_identification),name="list_identification",), # Json
    path("units/<int:identification_id>",csrf_exempt(views.list_units),name="list_units",),                          # Json
    path("unit/<int:identification_id>/<int:correlative>",csrf_exempt(views.create_unit),name="create_unit",),       # Json
    path("remove-unit/<int:id>", csrf_exempt(views.remove_unit), name="remove_unit"),                                # Json
    path("save-units", csrf_exempt(views.save_units), name="save_units"),                                            # Json 
    path("identification/<int:id>",csrf_exempt(views.save_identification),name="identification",),                   # Json
    path("new-identification/<int:entryform_id>/<int:correlative>",csrf_exempt(views.new_empty_identification),name="new_identification",), # Json
    path("save-new-identification/<int:id>",csrf_exempt(views.save_new_identification),name="save_new_identification",), # Json
    path("remove-identification/<int:id>",csrf_exempt(views.remove_identification),name="remove_identification",),   # Json
    path("end-pre-report/<int:analysis_id>/<str:end_date>",csrf_exempt(views.end_pre_report),name="end_pre_report",),# Json
    path("init-pre-report/<int:analysis_id>",csrf_exempt(views.init_pre_report),name="init_pre_report",),            # Json
    path("save-scores/<str:type>/<int:id>", csrf_exempt(views.save_scores), name="save_scores"),                     # Json
    path("get-scores/<str:type>/<int:id>", csrf_exempt(views.get_scores), name="get_scores"),                        # Json
    
    
    path("research/<int:id>", csrf_exempt(views.RESEARCH.as_view()), name="research"),                               # Get (Render), Post(Json), Delete(Json)
    path("get-research/<int:id>",csrf_exempt(views.get_research_metadata),name="get_research",),                     # Json
    path("force-step/<int:form>/<int:step>",csrf_exempt(views.force_form_to_step),name="force_form_to_step",),       # Json
    path("centers", csrf_exempt(views.centers_list), name="centers_list"),                                           # Json
    path("toggle-analysis-status/<int:pk>", views.toggle_analysis_status, name="toggle_analysis_status"),            # Json
    path("get_serviceDeadline/<int:id>", csrf_exempt(views.get_serviceDeadline), name="get_serviceDeadline"),        # Json
    path("save_serviceDeadline/<int:id>", csrf_exempt(views.save_serviceDeadline), name="save_serviceDeadline"),     # Json
    path("consolidado/<int:form_id>",csrf_exempt(views.ConsolidadosBase.as_view()),name="consolidado"),              # Get (Render), Post(Json), Delete(Json)
    path("export_consolidado/<int:id>", csrf_exempt(views.export_consolidado), name="export_consolidado"),           # Json
    path("consolidado/<int:id>/save", csrf_exempt(views.analysisReport_save), name="analysisReport_save"),           # Json
    path("consolidado/methology/<int:id>/save", csrf_exempt(views.analysisReportMethology_save), name="analysisReportMethology_save"),           # Json
    path("consolidado/<int:id>/report", csrf_exempt(views.analysis_report), name="analysis_report"),                 # Json
    path("consolidado/<int:id>/addImage", csrf_exempt(views.analysisReport_addImage), name="analysisReport_addImage"), # Json
    path("consolidado/delete-Img/<int:id>", csrf_exempt(views.analysisReport_deleteImage), name="analysisReport_deleteImage"), # Json
    path("consolidado/<int:id>/template_HE", csrf_exempt(views.template_consolidados_HE), name="template_consolidados_HE"),  # Get (Render)
    path("consolidado/<int:id>/template_HE_diagnostic", csrf_exempt(views.template_consolidados_HE_diagnostic), name="template_consolidados_HE_diagnostic"), # Get (Render)
    path("consolidado/<int:id>/template_HE_contraportada", csrf_exempt(views.template_consolidados_HE_contraportada), name="template_consolidados_HE_contraportada"), # Get (Render)
    path("consolidado/<int:id>/download_HE", csrf_exempt(views.download_consolidados_HE), name="download_consolidados_HE"), # Get (Pdf)
    path("consolidado/methodology", csrf_exempt(views.createMethodology), name="createMethodology"),                 # Json
    path("consolidado/methodology/<int:id>", csrf_exempt(views.saveMethodology), name="saveMethodology"),            # Json
    path("consolidado/methodology/<int:id>/addImage", csrf_exempt(views.createMethodologyImage), name="createMethodologyImage"), # Json
    path("consolidado/methodology/<int:id>/deleteImage", csrf_exempt(views.methodology_deleteImage), name="methodology_deleteImage"), # Json
    path("consolidado/methodology/<int:id>/delete", csrf_exempt(views.deleteMethodology), name="deleteMethodology"), # Json
    path("consolidado/analysis/<int:id>/methodology", csrf_exempt(views.ExamMethodologys), name="ExamMethodologys"), # Json

    #SG

    path("consolidado/<int:id>/download_SG", csrf_exempt(views.download_consolidados_SG), name="download_consolidados_SG"), # Json
    path("consolidado/<int:id>/template_SG", csrf_exempt(views.template_consolidados_SG), name="template_consolidados_SG"), # Get (Render)
    path("consolidado/<int:id>/template_SG_diagnostic", csrf_exempt(views.template_consolidados_SG_diagnostic), name="template_consolidados_SG_diagnostic"), # Get (Render)
    path("consolidado/<int:id>/template_SG_contraportada", csrf_exempt(views.template_consolidados_SG_contraportada), name="template_consolidados_SG_contraportada"), # Get (Render)
]
