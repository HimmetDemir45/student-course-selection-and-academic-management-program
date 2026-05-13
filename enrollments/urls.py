from django.urls import path

from . import views

app_name = "enrollments"

urlpatterns = [
    path("sections/", views.SectionBrowseView.as_view(), name="browse"),
    path("my/", views.MyEnrollmentsView.as_view(), name="my_enrollments"),
    path("enroll/", views.StudentEnrollView.as_view(), name="enroll"),
    path("<int:pk>/drop/", views.StudentDropEnrollmentView.as_view(), name="drop"),
]
