from datetime import timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import User
from apps.catalog.models import Plan
from .models import Quotation, QuotationLine, QuotationTemplate, QuotationTemplateLine, Subscription, SubscriptionLine


class PriceLineSerializer(serializers.ModelSerializer):
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    description = serializers.CharField(required=False)

    def validate(self, attrs):
        product = attrs.get("product", getattr(self.instance, "product", None))
        variant = attrs.get("variant", getattr(self.instance, "variant", None))
        if variant and variant.product_id != product.id:
            raise serializers.ValidationError({"variant": "Variant must belong to the selected product."})
        if "unit_price" not in attrs and not self.instance:
            attrs["unit_price"] = variant.sales_price if variant else product.sales_price
        if "description" not in attrs and not self.instance:
            attrs["description"] = variant.label if variant else product.name
        tax_rule = attrs.get("tax_rule", getattr(self.instance, "tax_rule", None))
        if tax_rule:
            attrs["tax_rate"] = tax_rule.rate
        return attrs


class SubscriptionLineSerializer(PriceLineSerializer):
    class Meta:
        model = SubscriptionLine
        fields = ("id", "product", "variant", "description", "quantity", "unit_price", "tax_rule", "tax_rate", "subtotal", "tax_amount", "total")
        read_only_fields = ("id", "tax_rate", "subtotal", "tax_amount", "total")


class SubscriptionSerializer(serializers.ModelSerializer):
    lines = SubscriptionLineSerializer(many=True)
    customer_email = serializers.EmailField(source="customer.email", read_only=True)

    class Meta:
        model = Subscription
        fields = ("id", "number", "customer", "customer_email", "plan", "start_date", "expiry_date", "payment_terms_days", "status", "next_billing_date", "is_paused", "paused_at", "closed_at", "notes", "lines", "created_at", "updated_at")
        read_only_fields = ("id", "number", "status", "next_billing_date", "is_paused", "paused_at", "closed_at", "created_at", "updated_at")

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        expiry = attrs.get("expiry_date", getattr(self.instance, "expiry_date", None))
        if start and expiry and expiry < start:
            raise serializers.ValidationError({"expiry_date": "Must be on or after start_date."})
        plan = attrs.get("plan", getattr(self.instance, "plan", None))
        for line in attrs.get("lines", []):
            if plan and line["quantity"] < plan.minimum_quantity:
                raise serializers.ValidationError({"lines": "A line quantity is below the plan minimum quantity."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        lines = validated_data.pop("lines")
        subscription = Subscription(**validated_data)
        subscription.full_clean()
        subscription.save()
        for line_data in lines:
            line = SubscriptionLine(subscription=subscription, **line_data)
            line.full_clean()
            line.save()
        return subscription


class TemplateLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationTemplateLine
        fields = ("id", "product", "variant", "quantity", "tax_rule")
        read_only_fields = ("id",)

    def validate(self, attrs):
        variant = attrs.get("variant")
        product = attrs.get("product")
        if variant and variant.product_id != product.id:
            raise serializers.ValidationError({"variant": "Variant must belong to the selected product."})
        return attrs


class QuotationTemplateSerializer(serializers.ModelSerializer):
    lines = TemplateLineSerializer(many=True)
    class Meta:
        model = QuotationTemplate
        fields = ("id", "name", "plan", "validity_days", "is_active", "lines", "created_at")
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        plan = attrs.get("plan", getattr(self.instance, "plan", None))
        for line in attrs.get("lines", []):
            if line["quantity"] < plan.minimum_quantity:
                raise serializers.ValidationError({"lines": "A line quantity is below the plan minimum quantity."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        lines = validated_data.pop("lines")
        template = QuotationTemplate.objects.create(**validated_data)
        for line_data in lines:
            QuotationTemplateLine.objects.create(template=template, **line_data)
        return template


class QuotationLineSerializer(PriceLineSerializer):
    class Meta:
        model = QuotationLine
        fields = ("id", "product", "variant", "description", "quantity", "unit_price", "tax_rule", "tax_rate", "subtotal", "tax_amount", "total")
        read_only_fields = ("id", "tax_rate", "subtotal", "tax_amount", "total")


class QuotationSerializer(serializers.ModelSerializer):
    lines = QuotationLineSerializer(many=True, required=False)
    template = serializers.PrimaryKeyRelatedField(queryset=QuotationTemplate.objects.filter(is_active=True), write_only=True, required=False)
    customer_email = serializers.EmailField(source="customer.email", read_only=True)
    valid_until = serializers.DateField(required=False)
    plan = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all(), required=False)

    class Meta:
        model = Quotation
        fields = ("id", "number", "customer", "customer_email", "plan", "valid_until", "status", "notes", "converted_subscription", "template", "lines", "created_at")
        read_only_fields = ("id", "number", "status", "converted_subscription", "created_at")

    def validate(self, attrs):
        template = attrs.get("template")
        lines = attrs.get("lines")
        if template and "plan" in attrs and attrs["plan"] != template.plan:
            raise serializers.ValidationError({"plan": "Must match the selected template plan."})
        if not template and not lines and not self.instance:
            raise serializers.ValidationError({"lines": "Provide lines or a quotation template."})
        if not template and not attrs.get("valid_until") and not self.instance:
            raise serializers.ValidationError({"valid_until": "This field is required without a template."})
        if not template and not attrs.get("plan") and not self.instance:
            raise serializers.ValidationError({"plan": "This field is required without a template."})
        customer = attrs.get("customer", getattr(self.instance, "customer", None))
        if customer and customer.role != User.Role.CUSTOMER:
            raise serializers.ValidationError({"customer": "Quotations can only belong to Customer users."})
        plan = attrs.get("plan", template.plan if template else getattr(self.instance, "plan", None))
        if plan and not plan.is_active:
            raise serializers.ValidationError({"plan": "Plan is inactive."})
        for line in lines or []:
            if plan and line["quantity"] < plan.minimum_quantity:
                raise serializers.ValidationError({"lines": "A line quantity is below the plan minimum quantity."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        template = validated_data.pop("template", None)
        lines = validated_data.pop("lines", None)
        if template:
            validated_data["plan"] = template.plan
            if not validated_data.get("valid_until"):
                validated_data["valid_until"] = timezone.localdate() + timedelta(days=template.validity_days)
            lines = [{"product": item.product, "variant": item.variant, "description": item.variant.label if item.variant else item.product.name,
                      "quantity": item.quantity, "unit_price": item.variant.sales_price if item.variant else item.product.sales_price,
                      "tax_rule": item.tax_rule, "tax_rate": item.tax_rule.rate if item.tax_rule else Decimal("0.00")} for item in template.lines.select_related("product", "variant", "tax_rule")]
        quotation = Quotation.objects.create(**validated_data)
        for line_data in lines or []:
            QuotationLine.objects.create(quotation=quotation, **line_data)
        return quotation


class SubscriptionTransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Subscription.Status.choices)


class RenewSerializer(serializers.Serializer):
    expiry_date = serializers.DateField()

    def validate_expiry_date(self, value):
        if value <= self.context["subscription"].expiry_date:
            raise serializers.ValidationError("Must be later than the current expiry date.")
        return value


class QuotationConversionSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    expiry_date = serializers.DateField()
    payment_terms_days = serializers.IntegerField(min_value=0, default=30)

    def validate(self, attrs):
        if attrs["expiry_date"] < attrs["start_date"]:
            raise serializers.ValidationError({"expiry_date": "Must be on or after start_date."})
        return attrs
