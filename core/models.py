from django.db import models

class User(models.Model):
    user_id = models.AutoField(primary_key=True) 
    email = models.CharField(max_length=255, unique=True)
    given_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    city = models.CharField(max_length=100, null=True)
    phone_number = models.CharField(max_length=20, null=True)
    profile_description = models.TextField(null=True)
    password = models.CharField(max_length=255)

    class Meta:
        db_table = 'USER'

    def __str__(self):
        return f"{self.given_name} {self.surname}"


class Member(models.Model):
    member_user = models.OneToOneField(
        User, on_delete=models.CASCADE, db_column='member_user_id', primary_key=True
    )
    house_rules = models.TextField(blank=True, null=True)
    dependent_description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'member'

    def __str__(self):
        return f"Member {self.member_user_id}"


class Address(models.Model):
    member = models.OneToOneField(
        Member, on_delete=models.CASCADE, db_column='member_user_id', primary_key=True
    )
    house_number = models.CharField(max_length=20, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    town = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'address'

    def __str__(self):
        return f"Address for {self.member}"


class Caregiver(models.Model):
    caregiver_user = models.OneToOneField(
        User, on_delete=models.CASCADE, db_column='caregiver_user_id', primary_key=True
    )
    photo = models.ImageField(upload_to='caregiver_photos/', null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    caregiving_type = models.CharField(max_length=50, blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'caregiver'

    def __str__(self):
        return f"Caregiver {self.caregiver_user_id}"


class Job(models.Model):
    job_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(
        Member, on_delete=models.SET_NULL, db_column='member_user_id', blank=True, null=True
    )
    required_caregiving_type = models.CharField(max_length=50, blank=True, null=True)
    other_requirements = models.TextField(blank=True, null=True)
    date_posted = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'job'

    def __str__(self):
        return f"Job {self.job_id}"


class JobApplication(models.Model):
    id = models.AutoField(primary_key=True)
    caregiver = models.ForeignKey(
        Caregiver, on_delete=models.CASCADE, db_column='caregiver_user_id'
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, db_column='job_id')
    date_applied = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'job_application'

    def __str__(self):
        return f"Application: Caregiver {self.caregiver_id} -> Job {self.job_id}"


class Appointment(models.Model):
    appointment_id = models.AutoField(primary_key=True)
    caregiver = models.ForeignKey(
        Caregiver, on_delete=models.SET_NULL, db_column='caregiver_user_id', blank=True, null=True
    )
    member = models.ForeignKey(
        Member, on_delete=models.SET_NULL, db_column='member_user_id', blank=True, null=True
    )
    appointment_date = models.DateField(blank=True, null=True)
    appointment_time = models.TimeField(blank=True, null=True)
    work_hours = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'appointment'

    def __str__(self):
        return f"Appointment {self.appointment_id}"


class JobDetail(models.Model):
    job = models.OneToOneField(
        Job,
        on_delete=models.CASCADE,
        related_name="detail",
        db_column="job_id",
    )
    care_recipient_age = models.PositiveIntegerField(blank=True, null=True)
    preferred_time_slots = models.CharField(max_length=255, blank=True, null=True)
    service_frequency = models.CharField(max_length=100, blank=True, null=True)
    additional_notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "job_detail"

    def __str__(self):
        return f"Details for Job {self.job_id}"


class ContactRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("declined", "Declined"),
    ]

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="contact_requests",
        db_column="member_user_id",
    )
    caregiver = models.ForeignKey(
        Caregiver,
        on_delete=models.CASCADE,
        related_name="contact_requests",
        db_column="caregiver_user_id",
    )
    message = models.TextField()
    allow_caregiver_initiate = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "contact_request"

    def __str__(self):
        return f"ContactRequest {self.pk}"