from django.urls import path

from lab import views


app_name = "lab"
urlpatterns = [
    path("", views.home, name="home"),
    path("case/<int:pk>", views.CaseDetail.as_view(), name="case_detail"),
    path("case/<int:pk>/sheet", views.CaseReadSheet.as_view(), name="case_read_sheet"),
    path(
        "analysis/<int:pk>/sheet",
        views.AnalysisReadSheet.as_view(),
        name="analysis_read_sheet",
    ),
    path("case/<int:pk>/state", views.case_process_state, name="case_process_state"),
    path(
        "case/<int:pk>/<int:step>/edit",
        views.redirect_to_workflow_edit,
        name="redirect_to_workflow_edit",
    ),
    path("cases", views.case_select_options, name="case_select_options"),
    path(
        "difference/<int:pk>",
        views.update_unit_difference,
        name="update_unit_difference",
    ),
    path("organs", views.organ_list, name="organ_index"),
    path("stains", views.stain_list, name="stain_index"),
    path("units", views.unit_select_options, name="unit_select_options"),
    path("refresh_portal/<int:pk>", views.refresh_portal, name="refresh_portal"),
    path("resumen/<int:entryform_pk>/<int:user_pk>/<str:language>", views.template_resumen_report, name="resumen"),
    #
    # Cassettes Routes
    #
    path("cassettes", views.CassetteHome.as_view(), name="cassette_home"),
    path("cassettes/index", views.CassetteIndex.as_view(), name="cassette_index"),
    path("cassettes/diff", views.cassette_differences, name="cassette_difference"),
    path("cassettes/<int:pk>", views.CassetteDetail.as_view(), name="cassette_detail"),
    path("cassettes/prebuild", views.cassette_prebuild, name="cassette_prebuild"),
    path("cassettes/build", views.CassetteBuild.as_view(), name="cassette_build"),
    path("cassettes/process", views.CassetteProcess.as_view(), name="cassette_process"),
    #
    # Slide Routes
    #
    path("slides", views.SlideHome.as_view(), name="slide_home"),
    path("slides/index", views.SlideIndex.as_view(), name="slide_index"),
    path("slides/<int:pk>", views.SlideDetail.as_view(), name="slide_detail"),
    path("slides/prebuild", views.slide_prebuild, name="slide_prebuild"),
    path("slides/build", views.SlideBuild.as_view(), name="slide_build"),
    path("slides/release", views.SlideRelease.as_view(), name="slide_release"),
    path("slides/stain", views.SlideStain.as_view(), name="slide_stain"),
    path("slides/hide", views.slide_hide, name="slide_hide"),
    #
    # Process Routes
    #
    path("process", views.ProcessList.as_view(), name="process_index"),
    path("process/<int:process_type>", views.ProcessBuild.as_view(), name="process_build"),
]
