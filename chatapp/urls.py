from django.urls import path

from . import views

app_name = "chatapp"

urlpatterns = [
    # Public pages
    path("", views.landing_view, name="landing"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    # The app
    path("chat/", views.chat_view, name="chat"),
    path("chat/ask/", views.ask_view, name="ask"),
    path("chat/clear/", views.clear_chat_view, name="clear_chat"),
    path("knowledge-base/", views.knowledge_base_view, name="knowledge_base"),
]
