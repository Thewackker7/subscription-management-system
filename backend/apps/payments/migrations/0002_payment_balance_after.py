from decimal import Decimal

from django.db import migrations, models


def populate_balance_after(apps, schema_editor):
    Payment = apps.get_model("payments", "Payment")
    Invoice = apps.get_model("billing", "Invoice")

    for invoice_id in Payment.objects.values_list("invoice_id", flat=True).distinct():
        invoice = Invoice.objects.get(pk=invoice_id)
        total_paid = Decimal("0.00")
        payments = Payment.objects.filter(invoice_id=invoice_id).order_by("created_at", "id")
        for payment in payments:
            total_paid += payment.amount
            payment.balance_after = max(Decimal("0.00"), invoice.total - total_paid)
            payment.save(update_fields=["balance_after"])


class Migration(migrations.Migration):
    dependencies = [("payments", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="balance_after",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), editable=False, max_digits=14),
        ),
        migrations.RunPython(populate_balance_after, migrations.RunPython.noop),
    ]
