from rest_framework import viewsets
from apps.accounts.permissions import IsAdminRole
from .models import Plan, Product, ProductVariant, TaxRule
from .serializers import PlanSerializer, ProductSerializer, ProductVariantSerializer, TaxRuleSerializer


class AdminCatalogViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminRole]


class ProductViewSet(AdminCatalogViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductVariantViewSet(AdminCatalogViewSet):
    queryset = ProductVariant.objects.select_related("product")
    serializer_class = ProductVariantSerializer


class PlanViewSet(AdminCatalogViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer


class TaxRuleViewSet(AdminCatalogViewSet):
    queryset = TaxRule.objects.all()
    serializer_class = TaxRuleSerializer
