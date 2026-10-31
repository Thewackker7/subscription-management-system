from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import BillingGenerateView, InvoiceViewSet

router = DefaultRouter()
router.register("invoices", InvoiceViewSet, basename="invoice")
urlpatterns = [path("generate/", BillingGenerateView.as_view(), name="billing-generate"), path("", include(router.urls))]
