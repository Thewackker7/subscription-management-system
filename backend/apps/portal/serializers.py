from rest_framework import serializers

from apps.accounts.models import User
from apps.billing.serializers import InvoiceSerializer
from apps.payments.serializers import PaymentSerializer
from apps.subscriptions.serializers import SubscriptionSerializer


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "date_joined")
        read_only_fields = ("id", "email", "date_joined")
