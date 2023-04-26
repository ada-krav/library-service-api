from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from django.urls import reverse
from rest_framework import status

CREATE_USER_URL = reverse("users:create")
TOKEN_URL = reverse("users:token_obtain_pair")
MANAGE_USER_URL = reverse("users:manage")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class CreateUserTest(TestCase):

    def test_create_user(self):
        user = get_user_model().objects.create_user(
            "test1@test.com",
            "Usertestpassword",
        )
        self.assertEqual(user.email, "test1@test.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        superuser = get_user_model()
        user = superuser.objects.create_superuser(
            email="adm@adm.com",
            password="test",
        )
        self.assertEqual(user.email, "adm@adm.com")
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_valid_user_success(self):
        payload = {
            "email": "test@test.com",
            "password": "testpass",
            "first_name": "Test",
            "last_name": "User",
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_exists(self):
        payload = {"email": "test@test.com", "password": "testpass"}
        get_user_model().objects.create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class TestUserManage(TestCase):

    def test_retrieve_user_unauthorized(self):
        res = self.client.get(MANAGE_USER_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_password_unauthenticated(self):
        res = self.client.put(MANAGE_USER_URL, {"password": "newpassword"})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_user_authorized(self):
        user = create_user(email="test@test.com", password="testpass")
        self.client = APIClient()
        self.client.force_authenticate(user=user)
        res = self.client.get(MANAGE_USER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], user.email)

    def test_can_change_info_for_authorized(self):
        user = create_user(email="czar1937@urk.net", password="Testpass123")
        self.client = APIClient()
        self.client.force_authenticate(user=user)
        res = self.client.put(
            MANAGE_USER_URL, {
                "email": "life4beer27@gmail.com",
                "first_name": "New",
                "last_name": "Name",
                "password": "Testpass123",
            }
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["first_name"], "New")
        self.assertEqual(res.data["last_name"], "Name")


class TokenTest(TestCase):

    def test_create_token_invalid_credentials(self):
        create_user(email="test@test.com", password="testpass")
        payload = {"email": "123@mail.com", "password": "wrong"}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("access", res.data)
        self.assertNotIn("refresh", res.data)

    def test_create_token_for_user(self):
        payload = {"email": "test@test.com", "password": "testpass"}
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
