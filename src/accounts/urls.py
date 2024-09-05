from django.conf.urls import re_path
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import views as auth_views
from accounts import views

urlpatterns = [
    re_path(r"^user/$", csrf_exempt(views.USER.as_view()), name="user"),
    re_path(
        r"^user/(?P<id>\d+)$", csrf_exempt(views.USER.as_view()), name="user_with_id"
    ),
    re_path(r"^register/$", views.register, name="register"),
    re_path(r"^login/$", views.user_login, name="login"),
    re_path(r"^logout/$", views.user_logout, name="logout"),
    re_path(r"^profile$", views.user_profile, name="profile"),
    re_path(
        r"^changepassword/$", csrf_exempt(views.change_password), name="change-password"
    ),
    re_path(r"^changeinfo/$", csrf_exempt(views.change_info), name="change_info"),
    re_path(r"^permisos/$", csrf_exempt(views.PERMISOS.as_view()), name="permisos"),
]
