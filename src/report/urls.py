from django.urls import path

from report import views


app_name = "report"
urlpatterns = [
    path("service", views.service_report, name="service"),
    path("service/table", views.services_table, name="services_table"),
    path("efficiency", views.EfficiencyView.as_view(), name="efficiency"),
    path("control", views.ControlView.as_view(), name="control"),
    path("control/efficiency", views.control_charts, name="control_efficiency_charts"),
    path(
        "control/response", views.response_time_charts, name="control_response_charts"
    ),
]
