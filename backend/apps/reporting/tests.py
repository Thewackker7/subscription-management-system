from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.billing.models import Invoice
from apps.catalog.models import Plan
from apps.subscriptions.models import Subscription


class PaymentSummaryTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff@example.com", "StaffPass1!", role=User.Role.STAFF)
        customer = User.objects.create_user("customer@example.com", "Customer1!")
        plan = Plan.objects.create(name="Monthly", billing_interval="MONTHLY")
        subscription = Subscription.objects.create(
            customer=customer,
            plan=plan,
            start_date=date(2026, 1, 1),
            expiry_date=date(2026, 12, 31),
        )
        Invoice.objects.create(
            subscription=subscription,
            customer=customer,
            customer_email=customer.email,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            due_date=date(2026, 1, 15),
            total=Decimal("100.00"),
            status=Invoice.Status.CONFIRMED,
        )
        Invoice.objects.create(
            subscription=subscription,
            customer=customer,
            customer_email=customer.email,
            billing_period_start=date(2026, 2, 1),
            billing_period_end=date(2026, 2, 28),
            due_date=date(2026, 2, 15),
            total=Decimal("500.00"),
            status=Invoice.Status.DRAFT,
        )
        self.client.force_authenticate(self.staff)

    def test_summary_excludes_draft_invoice_from_outstanding_balance(self):
        response = self.client.get(reverse("payment-summary"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data["outstanding"]), Decimal("100.00"))
