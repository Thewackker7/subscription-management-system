from django.urls import path
from .views import (MyInvoiceDetailView, MyInvoicesView, MyPaymentsView, MySubscriptionDetailView,
                    MySubscriptionsView, PortalSummaryView, ProfileView)

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="portal-profile"),
    path("subscriptions/", MySubscriptionsView.as_view(), name="portal-subscriptions"),
    path("subscriptions/<int:pk>/", MySubscriptionDetailView.as_view(), name="portal-subscription-detail"),
    path("invoices/", MyInvoicesView.as_view(), name="portal-invoices"),
    path("invoices/<int:pk>/", MyInvoiceDetailView.as_view(), name="portal-invoice-detail"),
    path("payments/", MyPaymentsView.as_view(), name="portal-payments"),
    path("summary/", PortalSummaryView.as_view(), name="portal-summary"),
]
