from datetime import date

from celery import shared_task
import telebot
from django.conf import settings
from django.contrib.auth import get_user_model

from books.models import Book
from borrowings.models import Borrowing


bot = telebot.TeleBot(settings.TELEGRAM_TOKEN_API)


@shared_task
def send_to_char_borrowing_book(
        book_id: int,
        user_id,
        expected_return_date: date,
) -> None:
    book = Book.objects.get(id=book_id)
    user = get_user_model().objects.get(id=user_id)
    message = (
       f"{user.first_name} {user.last_name} borrowed {book.title} "
       f"expected return date: {expected_return_date}. "
       f"Price per day: {book.daily_fee}.")
    bot.send_message(settings.TELEGRAM_CHAT_ID, message)


@shared_task
def filter_borrowing_which_are_overdue() -> None:
    borrowings = Borrowing.objects.filter(
        actual_return_date__isnull=True,
        expected_return_date__lt=date.today()
    ).select_related("user", "book")
    message = ""
    if borrowings:
        for borrowing in borrowings:
            days_overdue = date.today() - borrowing.expected_return_date
            int_days_overdue = int(str(days_overdue).split()[0])
            message_days = f"{int_days_overdue} days" if int_days_overdue > 1 else f"{int_days_overdue} day"
            message += (
                f"{borrowing.user.first_name} {borrowing.user.last_name} "
                f"overdue the book {borrowing.book.title} for "
                f"{message_days}\n"
            )
    else:
        message = "No borrowings overdue today!"

    bot.send_message(settings.TELEGRAM_CHAT_ID, message)
