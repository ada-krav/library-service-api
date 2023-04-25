from datetime import date

import telebot
from django.conf import settings
from django.contrib.auth import get_user_model

from books.models import Book


bot = telebot.TeleBot(settings.TELEGRAM_TOKEN_API)


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
