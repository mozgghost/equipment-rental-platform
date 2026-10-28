from django.urls import path

from .views import (
    CategoryListView,
    CompanyEquipmentDetailView,
    CompanyEquipmentListCreateView,
    EquipmentDetailView,
    EquipmentListView,
)

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("equipment/", EquipmentListView.as_view(), name="equipment-list"),
    path(
        "equipment/<slug:slug>/",
        EquipmentDetailView.as_view(),
        name="equipment-detail",
    ),
    path(
        "manage/companies/<int:company_id>/equipment/",
        CompanyEquipmentListCreateView.as_view(),
        name="company-equipment-list-create",
    ),
    path(
        "manage/companies/<int:company_id>/equipment/<int:equipment_id>/",
        CompanyEquipmentDetailView.as_view(),
        name="company-equipment-detail",
    ),
]
