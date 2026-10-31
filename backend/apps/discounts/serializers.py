from rest_framework import serializers
from .models import DiscountApplication, DiscountRule


class DiscountRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountRule
        fields = ("id", "name", "discount_type", "value", "scope", "products", "minimum_purchase_amount", "minimum_quantity", "starts_on", "ends_on", "maximum_uses", "usage_count", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "usage_count", "created_at", "updated_at")

    def validate(self, attrs):
        scope = attrs.get("scope", getattr(self.instance, "scope", None))
        products = attrs.get("products")
        if scope == DiscountRule.Scope.PRODUCT and not products and not (self.instance and self.instance.products.exists()):
            raise serializers.ValidationError({"products": "Product-scoped discounts require at least one product."})
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
