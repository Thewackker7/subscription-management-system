from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.permissions import IsAdminOrStaff
from .models import Quotation, QuotationTemplate, Subscription
from .serializers import (QuotationConversionSerializer, QuotationSerializer, QuotationTemplateSerializer,
                          RenewSerializer, SubscriptionSerializer, SubscriptionTransitionSerializer)
from .services import convert_quotation_to_subscription


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        queryset = Subscription.objects.select_related("customer", "plan").prefetch_related("lines__product", "lines__variant", "lines__tax_rule")
        if self.request.user.role == User.Role.CUSTOMER:
            return queryset.filter(customer=self.request.user)
        return queryset

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [IsAuthenticated()]
        return [IsAdminOrStaff()]

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        subscription = self.get_object()
        serializer = SubscriptionTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            subscription.transition(serializer.validated_data["status"])
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict)
        return Response(self.get_serializer(subscription).data)

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        subscription = self.get_object()
        try:
            subscription.pause()
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict)
        return Response(self.get_serializer(subscription).data)

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        subscription = self.get_object()
        try:
            subscription.resume()
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict)
        return Response(self.get_serializer(subscription).data)

    @action(detail=True, methods=["post"])
    def renew(self, request, pk=None):
        subscription = self.get_object()
        serializer = RenewSerializer(data=request.data, context={"subscription": subscription})
        serializer.is_valid(raise_exception=True)
        try:
            subscription.renew(serializer.validated_data["expiry_date"])
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict)
        return Response(self.get_serializer(subscription).data)


class QuotationTemplateViewSet(viewsets.ModelViewSet):
    queryset = QuotationTemplate.objects.select_related("plan").prefetch_related("lines__product", "lines__variant", "lines__tax_rule")
    serializer_class = QuotationTemplateSerializer
    permission_classes = [IsAdminOrStaff]


class QuotationViewSet(viewsets.ModelViewSet):
    serializer_class = QuotationSerializer
    permission_classes = [IsAdminOrStaff]
    queryset = Quotation.objects.select_related("customer", "plan", "converted_subscription").prefetch_related("lines__product", "lines__variant", "lines__tax_rule")

    @action(detail=True, methods=["post"])
    def convert(self, request, pk=None):
        serializer = QuotationConversionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            subscription = convert_quotation_to_subscription(quotation_id=pk, **serializer.validated_data)
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict)
        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)
