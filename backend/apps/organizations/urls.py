from django.urls import path

from .views import (
    CompanyDetailView,
    CompanyListCreateView,
    CompanyMembershipDetailView,
    CompanyMembershipListCreateView,
)

urlpatterns = [
    path("", CompanyListCreateView.as_view(), name="company-list-create"),
    path("<int:company_id>/", CompanyDetailView.as_view(), name="company-detail"),
    path(
        "<int:company_id>/members/",
        CompanyMembershipListCreateView.as_view(),
        name="company-members",
    ),
    path(
        "<int:company_id>/members/<int:membership_id>/",
        CompanyMembershipDetailView.as_view(),
        name="company-member-detail",
    ),
]
