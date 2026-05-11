from django.urls import path

from . import views

app_name = "courses"

urlpatterns = [
    path("", views.CourseListView.as_view(), name="course_list"),
    path("create/", views.CourseCreateView.as_view(), name="course_create"),
    path("<int:pk>/edit/", views.CourseUpdateView.as_view(), name="course_update"),
    path("<int:pk>/delete/", views.CourseDeleteView.as_view(), name="course_delete"),
    path("<int:pk>/toggle/", views.course_toggle_active, name="course_toggle_active"),
    path("offerings/", views.CourseOfferingListView.as_view(), name="offering_list"),
    path("offerings/create/", views.CourseOfferingCreateView.as_view(), name="offering_create"),
    path("offerings/<int:pk>/edit/", views.CourseOfferingUpdateView.as_view(), name="offering_update"),
    path("offerings/<int:pk>/delete/", views.CourseOfferingDeleteView.as_view(), name="offering_delete"),
    path("offerings/<int:pk>/toggle/", views.offering_toggle_active, name="offering_toggle_active"),
]
