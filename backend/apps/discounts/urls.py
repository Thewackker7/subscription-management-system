from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import DiscountRuleViewSet

router = DefaultRouter()
router.register("", DiscountRuleViewSet, basename="discount")
urlpatterns = [path("", include(router.urls))]
