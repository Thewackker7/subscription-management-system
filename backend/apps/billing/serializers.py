from rest_framework import serializers
from .models import Invoice, InvoiceLine


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = ("id", "product", "variant", "description", "quantity", "unit_price", "tax_rule", "tax_rate", "subtotal", "tax_amount", "total")


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)
    balance = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    discount_applications = serializers.SerializerMethodField()

    def get_discount_applications(self, invoice):
        return [{"id": item.id, "rule": item.rule_id, "rule_name": item.rule.name, "amount": item.amount, "applied_at": item.applied_at}
                for item in invoice.discount_applications.select_related("rule").all()]

    class Meta:
        model = Invoice
        fields = ("id", "number", "subscription", "customer", "customer_email", "customer_name", "billing_period_start", "billing_period_end", "issue_date", "due_date", "status", "subtotal", "tax_total", "discount_total", "discount_applications", "total", "amount_paid", "balance", "is_overdue", "sent_at", "cancelled_at", "lines", "created_at")
        read_only_fields = fields


class BillingGenerationSerializer(serializers.Serializer):
    subscription_id = serializers.IntegerField(required=False, min_value=1)
    as_of = serializers.DateField(required=False)
