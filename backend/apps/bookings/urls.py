from django.urls import path
from .views import BookingDetailView, BookingListCreateView
urlpatterns = [path("", BookingListCreateView.as_view()), path("<int:booking_id>/", BookingDetailView.as_view())]
