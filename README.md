# Library Service API

This application is an online library that allows users to view a list of books. 
Users can also borrow books, return them, and pay for their rental.

## Installation

1. Copy .env.sample -> .env and populate with all required data
2. docker-compose up --build
3. Create admin user & Create schedule for running sync in DB

## Technologies

1. Python
2. Django
3. Django REST Framework
4. Celery
5. Redis
6. Telebot
7. Stripe