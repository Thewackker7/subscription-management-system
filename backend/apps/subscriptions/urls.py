from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import QuotationTemplateViewSet, QuotationViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register("quotation-templates", QuotationTemplateViewSet, basename="quotation-template")
router.register("quotations", QuotationViewSet, basename="quotation")
router.register("", SubscriptionViewSet, basename="subscription")
urlpatterns = [path("", include(router.urls))]
