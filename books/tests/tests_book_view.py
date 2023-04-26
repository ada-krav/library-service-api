from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from books.models import Book
from django.urls import reverse

BOOK_URL = reverse("books:book-list")
BOOK_URL_DETAIL = reverse("books:book-detail", args=[1])


def sample_book(**params):
    defaults = {
        "title": "Sample book",
        "author": "Sample author",
        "cover": "HARD",
        "inventory": 10,
        "daily_fee": 15.99,
    }
    defaults.update(params)

    return Book.objects.create(**defaults)


class UnauthenticatedBookApiTest(TestCase):

    def setUp(self):
        self.book1 = sample_book(
            title="Book 1",
            author="Author 1",
            cover=Book.CoverType.HARD,
            inventory=10,
            daily_fee=1.99,
        )
        self.book2 = sample_book(
            title="Book 2",
            author="Author 2",
            cover=Book.CoverType.SOFT,
            inventory=5,
            daily_fee=0.99,
        )
        self.book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "cover": "ST",
            "inventory": 5,
            "daily_fee": 2.99,
        }

    def test_unauthenticated_user_can_list_books(self):
        url = BOOK_URL

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        self.assertEqual(response.data[0]["title"], self.book1.title)
        self.assertEqual(response.data[0]["author"], self.book1.author)

        self.assertEqual(response.data[1]["title"], self.book2.title)
        self.assertEqual(response.data[1]["author"], self.book2.author)

    def test_unauthorized_user_cannot_create_book(self):
        self.url = BOOK_URL
        response = self.client.post(self.url, self.book_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cannot_update_book(self):
        self.url = BOOK_URL_DETAIL
        response = self.client.put(self.url, self.book_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cannot_delete_book(self):
        self.url = BOOK_URL_DETAIL
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_can_retrieve_book(self):
        self.url = BOOK_URL_DETAIL
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AuthenticatedBookTestCase(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "test1@test.com",
            "Usertestpassword",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.book1 = sample_book(
            title="Book 1",
            author="Test",
            cover=Book.CoverType.HARD,
            inventory=10,
            daily_fee=1.99,
        )
        self.book2 = sample_book(
            title="Book 2",
            author="Test2",
            cover=Book.CoverType.SOFT,
            inventory=5,
            daily_fee=0.99,
        )
        self.book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "cover": "ST",
            "inventory": 5,
            "daily_fee": 2.99,
        }
        self.book_url = BOOK_URL
        self.book_detail_url = BOOK_URL_DETAIL

    def test_authenticated_user_cannot_create_book(self):
        response = self.client.post(
            self.book_url, self.book_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_update_book(self):
        response = self.client.put(
            self.book_detail_url, self.book_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_delete_book(self):
        response = self.client.delete(self.book_detail_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_retrieve_book(self):
        response = self.client.get(self.book_detail_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminBookApiTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="adm@adm.com",
            password="Testadmin",
            is_staff=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.book1 = sample_book(
            title="Book 1",
            author="Test",
            cover=Book.CoverType.HARD,
            inventory=10,
            daily_fee=1.99,
        )
        self.book2 = sample_book(
            title="Book 2",
            author="Test",
            cover=Book.CoverType.SOFT,
            inventory=5,
            daily_fee=0.99,
        )
        self.book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "cover": "ST",
            "inventory": 5,
            "daily_fee": 2.99,
        }

    def test_admin_user_can_create_book(self):
        response = self.client.post(BOOK_URL, self.book_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_user_can_update_book(self):
        url = BOOK_URL_DETAIL
        response = self.client.put(url, self.book_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_user_can_delete_book(self):
        url = BOOK_URL_DETAIL
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
