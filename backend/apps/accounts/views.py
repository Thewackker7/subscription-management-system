import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .permissions import IsAdminRole
from .models import User
from .serializers import (LoginSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer,
                          StaffCreateSerializer, UserCreateSerializer)

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({"status": "ok"})


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserCreateSerializer


class StaffCreateView(generics.CreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = StaffCreateSerializer


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = User.objects.normalize_email(serializer.validated_data["email"]).lower()
        user = User.objects.filter(email=email, is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.PASSWORD_RESET_FRONTEND_URL}?{urlencode({'uid': uid, 'token': token})}"
            try:
                send_mail("Password reset", f"Use this link to reset your password: {reset_url}", settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
            except Exception:
                # Preserve account privacy; operators receive the actionable server log.
                logger.exception("Password reset email delivery failed")
        return Response({"detail": "If the email is registered, password reset instructions have been sent."}, status=status.HTTP_202_ACCEPTED)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been reset."})
