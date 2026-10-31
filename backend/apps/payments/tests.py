from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.billing.models import Invoice
from apps.catalog.models import Plan
from apps.subscriptions.models import Subscription
from .models import Payment


class PaymentTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff@example.com", "StaffPass1!", role=User.Role.STAFF)
        self.customer = User.objects.create_user("customer@example.com", "Customer1!")
        plan = Plan.objects.create(name="Monthly", billing_interval="MONTHLY")
        subscription = Subscription.objects.create(customer=self.customer, plan=plan, start_date=date(2026, 1, 1), expiry_date=date(2026, 12, 31))
        self.invoice = Invoice.objects.create(subscription=subscription, customer=self.customer, customer_email=self.customer.email,
            billing_period_start=date(2026, 1, 1), billing_period_end=date(2026, 1, 31), due_date=date(2026, 1, 15),
            subtotal=Decimal("100.00"), total=Decimal("100.00"), status=Invoice.Status.CONFIRMED)
        self.client.force_authenticate(self.staff)

    def test_partial_multiple_and_full_payment_updates_invoice(self):
        payload = {"invoice": self.invoice.id, "method": "UPI", "amount": "40.00", "payment_date": "2026-01-10", "external_reference": "upi-1"}
        first = self.client.post(reverse("payment-list"), payload, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, Decimal("40.00"))
        self.assertEqual(self.invoice.status, Invoice.Status.CONFIRMED)
        second = self.client.post(reverse("payment-list"), {**payload, "amount": "60.00", "external_reference": "upi-2"}, format="json")
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, Decimal("100.00"))
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)
        self.assertEqual(Payment.objects.count(), 2)

    def test_excessive_payment_is_rejected_and_customer_cannot_record(self):
        rejected = self.client.post(reverse("payment-list"), {"invoice": self.invoice.id, "method": "CARD", "amount": "100.01", "payment_date": "2026-01-10"}, format="json")
        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST)
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.post(reverse("payment-list"), {"invoice": self.invoice.id, "method": "CARD", "amount": "10.00", "payment_date": "2026-01-10"}, format="json").status_code, status.HTTP_403_FORBIDDEN)
