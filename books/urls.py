from django.urls import path, include
from rest_framework import routers

from .views import BookViewSets


router = routers.DefaultRouter()
router.register("", BookViewSets)

urlpatterns = [
    path("", include(router.urls))
]

app_name = "books"
