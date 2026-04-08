from django.contrib.auth.decorators import login_required
from django.urls import path

from apps.accounts.views import (
    login_ajax,
    register_ajax,
    logout_ajax,
    profile_view,
    login_page,
    delete_account,
    set_theme,
)

urlpatterns = [
    path("login/", login_page, name="login"),
    path("login/ajax/", login_ajax, name="login_ajax"),
    path("register/ajax/", register_ajax, name="register_ajax"),
    path("logout/ajax/", logout_ajax, name="logout_ajax"),
    path("profile/", login_required(profile_view), name="profile"),
    path("delete-account/", delete_account, name="delete_account"),
    path("set-theme/", set_theme, name="set_theme"),
    # path("profile/", profile, name="profile"),
]
