from datetime import date
from decimal import Decimal
from django.db import IntegrityError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User
from .models import Plan, Product, ProductVariant, TaxRule


class CatalogModelTests(APITestCase):
    def test_variant_sales_price_adds_to_base_product_price(self):
        product = Product.objects.create(name="Cloud Workspace", product_type="SERVICE", sales_price=Decimal("1000.00"), cost_price=Decimal("100.00"))
        variant = ProductVariant.objects.create(product=product, label="Odoo", extra_price=Decimal("560.00"))
        self.assertEqual(variant.sales_price, Decimal("1560.00"))

    def test_tax_rate_cannot_exceed_100_percent(self):
        with self.assertRaises(IntegrityError):
            TaxRule.objects.create(name="Impossible", rate=Decimal("100.01"))

    def test_plan_rejects_invalid_availability_dates_at_api_boundary(self):
        admin = User.objects.create_user("admin@example.com", "AdminPass1!", role=User.Role.ADMIN)
        self.client.force_authenticate(admin)
        response = self.client.post(reverse("plan-list"), {"name": "Monthly", "billing_interval": "MONTHLY", "available_from": "2026-02-01", "available_until": "2026-01-01"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_catalog_requires_admin(self):
        customer = User.objects.create_user("customer@example.com", "Customer1!")
        self.client.force_authenticate(customer)
        response = self.client.get(reverse("product-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
