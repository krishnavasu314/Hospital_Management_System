from django.urls import path

from .views import UserLoginView, UserLogoutView, dashboard, google_callback, google_connect, signup


urlpatterns = [
    path("accounts/login/", UserLoginView.as_view(), name="login"),
    path("accounts/logout/", UserLogoutView.as_view(), name="logout"),
    path("accounts/signup/", signup, name="signup"),
    path("accounts/google/connect/", google_connect, name="google-connect"),
    path("accounts/google/callback/", google_callback, name="google-callback"),
    path("dashboard/", dashboard, name="dashboard"),
]
