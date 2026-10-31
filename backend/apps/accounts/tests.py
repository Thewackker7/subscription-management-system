from django.core import mail
from django.test import override_settings
from django.urls import reverse
from urllib.parse import parse_qs, urlparse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User


class AuthenticationAndRoleTests(APITestCase):
    def test_health_is_public(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})

    def test_registration_normalizes_email_and_rejects_weak_password(self):
        response = self.client.post(reverse("register"), {"email": "Person@Example.COM", "password": "weakpass"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(reverse("register"), {"email": "Person@Example.COM", "password": "StrongPass!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get().email, "person@example.com")

        duplicate = self.client.post(reverse("register"), {"email": "PERSON@example.com", "password": "StrongPass!"}, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_admin_can_create_staff(self):
        staff_url = reverse("staff-create")
        customer = User.objects.create_user("customer@example.com", "Customer1!")
        self.client.force_authenticate(customer)
        forbidden = self.client.post(staff_url, {"email": "staff@example.com", "password": "StaffPass1!"}, format="json")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        admin = User.objects.create_user("admin@example.com", "AdminPass1!", role=User.Role.ADMIN)
        self.client.force_authenticate(admin)
        created = self.client.post(staff_url, {"email": "staff@example.com", "password": "StaffPass1!"}, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(email="staff@example.com").role, User.Role.STAFF)

    def test_login_returns_jwt_and_role_aware_user_summary(self):
        User.objects.create_user("admin@example.com", "AdminPass1!", role=User.Role.ADMIN)
        response = self.client.post(reverse("login"), {"email": "admin@example.com", "password": "AdminPass1!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["user"], {"id": 1, "email": "admin@example.com", "role": "ADMIN"})

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", PASSWORD_RESET_FRONTEND_URL="http://frontend/reset")
    def test_password_reset_is_non_enumerating_and_single_use(self):
        user = User.objects.create_user("customer@example.com", "Customer1!")
        known = self.client.post(reverse("password-reset-request"), {"email": user.email}, format="json")
        unknown = self.client.post(reverse("password-reset-request"), {"email": "none@example.com"}, format="json")
        self.assertEqual(known.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(known.data, unknown.data)
        self.assertEqual(len(mail.outbox), 1)
        query = parse_qs(urlparse(mail.outbox[0].body.split()[-1]).query)
        confirmation = self.client.post(reverse("password-reset-confirm"), {"uid": query["uid"][0], "token": query["token"][0], "password": "NewPassword1!"}, format="json")
        self.assertEqual(confirmation.status_code, status.HTTP_200_OK)
        repeat = self.client.post(reverse("password-reset-confirm"), {"uid": query["uid"][0], "token": query["token"][0], "password": "OtherPassword1!"}, format="json")
        self.assertEqual(repeat.status_code, status.HTTP_400_BAD_REQUEST)
