"""ParkiPay — Auth URL Routes"""
from django.urls import path
from apps.accounts.views import LoginView, RefreshView, LogoutView, MeView

urlpatterns = [
    # POST { employee_id, password } → { access, refresh, officer }
    path("login/", LoginView.as_view(), name="auth-login"),

    # POST { refresh } → { access, refresh }
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),

    # POST { refresh } → 200 OK (blacklists token)
    path("logout/", LogoutView.as_view(), name="auth-logout"),

    # GET → officer profile JSON
    path("me/", MeView.as_view(), name="auth-me"),
]
