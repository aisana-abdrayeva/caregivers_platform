from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.DashboardResource.as_view(), name="dashboard"),
    # User
    path("users/", views.UserListResource.as_view(), name="user_list"),
    path("users/create/", views.UserCreateResource.as_view(), name="user_create"),
    path("users/<int:user_id>/edit/", views.UserUpdateResource.as_view(), name="user_edit"),
    path("users/<int:user_id>/delete/", views.UserDeleteResource.as_view(), name="user_delete"),

    # Member
    path("members/", views.MemberListResource.as_view(), name="member_list"),
    path("members/create/", views.MemberCreateResource.as_view(), name="member_create"),
    path("members/register/", views.MemberRegistrationResource.as_view(), name="member_register"),
    path("members/<int:member_id>/edit/", views.MemberUpdateResource.as_view(), name="member_edit"),
    path("members/<int:member_id>/delete/", views.MemberDeleteResource.as_view(), name="member_delete"),

    # Address
    path("addresses/", views.AddressListResource.as_view(), name="address_list"),
    path("addresses/create/", views.AddressCreateResource.as_view(), name="address_create"),
    path("addresses/<int:pk>/edit/", views.AddressUpdateResource.as_view(), name="address_edit"),
    path("addresses/<int:pk>/delete/", views.AddressDeleteResource.as_view(), name="address_delete"),

    # Caregiver
    path("caregivers/", views.CaregiverListResource.as_view(), name="caregiver_list"),
    path("caregivers/create/", views.CaregiverCreateResource.as_view(), name="caregiver_create"),
    path("caregivers/register/", views.CaregiverRegistrationResource.as_view(), name="caregiver_register"),
    path("caregivers/<int:pk>/edit/", views.CaregiverUpdateResource.as_view(), name="caregiver_edit"),
    path("caregivers/<int:pk>/delete/", views.CaregiverDeleteResource.as_view(), name="caregiver_delete"),
    path("caregivers/<int:pk>/profile/", views.CaregiverProfileResource.as_view(), name="caregiver_profile"),

    # Job
    path("jobs/", views.JobListResource.as_view(), name="job_list"),
    path("jobs/create/", views.JobCreateResource.as_view(), name="job_create"),
    path("jobs/<int:pk>/", views.JobDetailResource.as_view(), name="job_detail"),
    path("jobs/<int:pk>/edit/", views.JobUpdateResource.as_view(), name="job_edit"),
    path("jobs/<int:pk>/delete/", views.JobDeleteResource.as_view(), name="job_delete"),

    # Job Application
    path("applications/", views.JobApplicationListResource.as_view(), name="job_application_list"),
    path("applications/create/", views.JobApplicationCreateResource.as_view(), name="job_application_create"),
    path("applications/<int:pk>/delete/", views.JobApplicationDeleteResource.as_view(), name="job_application_delete"),

    # Appointment
    path("appointments/", views.AppointmentListResource.as_view(), name="appointment_list"),
    path("appointments/create/", views.AppointmentCreateResource.as_view(), name="appointment_create"),
    path("appointments/<int:pk>/edit/", views.AppointmentUpdateResource.as_view(), name="appointment_edit"),
    path("appointments/<int:pk>/delete/", views.AppointmentDeleteResource.as_view(), name="appointment_delete"),
    path("appointments/<int:pk>/status/", views.AppointmentStatusResource.as_view(), name="appointment_status"),
]
