from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.permissions import IsAdminOrStaff
from .models import Invoice
from .serializers import BillingGenerationSerializer, InvoiceSerializer
from .services import generate_due_invoices, generate_invoice_for_subscription


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        queryset = Invoice.objects.select_related("subscription", "customer").prefetch_related("lines__product", "lines__variant", "lines__tax_rule")
        if self.request.user.role == User.Role.CUSTOMER:
            return queryset.filter(customer=self.request.user)
        return queryset

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [IsAuthenticated()]
        return [IsAdminOrStaff()]

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        invoice = self.get_object()
        try:
            invoice.confirm()
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict)
        return Response(self.get_serializer(invoice).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        invoice = self.get_object()
        try:
            invoice.cancel()
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict)
        return Response(self.get_serializer(invoice).data)

    @action(detail=True, methods=["post"], url_path="send", url_name="send")
    def mark_sent(self, request, pk=None):
        """Record send intent only; email delivery belongs to a separate configured service."""
        invoice = self.get_object()
        if invoice.status == Invoice.Status.DRAFT:
            invoice.confirm()
        if invoice.status != Invoice.Status.CONFIRMED:
            raise ValidationError({"detail": "Only confirmed invoices can be marked sent."})
        invoice.sent_at = timezone.now()
        invoice.save(update_fields=["sent_at"])
        return Response({"detail": "Invoice marked as sent. No email delivery was attempted.", "invoice": self.get_serializer(invoice).data})

    @action(detail=True, methods=["get"])
    def print_ready(self, request, pk=None):
        return Response(self.get_serializer(self.get_object()).data)


class BillingGenerateView(APIView):
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        serializer = BillingGenerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        as_of = serializer.validated_data.get("as_of") or timezone.localdate()
        subscription_id = serializer.validated_data.get("subscription_id")
        if subscription_id:
            invoice, created = generate_invoice_for_subscription(subscription_id, as_of)
            return Response({"generated": [InvoiceSerializer(invoice).data] if invoice and created else [],
                             "existing": [InvoiceSerializer(invoice).data] if invoice and not created else []})
        generated, existing = generate_due_invoices(as_of)
        return Response({"generated": InvoiceSerializer(generated, many=True).data, "existing": InvoiceSerializer(existing, many=True).data})
