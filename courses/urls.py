from django.urls import path

from . import views

app_name = "courses"

urlpatterns = [
    path("elective-pools/", views.ElectivePoolListView.as_view(), name="electivepool_list"),
    path("elective-pools/create/", views.ElectivePoolCreateView.as_view(), name="electivepool_create"),
    path("elective-pools/<int:pk>/edit/", views.ElectivePoolUpdateView.as_view(), name="electivepool_update"),
    path("elective-pools/<int:pk>/delete/", views.ElectivePoolDeleteView.as_view(), name="electivepool_delete"),
    path("derslikler/", views.ClassroomListView.as_view(), name="classroom_list"),
    path("derslikler/ekle/", views.ClassroomCreateView.as_view(), name="classroom_create"),
    path("derslikler/<int:pk>/duzenle/", views.ClassroomUpdateView.as_view(), name="classroom_update"),
    path("derslikler/<int:pk>/sil/", views.ClassroomDeleteView.as_view(), name="classroom_delete"),
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
    # Önkoşul yönetimi
    path("<int:pk>/prerequisites/", views.CoursePrerequisiteView.as_view(), name="course_prerequisites"),
    path("prerequisites/<int:link_pk>/delete/", views.prerequisite_delete, name="prerequisite_delete"),
    # Ders detay
    path("<int:pk>/", views.CourseDetailView.as_view(), name="course_detail"),
]
