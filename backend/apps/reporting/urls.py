from django.urls import path
from .views import PaymentSummaryView

urlpatterns = [path("payment-summary/", PaymentSummaryView.as_view(), name="payment-summary")]
