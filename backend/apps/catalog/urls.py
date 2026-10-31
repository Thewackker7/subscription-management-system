from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, ProductVariantViewSet, ProductViewSet, TaxRuleViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("variants", ProductVariantViewSet, basename="variant")
router.register("plans", PlanViewSet, basename="plan")
router.register("taxes", TaxRuleViewSet, basename="tax")
urlpatterns = [path("", include(router.urls))]
