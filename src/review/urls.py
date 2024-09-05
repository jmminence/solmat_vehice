from django.urls import path

from review import views


app_name = "review"
urlpatterns = [
    path("", views.index, name="index"),
    path("state/<int:index>", views.list, name="list"),
    path("stage/<int:type>/<int:pk>/", views.UpdateStageView.as_view(), name="stage"),
    path("files/<int:type>/<int:pk>/", views.FileView.as_view(), name="files"),
    path("recipients/", views.new_recipient, name="create_recipient"),
    path(
        "recipients/<int:type>/<int:pk>/", views.AnalysisRecipientView.as_view(), name="recipients"
    ),
    path("lists/<int:pk>/", views.MailListView.as_view(), name="mail_list"),
    path(
        "object/<int:type>/<int:pk>/mails", views.object_mailing_list, name="analysis_emails"
    ),
    path("send", views.EmailSendView.as_view(), name="send_email"),
    path("final_report/<int:type>/<int:pk>", views.FinalReportView.as_view(), name="final_report"),
    path("attachment/<int:type>/<int:pk>", views.AttachmentView.as_view(), name="attachment"),
    path("grouper", views.GrouperView.as_view(), name="groupers")
]
