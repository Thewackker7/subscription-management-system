from rest_framework import serializers

from apps.billing.models import Invoice
from .models import Payment
from .services import record_payment


class PaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source="invoice.number", read_only=True)

    class Meta:
        model = Payment
        fields = ("id", "identifier", "invoice", "invoice_number", "method", "amount", "payment_date", "note", "external_reference", "balance_after", "created_at")
        read_only_fields = ("id", "identifier", "invoice_number", "balance_after", "created_at")

    def validate_external_reference(self, value):
        return value or None

    def create(self, validated_data):
        invoice = validated_data.pop("invoice")
        return record_payment(invoice_id=invoice.id, **validated_data)
