from types import SimpleNamespace

from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from .models import (
    Address,
    Appointment,
    Caregiver,
    ContactRequest,
    Job,
    JobApplication,
    JobDetail,
    Member,
    User,
)

CARE_TYPES = (
    ("babysitter", "Babysitter"),
    ("caregiver for elderly", "Caregiver for elderly"),
    ("playmate for children", "Playmate for children"),
)

EMPTY_JOB_DETAIL = SimpleNamespace(
    care_recipient_age="",
    preferred_time_slots="",
    service_frequency="",
    additional_notes="",
)

APPOINTMENT_STATUS_OPTIONS = ("pending", "accepted", "declined")


def _clean_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class DashboardResource(View):
    template_name = "dashboard.html"

    def get(self, request):
        return render(request, self.template_name)


# --------------------
# USER RESOURCES
# --------------------
class UserListResource(View):
    template_name = "user_list.html"

    def get(self, request):
        query = request.GET.get("q")
        users = User.objects.all()
        if query:
            users = users.filter(
                Q(given_name__icontains=query)
                | Q(surname__icontains=query)
                | Q(email__icontains=query)
            )
        return render(request, self.template_name, {"users": users, "query": query or ""})


class UserCreateResource(View):
    template_name = "user_form.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get("email")
        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return redirect("user_create")
        User.objects.create(
            email=email,
            given_name=request.POST.get("given_name"),
            surname=request.POST.get("surname"),
            city=request.POST.get("city"),
            phone_number=request.POST.get("phone_number"),
            profile_description=request.POST.get("profile_description"),
            password=request.POST.get("password"),
        )
        messages.success(request, "User created successfully.")
        return redirect("user_list")


class UserUpdateResource(View):
    template_name = "user_form.html"

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        return render(request, self.template_name, {"user": user})

    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        user.email = request.POST.get("email")
        user.given_name = request.POST.get("given_name")
        user.surname = request.POST.get("surname")
        user.city = request.POST.get("city")
        user.phone_number = request.POST.get("phone_number")
        user.profile_description = request.POST.get("profile_description")
        user.password = request.POST.get("password")
        user.save()
        messages.success(request, "User updated successfully.")
        return redirect("user_list")


class UserDeleteResource(View):
    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        try:
            user.delete()
            messages.success(request, "User deleted successfully.")
        except ProtectedError:
            messages.error(
                request, "Cannot delete user; related caregiver/member exists."
            )
        return redirect("user_list")


# --------------------
# MEMBER RESOURCES
# --------------------
class MemberListResource(View):
    template_name = "member_list.html"

    def get(self, request):
        members = Member.objects.select_related("member_user").all()
        return render(request, self.template_name, {"members": members})


class MemberCreateResource(View):
    template_name = "member_form.html"

    def get(self, request):
        users = User.objects.exclude(member__isnull=False)
        return render(request, self.template_name, {"users": users})

    def post(self, request):
        user_id = request.POST.get("user_id")
        user = get_object_or_404(User, pk=user_id)
        if Member.objects.filter(member_user=user).exists():
            messages.error(request, "This user is already a member.")
            return redirect("member_create")
        Member.objects.create(
            member_user=user,
            house_rules=request.POST.get("house_rules"),
            dependent_description=request.POST.get("dependent_description"),
        )
        messages.success(request, "Member created successfully.")
        return redirect("member_list")


class MemberUpdateResource(View):
    template_name = "member_form.html"

    def get(self, request, member_id):
        member = get_object_or_404(Member, pk=member_id)
        users = User.objects.all()
        return render(
            request, self.template_name, {"member": member, "users": users}
        )

    def post(self, request, member_id):
        member = get_object_or_404(Member, pk=member_id)
        member.house_rules = request.POST.get("house_rules")
        member.dependent_description = request.POST.get("dependent_description")
        member.save()
        messages.success(request, "Member updated successfully.")
        return redirect("member_list")


class MemberDeleteResource(View):
    def post(self, request, member_id):
        member = get_object_or_404(Member, pk=member_id)
        try:
            member.delete()
            messages.success(request, "Member deleted successfully.")
        except ProtectedError:
            messages.error(
                request,
                "Cannot delete member; related address/job/appointment exists.",
            )
        return redirect("member_list")


class MemberRegistrationResource(View):
    template_name = "member_registration_form.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get("email")
        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return redirect("member_register")
        user = User.objects.create(
            email=email,
            given_name=request.POST.get("given_name"),
            surname=request.POST.get("surname"),
            city=request.POST.get("city"),
            phone_number=request.POST.get("phone_number"),
            profile_description=request.POST.get("dependent_description"),
            password=request.POST.get("password"),
        )
        member = Member.objects.create(
            member_user=user,
            house_rules=request.POST.get("house_rules"),
            dependent_description=request.POST.get("dependent_description"),
        )
        Address.objects.update_or_create(
            member=member,
            defaults={
                "house_number": request.POST.get("house_number"),
                "street": request.POST.get("street"),
                "town": request.POST.get("city"),
            },
        )
        messages.success(request, "Member registered successfully.")
        return redirect("member_list")


# --------------------
# ADDRESS RESOURCES
# --------------------
class AddressListResource(View):
    template_name = "address_list.html"

    def get(self, request):
        addresses = Address.objects.select_related("member", "member__member_user")
        return render(request, self.template_name, {"addresses": addresses})


class AddressCreateResource(View):
    template_name = "address_form.html"

    def get(self, request):
        members = Member.objects.exclude(address__isnull=False)
        return render(request, self.template_name, {"members": members})

    def post(self, request):
        member = get_object_or_404(Member, pk=request.POST.get("member_id"))
        if hasattr(member, "address"):
            messages.error(request, "This member already has an address.")
            return redirect("address_create")
        Address.objects.create(
            member=member,
            house_number=request.POST.get("house_number"),
            street=request.POST.get("street"),
            town=request.POST.get("town"),
        )
        messages.success(request, "Address created successfully.")
        return redirect("address_list")


class AddressUpdateResource(View):
    template_name = "address_form.html"

    def get(self, request, pk):
        address = get_object_or_404(Address, pk=pk)
        members = Member.objects.all()
        return render(
            request, self.template_name, {"address": address, "members": members}
        )

    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk)
        address.house_number = request.POST.get("house_number")
        address.street = request.POST.get("street")
        address.town = request.POST.get("town")
        address.save()
        messages.success(request, "Address updated successfully.")
        return redirect("address_list")


class AddressDeleteResource(View):
    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk)
        address.delete()
        messages.success(request, "Address deleted successfully.")
        return redirect("address_list")


# --------------------
# CAREGIVER RESOURCES
# --------------------
class CaregiverListResource(View):
    template_name = "caregiver_list.html"

    def get(self, request):
        caregiving_type = request.GET.get("caregiving_type")
        city = request.GET.get("city")
        min_price = request.GET.get("min_price")
        max_price = request.GET.get("max_price")

        caregivers = Caregiver.objects.select_related("caregiver_user").all()

        if caregiving_type:
            caregivers = caregivers.filter(
                caregiving_type__iexact=caregiving_type.strip()
            )
        if city:
            caregivers = caregivers.filter(
                caregiver_user__city__icontains=city.strip()
            )
        if min_price:
            caregivers = caregivers.filter(hourly_rate__gte=min_price)
        if max_price:
            caregivers = caregivers.filter(hourly_rate__lte=max_price)

        context = {
            "caregivers": caregivers,
            "care_types": CARE_TYPES,
            "selected_type": caregiving_type or "",
            "city_query": city or "",
            "min_price": min_price or "",
            "max_price": max_price or "",
        }
        return render(request, self.template_name, context)


class CaregiverCreateResource(View):
    template_name = "caregiver_form.html"

    def get(self, request):
        users = User.objects.exclude(caregiver__isnull=False)
        return render(request, self.template_name, {"users": users, "care_types": CARE_TYPES})

    def post(self, request):
        user = get_object_or_404(User, pk=request.POST.get("user_id"))
        if Caregiver.objects.filter(caregiver_user=user).exists():
            messages.error(request, "This user is already a caregiver.")
            return redirect("caregiver_create")
        Caregiver.objects.create(
            caregiver_user=user,
            photo=request.FILES.get("photo"),
            gender=request.POST.get("gender"),
            caregiving_type=request.POST.get("caregiving_type"),
            hourly_rate=request.POST.get("hourly_rate"),
        )
        messages.success(request, "Caregiver created successfully.")
        return redirect("caregiver_list")


class CaregiverUpdateResource(View):
    template_name = "caregiver_form.html"

    def get(self, request, pk):
        caregiver = get_object_or_404(Caregiver, pk=pk)
        users = User.objects.all()
        return render(
            request,
            self.template_name,
            {"caregiver": caregiver, "users": users, "care_types": CARE_TYPES},
        )

    def post(self, request, pk):
        caregiver = get_object_or_404(Caregiver, pk=pk)
        caregiver.gender = request.POST.get("gender")
        caregiver.caregiving_type = request.POST.get("caregiving_type")
        caregiver.hourly_rate = request.POST.get("hourly_rate")
        if request.FILES.get("photo"):
            caregiver.photo = request.FILES.get("photo")
        caregiver.save()
        messages.success(request, "Caregiver updated successfully.")
        return redirect("caregiver_list")


class CaregiverDeleteResource(View):
    def post(self, request, pk):
        caregiver = get_object_or_404(Caregiver, pk=pk)
        try:
            caregiver.delete()
            messages.success(request, "Caregiver deleted successfully.")
        except ProtectedError:
            messages.error(
                request,
                "Cannot delete caregiver; related appointment/job_application exists.",
            )
        return redirect("caregiver_list")


class CaregiverRegistrationResource(View):
    template_name = "caregiver_registration_form.html"

    def get(self, request):
        return render(request, self.template_name, {"care_types": CARE_TYPES})

    def post(self, request):
        email = request.POST.get("email")
        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return redirect("caregiver_register")
        user = User.objects.create(
            email=email,
            given_name=request.POST.get("given_name"),
            surname=request.POST.get("surname"),
            city=request.POST.get("city"),
            phone_number=request.POST.get("phone_number"),
            profile_description=request.POST.get("biography"),
            password=request.POST.get("password"),
        )
        Caregiver.objects.create(
            caregiver_user=user,
            photo=request.FILES.get("photo"),
            gender=request.POST.get("gender"),
            caregiving_type=request.POST.get("caregiving_type"),
            hourly_rate=request.POST.get("hourly_rate"),
        )
        messages.success(request, "Caregiver registered successfully.")
        return redirect("caregiver_list")


class CaregiverProfileResource(View):
    template_name = "caregiver_profile.html"

    def get(self, request, pk):
        caregiver = get_object_or_404(Caregiver, pk=pk)
        members = Member.objects.select_related("member_user")
        requests_qs = ContactRequest.objects.filter(caregiver=caregiver).select_related(
            "member", "member__member_user"
        )
        context = {
            "caregiver": caregiver,
            "members": members,
            "contact_requests": requests_qs.order_by("-created_at"),
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        caregiver = get_object_or_404(Caregiver, pk=pk)
        member = get_object_or_404(Member, pk=request.POST.get("member_id"))
        ContactRequest.objects.create(
            member=member,
            caregiver=caregiver,
            message=request.POST.get("message"),
            allow_caregiver_initiate=bool(request.POST.get("allow_contact")),
        )
        messages.success(request, "Message sent to caregiver.")
        return redirect("caregiver_profile", pk=pk)


# --------------------
# JOB RESOURCES
# --------------------
class JobListResource(View):
    template_name = "job_list.html"

    def get(self, request):
        caregiving_type = request.GET.get("caregiving_type")
        city = request.GET.get("city")
        frequency = request.GET.get("service_frequency")

        jobs = Job.objects.select_related("member", "member__member_user").prefetch_related("detail")

        if caregiving_type:
            jobs = jobs.filter(required_caregiving_type__iexact=caregiving_type)
        if city:
            jobs = jobs.filter(member__member_user__city__icontains=city.strip())
        if frequency:
            jobs = jobs.filter(
                detail__service_frequency__icontains=frequency.strip()
            )

        jobs = list(jobs)
        for job in jobs:
            job.detail_data = getattr(job, "detail", None)

        context = {
            "jobs": jobs,
            "care_types": CARE_TYPES,
            "selected_type": caregiving_type or "",
            "city_query": city or "",
            "frequency_query": frequency or "",
        }
        return render(request, self.template_name, context)


class JobCreateResource(View):
    template_name = "job_form.html"

    def get(self, request):
        members = Member.objects.select_related("member_user")
        return render(
            request,
            self.template_name,
            {
                "members": members,
                "care_types": CARE_TYPES,
                "detail": EMPTY_JOB_DETAIL,
                "job": None,
            },
        )

    def post(self, request):
        member = get_object_or_404(Member, pk=request.POST.get("member_id"))
        required_type = request.POST.get("required_caregiving_type")

        if Job.objects.filter(member=member, required_caregiving_type=required_type).exists():
            messages.error(request, "A similar job already exists for this member.")
            return redirect("job_create")

        job = Job.objects.create(
            member=member,
            required_caregiving_type=required_type,
            other_requirements=request.POST.get("other_requirements"),
            date_posted=timezone.now().date(),
        )

        JobDetail.objects.update_or_create(
            job=job,
            defaults={
                "care_recipient_age": _clean_int(request.POST.get("care_recipient_age")),
                "preferred_time_slots": request.POST.get("preferred_time_slots"),
                "service_frequency": request.POST.get("service_frequency"),
                "additional_notes": request.POST.get("additional_notes"),
            },
        )
        messages.success(request, "Job created successfully.")
        return redirect("job_list")


class JobUpdateResource(View):
    template_name = "job_form.html"

    def get(self, request, pk):
        job = get_object_or_404(Job, pk=pk)
        members = Member.objects.select_related("member_user")
        detail = getattr(job, "detail", None)
        return render(
            request,
            self.template_name,
            {
                "job": job,
                "members": members,
                "detail": detail or EMPTY_JOB_DETAIL,
                "care_types": CARE_TYPES,
            },
        )

    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk)
        job.member = get_object_or_404(Member, pk=request.POST.get("member_id"))
        job.required_caregiving_type = request.POST.get("required_caregiving_type")
        job.other_requirements = request.POST.get("other_requirements")
        job.save()

        JobDetail.objects.update_or_create(
            job=job,
            defaults={
                "care_recipient_age": _clean_int(request.POST.get("care_recipient_age")),
                "preferred_time_slots": request.POST.get("preferred_time_slots"),
                "service_frequency": request.POST.get("service_frequency"),
                "additional_notes": request.POST.get("additional_notes"),
            },
        )
        messages.success(request, "Job updated successfully.")
        return redirect("job_list")


class JobDeleteResource(View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk)
        try:
            job.delete()
            messages.success(request, "Job deleted successfully.")
        except ProtectedError:
            messages.error(
                request, "Cannot delete job; related job_application exists."
            )
        return redirect("job_list")


class JobDetailResource(View):
    template_name = "job_detail.html"

    def get(self, request, pk):
        job = get_object_or_404(
            Job.objects.select_related("member", "member__member_user"), pk=pk
        )
        detail = getattr(job, "detail", None)
        applications = JobApplication.objects.filter(job=job).select_related(
            "caregiver", "caregiver__caregiver_user"
        )
        caregivers = Caregiver.objects.select_related("caregiver_user")
        return render(
            request,
            self.template_name,
            {
                "job": job,
                "detail": detail,
                "applications": applications,
                "caregivers": caregivers,
            },
        )


# --------------------
# JOB APPLICATION RESOURCES
# --------------------
class JobApplicationListResource(View):
    template_name = "job_application_list.html"

    def get(self, request):
        applications = JobApplication.objects.select_related(
            "caregiver", "caregiver__caregiver_user", "job"
        )
        return render(request, self.template_name, {"applications": applications})


class JobApplicationCreateResource(View):
    template_name = "job_application_form.html"

    def get(self, request):
        caregivers = Caregiver.objects.select_related("caregiver_user")
        jobs = Job.objects.select_related("member", "member__member_user")
        return render(
            request, self.template_name, {"caregivers": caregivers, "jobs": jobs}
        )

    def post(self, request):
        caregiver = get_object_or_404(Caregiver, pk=request.POST.get("caregiver_id"))
        job = get_object_or_404(Job, pk=request.POST.get("job_id"))

        if JobApplication.objects.filter(caregiver=caregiver, job=job).exists():
            messages.error(request, "This caregiver has already applied for this job.")
            return redirect("job_application_create")

        JobApplication.objects.create(
            caregiver=caregiver,
            job=job,
            date_applied=timezone.now().date(),
        )
        messages.success(request, "Application submitted successfully.")
        next_url = request.POST.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}
        ):
            return redirect(next_url)
        return redirect("job_application_list")


class JobApplicationDeleteResource(View):
    def post(self, request, pk):
        application = get_object_or_404(JobApplication, pk=pk)
        application.delete()
        messages.success(request, "Application deleted successfully.")
        return redirect("job_application_list")


# --------------------
# APPOINTMENT RESOURCES
# --------------------
class AppointmentListResource(View):
    template_name = "appointment_list.html"

    def get(self, request):
        appointments = Appointment.objects.select_related(
            "caregiver",
            "caregiver__caregiver_user",
            "member",
            "member__member_user",
        )
        status = request.GET.get("status")
        if status:
            appointments = appointments.filter(status__iexact=status)
        return render(
            request,
            self.template_name,
            {
                "appointments": appointments,
                "status_filter": status or "",
                "status_options": APPOINTMENT_STATUS_OPTIONS,
            },
        )


class AppointmentCreateResource(View):
    template_name = "appointment_form.html"

    def get(self, request):
        caregivers = Caregiver.objects.select_related("caregiver_user")
        members = Member.objects.select_related("member_user")
        return render(
            request,
            self.template_name,
            {
                "caregivers": caregivers,
                "members": members,
                "appointment": None,
                "current_status": "pending",
                "status_options": APPOINTMENT_STATUS_OPTIONS,
            },
        )

    def post(self, request):
        caregiver = get_object_or_404(Caregiver, pk=request.POST.get("caregiver_id"))
        member = get_object_or_404(Member, pk=request.POST.get("member_id"))

        if Appointment.objects.filter(caregiver=caregiver, member=member).exists():
            messages.error(request, "The appointment already exists.")
            return redirect("appointment_create")

        Appointment.objects.create(
            caregiver=caregiver,
            member=member,
            appointment_date=request.POST.get("appointment_date"),
            appointment_time=request.POST.get("appointment_time"),
            work_hours=request.POST.get("work_hours"),
            status=self._normalize_status(request.POST.get("status")),
        )
        messages.success(request, "Appointment created successfully.")
        return redirect("appointment_list")

    @staticmethod
    def _normalize_status(value):
        if value in APPOINTMENT_STATUS_OPTIONS:
            return value
        return "pending"


class AppointmentUpdateResource(View):
    template_name = "appointment_form.html"

    def get(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        caregivers = Caregiver.objects.select_related("caregiver_user")
        members = Member.objects.select_related("member_user")
        return render(
            request,
            self.template_name,
            {
                "appointment": appointment,
                "caregivers": caregivers,
                "members": members,
                "current_status": appointment.status or "",
                "status_options": APPOINTMENT_STATUS_OPTIONS,
            },
        )

    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        appointment.caregiver = get_object_or_404(
            Caregiver, pk=request.POST.get("caregiver_id")
        )
        appointment.member = get_object_or_404(
            Member, pk=request.POST.get("member_id")
        )
        appointment.appointment_date = request.POST.get("appointment_date")
        appointment.appointment_time = request.POST.get("appointment_time")
        appointment.work_hours = request.POST.get("work_hours")
        appointment.status = AppointmentCreateResource._normalize_status(
            request.POST.get("status")
        )
        appointment.save()
        messages.success(request, "Appointment updated successfully.")
        return redirect("appointment_list")


class AppointmentDeleteResource(View):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        appointment.delete()
        messages.success(request, "Appointment deleted successfully.")
        return redirect("appointment_list")


class AppointmentStatusResource(View):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        appointment.status = AppointmentCreateResource._normalize_status(
            request.POST.get("status")
        )
        appointment.save(update_fields=["status"])
        messages.success(request, "Appointment status updated.")
        return redirect("appointment_list")
