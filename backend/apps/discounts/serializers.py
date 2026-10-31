from decimal import Decimal

from rest_framework import serializers
from .models import DiscountApplication, DiscountRule


class DiscountRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountRule
        fields = ("id", "name", "discount_type", "value", "scope", "products", "minimum_purchase_amount", "minimum_quantity", "starts_on", "ends_on", "maximum_uses", "usage_count", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "usage_count", "created_at", "updated_at")

    def validate(self, attrs):
        scope = attrs.get("scope", getattr(self.instance, "scope", None))
        products_were_supplied = "products" in attrs
        products = attrs.get("products")
        if scope == DiscountRule.Scope.PRODUCT:
            if products_were_supplied and not products:
                raise serializers.ValidationError({"products": "Product-scoped discounts require at least one product."})
            if not products_were_supplied and not (self.instance and self.instance.products.exists()):
                raise serializers.ValidationError({"products": "Product-scoped discounts require at least one product."})
        discount_type = attrs.get("discount_type", getattr(self.instance, "discount_type", None))
        value = attrs.get("value", getattr(self.instance, "value", None))
        if discount_type == DiscountRule.DiscountType.PERCENTAGE and value is not None and value > Decimal("100.00"):
            raise serializers.ValidationError({"value": "Percentage discounts cannot exceed 100%."})
        starts_on = attrs.get("starts_on", getattr(self.instance, "starts_on", None))
        ends_on = attrs.get("ends_on", getattr(self.instance, "ends_on", None))
        if starts_on and ends_on and ends_on < starts_on:
            raise serializers.ValidationError({"ends_on": "Must be on or after starts_on."})
        return attrs


class DiscountApplicationSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source="rule.name", read_only=True)
    class Meta:
        model = DiscountApplication
        fields = ("id", "rule", "rule_name", "amount", "applied_at")
