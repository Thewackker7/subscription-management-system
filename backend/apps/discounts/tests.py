from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.models import Plan, Product, TaxRule
from apps.subscriptions.models import Subscription, SubscriptionLine
from apps.billing.models import Invoice
from .models import DiscountRule


class DiscountTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin@example.com", "AdminPass1!", role=User.Role.ADMIN)
        self.staff = User.objects.create_user("staff@example.com", "StaffPass1!", role=User.Role.STAFF)
        self.customer = User.objects.create_user("customer@example.com", "Customer1!")
        plan = Plan.objects.create(name="Monthly", billing_interval="MONTHLY")
        self.product = Product.objects.create(name="Workspace", product_type="SERVICE", sales_price=Decimal("100.00"), cost_price=Decimal("10.00"))
        tax = TaxRule.objects.create(name="GST", rate=Decimal("10.00"))
        self.subscription = Subscription.objects.create(customer=self.customer, plan=plan, start_date=date(2026, 1, 1), expiry_date=date(2026, 12, 31), status=Subscription.Status.ACTIVE, next_billing_date=date(2026, 1, 1))
        SubscriptionLine.objects.create(subscription=self.subscription, product=self.product, description="Workspace", quantity=2, unit_price=Decimal("100.00"), tax_rule=tax, tax_rate=tax.rate)

    def create_rule(self, **extra):
        data = {"name": "Ten off", "discount_type": "PERCENTAGE", "value": "10.00", "scope": "SUBSCRIPTION", "minimum_purchase_amount": "0.00", "minimum_quantity": 0, "starts_on": "2026-01-01", "maximum_uses": 1}
        data.update(extra)
        self.client.force_authenticate(self.admin)
        return self.client.post(reverse("discount-list"), data, format="json")

    def test_admin_only_and_percentage_discount_recalculates_tax(self):
        self.client.force_authenticate(self.staff)
        forbidden = self.client.post(reverse("discount-list"), {"name": "no", "discount_type": "FIXED", "value": "1", "scope": "SUBSCRIPTION", "starts_on": "2026-01-01"}, format="json")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.create_rule().status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(self.staff)
        response = self.client.post(reverse("billing-generate"), {"subscription_id": self.subscription.id, "as_of": "2026-01-01"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice = Invoice.objects.get()
        self.assertEqual(invoice.discount_total, Decimal("20.00"))
        self.assertEqual(invoice.tax_total, Decimal("18.00"))
        self.assertEqual(invoice.total, Decimal("198.00"))
        self.assertEqual(DiscountRule.objects.get().usage_count, 1)

    def test_product_scope_and_expired_rule_are_not_applied(self):
        created = self.create_rule(name="Product fixed", discount_type="FIXED", value="30.00", scope="PRODUCT", products=[self.product.id])
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.create_rule(name="Expired", ends_on="2026-01-01", maximum_uses=None)
        self.client.force_authenticate(self.staff)
        self.client.post(reverse("billing-generate"), {"subscription_id": self.subscription.id, "as_of": "2026-01-02"}, format="json")
        invoice = Invoice.objects.get()
        self.assertEqual(invoice.discount_total, Decimal("30.00"))
