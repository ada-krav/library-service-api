from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
)
from payments.models import Payment


BORROWING_URL = reverse("borrowings:borrowing-list")


def detail_url(borrowing_id):
    return reverse("borrowings:borrowing-detail", args=[borrowing_id])


def sample_book(**params):
    defaults = {
        "title": "Sample book",
        "author": "Sample author",
        "cover": "HD",
        "inventory": 1,
        "daily_fee": 2.00,
    }
    defaults.update(params)

    return Book.objects.create(**defaults)


def sample_borrowing(user, book, **params):
    defaults = {
        "expected_return_date": "2023-04-30",
        "actual_return_date": None,
        "user": user,
        "book": book
    }
    defaults.update(params)

    return Borrowing.objects.create(**defaults)


class UnauthenticatedBorrowingApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(BORROWING_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_borrowings(self):
        book_1 = sample_book()
        book_2 = sample_book(inventory=2)

        user_1 = get_user_model().objects.create_user(
            "ts@ts.com",
            "password"
        )

        bor1 = sample_borrowing(book=book_1, user=self.user)
        bor2 = sample_borrowing(book=book_2, user=self.user)
        bor3 = sample_borrowing(book=book_2, user=user_1)

        res = self.client.get(BORROWING_URL)

        serializer_1 = BorrowingListSerializer(bor1)
        serializer_2 = BorrowingListSerializer(bor2)
        serializer_3 = BorrowingListSerializer(bor3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
        self.assertNotIn(serializer_3.data, res.data)

    def test_list_filter_by_is_active_true(self):
        book = sample_book(inventory=2)
        bor1 = sample_borrowing(
            book=book,
            user=self.user,
            actual_return_date="2023-06-01"
        )
        bor2 = sample_borrowing(book=book, user=self.user)

        res = self.client.get(BORROWING_URL, {"is_active": True})

        serializer_1 = BorrowingListSerializer(bor1)
        serializer_2 = BorrowingListSerializer(bor2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)

    def test_list_filter_by_is_active_false(self):
        book = sample_book(inventory=3)
        borrowing1 = sample_borrowing(
            book=book,
            user=self.user,
            actual_return_date="2023-06-01"
        )
        borrowing2 = sample_borrowing(book=book, user=self.user)

        res = self.client.get(BORROWING_URL, {"is_active": False})

        serializer_1 = BorrowingListSerializer(borrowing1)
        serializer_2 = BorrowingListSerializer(borrowing2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_1.data, res.data)
        self.assertNotIn(serializer_2.data, res.data)

    def test_retrieve_borrowings_if_its_his(self):
        book = sample_book()
        borrowing = sample_borrowing(self.user, book)

        url = detail_url(borrowing.id)
        res = self.client.get(url)

        serializer = BorrowingDetailSerializer(borrowing)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_user_cant_retrieve_not_his_borrowings(self):
        book = sample_book()
        user1 = get_user_model().objects.create_user(
            "testuser@user.com",
            "testpass"
        )
        borrowing = sample_borrowing(user1, book)

        url = detail_url(borrowing.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cant_use_put(self):
        book = sample_book()
        borrowing = sample_borrowing(self.user, book)
        url = detail_url(borrowing.id)
        res = self.client.put(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_user_cant_use_delete(self):
        book = sample_book()
        borrowing = sample_borrowing(self.user, book)
        url = detail_url(borrowing.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_user_create_borrowings(self):
        book = sample_book(inventory=5)

        payload = {
            "book": book.id,
            "expected_return_date": "2023-06-28",
        }
        with patch("notification.tasks.send_to_chat_borrowing_book.delay") as mock_task:
            res = self.client.post(BORROWING_URL, payload)

            payment = Payment.objects.first()
            book = Book.objects.get(id=book.id)

            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            self.assertEqual(mock_task.called, True)
            self.assertEqual(res.data["payments"][0]["stripe_session_url"], payment.stripe_session_url)
            self.assertEqual(book.inventory, 4)

    def test_return_book(self):
        book = sample_book(inventory=4)

        borrowing = sample_borrowing(self.user, book)

        res = self.client.post(reverse("borrowings:borrowing-return-book", args=[borrowing.id]))

        book = Book.objects.get(id=book.id)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(book.inventory, 5)


class AdminBorrowingTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            "admin@admin.com",
            "testpass",
        )
        self.client.force_authenticate(self.admin)

        self.user_1 = get_user_model().objects.create_user(
            "ts@ts.com",
            "password"
        )

        self.user_2 = get_user_model().objects.create_user(
            "ts2@ts.com",
            "password"
        )

        self.user_3 = get_user_model().objects.create_user(
            "ts3@ts.com",
            "password"
        )

    def test_list_borrowings(self):
        book_1 = sample_book()
        book_2 = sample_book(inventory=2)

        sample_borrowing(book=book_1, user=self.user_1)
        sample_borrowing(book=book_2, user=self.user_2)
        sample_borrowing(book=book_2, user=self.user_3)

        res = self.client.get(BORROWING_URL)

        borrowings = Borrowing.objects.order_by("id")

        serializer = BorrowingListSerializer(borrowings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_list_borrowings_filter_by_is_active(self):
        book_1 = sample_book()
        book_2 = sample_book(inventory=2)

        borrowing1 = sample_borrowing(book=book_1, user=self.user_1)
        borrowing2 = sample_borrowing(book=book_2, user=self.user_2)
        borrowing3 = sample_borrowing(
            book=book_2,
            user=self.user_3,
            actual_return_date="2023-06-20"
        )

        res = self.client.get(BORROWING_URL, {"is_active": True})

        serializer_1 = BorrowingListSerializer(borrowing1)
        serializer_2 = BorrowingListSerializer(borrowing2)
        serializer_3 = BorrowingListSerializer(borrowing3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
        self.assertNotIn(serializer_3.data, res.data)

    def test_list_borrowings_filter_by_user_id(self):
        book_1 = sample_book()
        book_2 = sample_book(inventory=2)

        borrowing1 = sample_borrowing(book=book_1, user=self.user_1)
        borrowing2 = sample_borrowing(book=book_2, user=self.user_2)
        borrowing3 = sample_borrowing(
            book=book_2,
            user=self.user_3,
            actual_return_date="2023-06-20"
        )

        res = self.client.get(BORROWING_URL, {"user_id": self.user_1.id})

        serializer_1 = BorrowingListSerializer(borrowing1)
        serializer_2 = BorrowingListSerializer(borrowing2)
        serializer_3 = BorrowingListSerializer(borrowing3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_1.data, res.data)
        self.assertNotIn(serializer_2.data, res.data)
        self.assertNotIn(serializer_3.data, res.data)

    def test_admin_retrieve_any_borrowing(self):
        book = sample_book()
        borrowing = sample_borrowing(self.user_1, book)

        url = detail_url(borrowing.id)
        res = self.client.get(url)

        serializer = BorrowingDetailSerializer(borrowing)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
