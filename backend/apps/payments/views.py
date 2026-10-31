from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import User
from apps.accounts.permissions import IsAdminOrStaff
from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = Payment.objects.select_related("invoice", "invoice__customer")
        if self.request.user.role == User.Role.CUSTOMER:
            return queryset.filter(invoice__customer=self.request.user)
        return queryset

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [IsAuthenticated()]
        return [IsAdminOrStaff()]
