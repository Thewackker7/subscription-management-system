from django.db.models import Sum
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.billing.models import Invoice
from apps.billing.serializers import InvoiceSerializer
from apps.payments.models import Payment
from apps.payments.serializers import PaymentSerializer
from apps.subscriptions.models import Subscription
from apps.subscriptions.serializers import SubscriptionSerializer
from .serializers import CustomerProfileSerializer


class CustomerPortalMixin:
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user.role != User.Role.CUSTOMER:
            raise PermissionDenied("Customer role required for portal access.")


class ProfileView(CustomerPortalMixin, generics.RetrieveUpdateAPIView):
    serializer_class = CustomerProfileSerializer

    def get_object(self):
        return self.request.user


class MySubscriptionsView(CustomerPortalMixin, generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    def get_queryset(self):
        return Subscription.objects.filter(customer=self.request.user).select_related("customer", "plan").prefetch_related("lines__product", "lines__variant", "lines__tax_rule")


class MySubscriptionDetailView(CustomerPortalMixin, generics.RetrieveAPIView):
    serializer_class = SubscriptionSerializer
    def get_queryset(self):
        return Subscription.objects.filter(customer=self.request.user).select_related("customer", "plan").prefetch_related("lines__product", "lines__variant", "lines__tax_rule")


class MyInvoicesView(CustomerPortalMixin, generics.ListAPIView):
    serializer_class = InvoiceSerializer
    def get_queryset(self):
        return Invoice.objects.filter(customer=self.request.user).select_related("subscription", "customer").prefetch_related("lines__product", "lines__variant", "lines__tax_rule", "discount_applications__rule")


class MyInvoiceDetailView(CustomerPortalMixin, generics.RetrieveAPIView):
    serializer_class = InvoiceSerializer
    def get_queryset(self):
        return Invoice.objects.filter(customer=self.request.user).select_related("subscription", "customer").prefetch_related("lines__product", "lines__variant", "lines__tax_rule", "discount_applications__rule")


class MyPaymentsView(CustomerPortalMixin, generics.ListAPIView):
    serializer_class = PaymentSerializer
    def get_queryset(self):
        return Payment.objects.filter(invoice__customer=self.request.user).select_related("invoice")


class PortalSummaryView(CustomerPortalMixin, APIView):
    def get(self, request):
        invoices = Invoice.objects.filter(customer=request.user)
        issued_invoices = invoices.filter(status=Invoice.Status.CONFIRMED)
        outstanding = sum((invoice.balance for invoice in issued_invoices), 0)
        return Response({"active_subscriptions": Subscription.objects.filter(customer=request.user, status=Subscription.Status.ACTIVE).count(),
                         "outstanding_balance": outstanding,
                         "paid_invoice_count": invoices.filter(status=Invoice.Status.PAID).count(),
                         "overdue_invoice_count": sum(1 for invoice in invoices if invoice.is_overdue)})
