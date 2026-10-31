from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import HealthCheckView, LoginView, PasswordResetConfirmView, PasswordResetRequestView, RegisterView, StaffCreateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", HealthCheckView.as_view(), name="health"),
    path("api/v1/auth/register/", RegisterView.as_view(), name="register"),
    path("api/v1/auth/login/", LoginView.as_view(), name="login"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/v1/auth/password-reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("api/v1/auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("api/v1/users/staff/", StaffCreateView.as_view(), name="staff-create"),
    path("api/v1/catalog/", include("apps.catalog.urls")),
    path("api/v1/subscriptions/", include("apps.subscriptions.urls")),
    path("api/v1/billing/", include("apps.billing.urls")),
]
