from decimal import Decimal

from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminOrStaff
from apps.billing.models import Invoice
from apps.payments.models import Payment


class PaymentSummaryView(APIView):
    """Read-only payment figures for Aswin's future dashboard aggregation."""
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        invoices = Invoice.objects.exclude(status=Invoice.Status.CANCELLED)
        outstanding = sum((invoice.balance for invoice in invoices), Decimal("0.00"))
        return Response({
            "received": Payment.objects.aggregate(value=Sum("amount"))["value"] or Decimal("0.00"),
            "outstanding": outstanding,
            "paid_invoice_count": invoices.filter(status=Invoice.Status.PAID).count(),
            "overdue_invoice_count": sum(1 for invoice in invoices if invoice.is_overdue),
            "discount_total": invoices.aggregate(value=Sum("discount_total"))["value"] or Decimal("0.00"),
        })
