from django.urls import path, include
from rest_framework.routers import DefaultRouter

from borrowings.views import BorrowingViewSet

router = DefaultRouter()
router.register("", BorrowingViewSet)

urlpatterns = [
    path("", include(router.urls)),
    # path(
    #     "<int:borrowing_id>/return/",
    #     ReturnBookView.as_view(),
    #     name="return_book",
    # ),
]

app_name = "borrowings"
