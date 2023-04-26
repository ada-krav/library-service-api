from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer
)


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
        self.assertIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)

    def test_retrieve_borrowings_if_its_his(self):
        book = sample_book()
        borrowing = sample_borrowing(self.user, book)

        url = detail_url(borrowing.id)
        res = self.client.get(url)

        serializer = BorrowingDetailSerializer(borrowing)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
