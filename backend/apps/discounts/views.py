from rest_framework import viewsets

from apps.accounts.permissions import IsAdminRole
from .models import DiscountRule
from .serializers import DiscountRuleSerializer


class DiscountRuleViewSet(viewsets.ModelViewSet):
    queryset = DiscountRule.objects.prefetch_related("products")
    serializer_class = DiscountRuleSerializer
    permission_classes = [IsAdminRole]
