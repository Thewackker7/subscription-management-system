from datetime import date, timedelta
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.models import Plan, Product, ProductVariant, TaxRule
from .models import Quotation, Subscription


class SubscriptionWorkflowTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin@example.com", "AdminPass1!", role=User.Role.ADMIN)
        self.staff = User.objects.create_user("staff@example.com", "StaffPass1!", role=User.Role.STAFF)
        self.customer = User.objects.create_user("customer@example.com", "Customer1!")
        self.other_customer = User.objects.create_user("other@example.com", "Customer1!")
        self.plan = Plan.objects.create(name="Monthly", billing_interval=Plan.BillingInterval.MONTHLY, minimum_quantity=2, allow_pause=True)
        self.product = Product.objects.create(name="Workspace", product_type="SERVICE", sales_price=Decimal("100.00"), cost_price=Decimal("20.00"))
        self.variant = ProductVariant.objects.create(product=self.product, label="Pro", extra_price=Decimal("50.00"))
        self.tax = TaxRule.objects.create(name="GST", rate=Decimal("18.00"))
        self.client.force_authenticate(self.staff)

    def payload(self):
        return {"customer": self.customer.id, "plan": self.plan.id, "start_date": "2026-01-01", "expiry_date": "2026-12-31", "payment_terms_days": 15,
                "lines": [{"product": self.product.id, "variant": self.variant.id, "quantity": 2, "tax_rule": self.tax.id}]}

    def test_subscription_prices_variant_and_tax_and_lifecycle(self):
        response = self.client.post(reverse("subscription-list"), self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        subscription = Subscription.objects.get()
        line = subscription.lines.get()
        self.assertEqual(line.unit_price, Decimal("150.00"))
        self.assertEqual(line.subtotal, Decimal("300.00"))
        self.assertEqual(line.tax_amount, Decimal("54.00"))
        self.assertEqual(line.total, Decimal("354.00"))
        self.assertTrue(subscription.number.startswith("SUB-"))

        url = reverse("subscription-transition", args=[subscription.pk])
        self.assertEqual(self.client.post(url, {"status": "CONFIRMED"}, format="json").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.post(url, {"status": "QUOTATION"}, format="json").status_code, status.HTTP_200_OK)
        self.client.post(url, {"status": "CONFIRMED"}, format="json")
        active = self.client.post(url, {"status": "ACTIVE"}, format="json")
        self.assertEqual(active.status_code, status.HTTP_200_OK)
        self.assertEqual(active.data["next_billing_date"], "2026-01-01")
        self.assertEqual(self.client.post(reverse("subscription-pause", args=[subscription.pk]), {}, format="json").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(reverse("subscription-resume", args=[subscription.pk]), {}, format="json").status_code, status.HTTP_200_OK)

    def test_minimum_quantity_and_customer_isolation(self):
        payload = self.payload()
        payload["lines"][0]["quantity"] = 1
        response = self.client.post(reverse("subscription-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        subscription = Subscription.objects.create(customer=self.customer, plan=self.plan, start_date=date(2026, 1, 1), expiry_date=date(2026, 12, 31))
        self.client.force_authenticate(self.other_customer)
        self.assertEqual(self.client.get(reverse("subscription-detail", args=[subscription.pk])).status_code, status.HTTP_404_NOT_FOUND)

    def test_quotation_template_conversion_is_single_use(self):
        template_response = self.client.post(reverse("quotation-template-list"), {"name": "Monthly workspace", "plan": self.plan.id, "validity_days": 30,
            "lines": [{"product": self.product.id, "variant": self.variant.id, "quantity": 2, "tax_rule": self.tax.id}]}, format="json")
        self.assertEqual(template_response.status_code, status.HTTP_201_CREATED)
        quote_response = self.client.post(reverse("quotation-list"), {"customer": self.customer.id, "template": template_response.data["id"]}, format="json")
        self.assertEqual(quote_response.status_code, status.HTTP_201_CREATED)
        convert_url = reverse("quotation-convert", args=[quote_response.data["id"]])
        conversion = self.client.post(convert_url, {"start_date": "2026-01-01", "expiry_date": "2026-12-31", "payment_terms_days": 15}, format="json")
        self.assertEqual(conversion.status_code, status.HTTP_201_CREATED)
        repeat = self.client.post(convert_url, {"start_date": "2026-01-01", "expiry_date": "2026-12-31"}, format="json")
        self.assertEqual(repeat.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subscription_patch_replaces_draft_lines_and_rejects_invalid_lines(self):
        created = self.client.post(reverse("subscription-list"), self.payload(), format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        subscription_id = created.data["id"]

        update = self.client.patch(reverse("subscription-detail", args=[subscription_id]), {
            "lines": [{"product": self.product.id, "quantity": 3, "tax_rule": self.tax.id}],
        }, format="json")
        self.assertEqual(update.status_code, status.HTTP_200_OK)
        self.assertEqual(len(update.data["lines"]), 1)
        self.assertEqual(update.data["lines"][0]["quantity"], 3)
        self.assertEqual(update.data["lines"][0]["unit_price"], "100.00")

        invalid = self.client.patch(reverse("subscription-detail", args=[subscription_id]), {
            "lines": [{"product": self.product.id, "quantity": 1, "tax_rule": self.tax.id}],
        }, format="json")
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Subscription.objects.get(pk=subscription_id).lines.get().quantity, 3)

    def test_template_and_quotation_patch_replace_lines_safely(self):
        template = self.client.post(reverse("quotation-template-list"), {
            "name": "Editable template", "plan": self.plan.id, "validity_days": 30,
            "lines": [{"product": self.product.id, "variant": self.variant.id, "quantity": 2, "tax_rule": self.tax.id}],
        }, format="json")
        self.assertEqual(template.status_code, status.HTTP_201_CREATED)
        template_update = self.client.patch(reverse("quotation-template-detail", args=[template.data["id"]]), {
            "lines": [{"product": self.product.id, "quantity": 3, "tax_rule": self.tax.id}],
        }, format="json")
        self.assertEqual(template_update.status_code, status.HTTP_200_OK)
        self.assertEqual(template_update.data["lines"][0]["quantity"], 3)

        quotation = self.client.post(reverse("quotation-list"), {
            "customer": self.customer.id, "plan": self.plan.id, "valid_until": "2099-01-01",
            "lines": [{"product": self.product.id, "quantity": 2, "tax_rule": self.tax.id}],
        }, format="json")
        self.assertEqual(quotation.status_code, status.HTTP_201_CREATED)
        quote_update = self.client.patch(reverse("quotation-detail", args=[quotation.data["id"]]), {
            "lines": [{"product": self.product.id, "variant": self.variant.id, "quantity": 2, "tax_rule": self.tax.id}],
        }, format="json")
        self.assertEqual(quote_update.status_code, status.HTTP_200_OK)
        self.assertEqual(quote_update.data["lines"][0]["unit_price"], "150.00")
        empty_lines = self.client.patch(reverse("quotation-detail", args=[quotation.data["id"]]), {"lines": []}, format="json")
        self.assertEqual(empty_lines.status_code, status.HTTP_400_BAD_REQUEST)
