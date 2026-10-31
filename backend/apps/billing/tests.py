from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.models import Plan, Product, TaxRule
from apps.subscriptions.models import Subscription, SubscriptionLine
from .models import Invoice
from .services import add_interval


class BillingTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff@example.com", "StaffPass1!", role=User.Role.STAFF)
        self.customer = User.objects.create_user("customer@example.com", "Customer1!")
        self.plan = Plan.objects.create(name="Monthly", billing_interval="MONTHLY")
        product = Product.objects.create(name="Workspace", product_type="SERVICE", sales_price=Decimal("100.00"), cost_price=Decimal("20.00"))
        tax = TaxRule.objects.create(name="GST", rate=Decimal("18.00"))
        self.subscription = Subscription.objects.create(customer=self.customer, plan=self.plan, start_date=date(2026, 1, 31), expiry_date=date(2026, 12, 31), status=Subscription.Status.ACTIVE, next_billing_date=date(2026, 1, 31))
        SubscriptionLine.objects.create(subscription=self.subscription, product=product, description="Workspace", quantity=1, unit_price=Decimal("100.00"), tax_rule=tax, tax_rate=tax.rate)
        self.client.force_authenticate(self.staff)

    def test_interval_calculation_and_idempotent_billing(self):
        self.assertEqual(add_interval(date(2026, 1, 31), "MONTHLY", 1), date(2026, 2, 28))
        self.assertEqual(add_interval(date(2024, 2, 29), "YEARLY", 1), date(2025, 2, 28))
        response = self.client.post(reverse("billing-generate"), {"subscription_id": self.subscription.id, "as_of": "2026-01-31"}, format="json")
        self.assertEqual(len(response.data["generated"]), 1)
        invoice = Invoice.objects.get()
        self.assertEqual(invoice.billing_period_end, date(2026, 2, 27))
        self.assertEqual(invoice.subtotal, Decimal("100.00"))
        self.assertEqual(invoice.tax_total, Decimal("18.00"))
        self.assertEqual(invoice.total, Decimal("118.00"))
        repeat = self.client.post(reverse("billing-generate"), {"subscription_id": self.subscription.id, "as_of": "2026-01-31"}, format="json")
        self.assertEqual(len(repeat.data["generated"]), 0)
        self.assertEqual(Invoice.objects.count(), 1)

    def test_customer_invoice_isolation_and_cancellation(self):
        self.client.post(reverse("billing-generate"), {"subscription_id": self.subscription.id, "as_of": "2026-01-31"}, format="json")
        invoice = Invoice.objects.get()
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get(reverse("invoice-detail", args=[invoice.id])).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(reverse("invoice-cancel", args=[invoice.id]), {}, format="json").status_code, status.HTTP_403_FORBIDDEN)
