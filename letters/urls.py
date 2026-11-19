from django.urls import path

from . import views

app_name = "letters"

urlpatterns = [
    path("", views.home, name="home"),
    path("explore/", views.explore, name="explore"),
    path("health/", views.health, name="health"),

    # Auth
    path("accounts/signup/", views.signup, name="signup"),
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),

    # Dashboard & creator
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/new/", views.editor_create, name="editor_create"),
    path("dashboard/<slug:slug>/edit/", views.editor_update, name="editor_update"),
    path("dashboard/<slug:slug>/preview/", views.preview_letter, name="preview"),
    path("dashboard/<slug:slug>/publish/", views.letter_publish, name="publish"),
    path("dashboard/<slug:slug>/unpublish/", views.letter_unpublish, name="unpublish"),
    path("dashboard/<slug:slug>/delete/", views.letter_delete, name="delete"),
    path("dashboard/<slug:slug>/duplicate/", views.letter_duplicate, name="duplicate"),
    path("dashboard/<slug:slug>/photos/<int:photo_id>/delete/", views.photo_delete, name="photo_delete"),
    path("dashboard/<slug:slug>/photos/reorder/", views.photo_reorder, name="photo_reorder"),

    # Public letter experience
    path("letter/<slug:slug>/", views.letter_detail, name="letter"),
    path("letter/<slug:slug>/qr.png", views.letter_qr, name="qr"),
]
