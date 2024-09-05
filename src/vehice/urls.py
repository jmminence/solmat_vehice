"""vehice URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include, re_path
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django_js_reverse.views import urls_js

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    re_path(r"^grappelli", include("grappelli.urls")),
    re_path(r"^admin/doc/", include("django.contrib.admindocs.urls")),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^accounts/", include("accounts.urls")),
    re_path(r"^", include("app.urls")),
    re_path(r"^", include("backend.urls")),
    re_path(r"lab/", include("lab.urls")),
    re_path(r"report/", include("report.urls")),
    re_path("avatar/", include("avatar.urls")),
    re_path("review/", include("review.urls")),
    re_path(r"api/", include("api.urls")),
    re_path(r"api/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    re_path(r"api/token", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    re_path(r"^jsreverse/$", urls_js, name="js_reverse"),
    re_path(r"^", include("mb.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
