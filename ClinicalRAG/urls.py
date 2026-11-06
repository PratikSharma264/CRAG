from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "accounts/login/",
        LoginView.as_view(
            template_name="chatapp/registration/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("chatapp.urls")),
]
