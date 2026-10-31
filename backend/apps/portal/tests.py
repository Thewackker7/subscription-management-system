from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.billing.models import Invoice
from apps.catalog.models import Plan
from apps.subscriptions.models import Subscription


class PortalTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user("customer@example.com", "Customer1!", first_name="Asha")
        self.other = User.objects.create_user("other@example.com", "Customer1!")
        plan = Plan.objects.create(name="Monthly", billing_interval="MONTHLY")
        subscription = Subscription.objects.create(customer=self.customer, plan=plan, start_date=date(2026, 1, 1), expiry_date=date(2026, 12, 31))
        self.invoice = Invoice.objects.create(subscription=subscription, customer=self.customer, customer_email=self.customer.email,
            billing_period_start=date(2026, 1, 1), billing_period_end=date(2026, 1, 31), due_date=date(2026, 1, 15), total=Decimal("100.00"), status=Invoice.Status.CONFIRMED)

    def test_customer_portal_owns_profile_and_denies_other_invoice(self):
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get(reverse("portal-profile")).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse("portal-invoice-detail", args=[self.invoice.id])).status_code, status.HTTP_200_OK)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(reverse("portal-invoice-detail", args=[self.invoice.id])).status_code, status.HTTP_404_NOT_FOUND)

    def test_summary_excludes_draft_invoice_from_outstanding_balance(self):
        Invoice.objects.create(
            subscription=self.invoice.subscription,
            customer=self.customer,
            customer_email=self.customer.email,
            billing_period_start=date(2026, 2, 1),
            billing_period_end=date(2026, 2, 28),
            due_date=date(2026, 2, 15),
            total=Decimal("500.00"),
            status=Invoice.Status.DRAFT,
        )
        self.client.force_authenticate(self.customer)
        response = self.client.get(reverse("portal-summary"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data["outstanding_balance"]), Decimal("100.00"))
