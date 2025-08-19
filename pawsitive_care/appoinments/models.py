from django.db import models
from django.conf import settings
from pets.models import Pet

class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration = models.DurationField()  # Expected duration of the service
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return self.name

class ClinicBranch(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    contact_number = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
    ]
    
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE)
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT)
    veterinarian = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='vet_appointments')
    date_time = models.DateTimeField()
    clinic_branch = models.ForeignKey(ClinicBranch, on_delete=models.PROTECT)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_time']
    
    def __str__(self):
        return f"{self.pet.name}'s appointment with Dr. {self.veterinarian.get_full_name()} on {self.date_time}"

class AppointmentFeedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comments = models.TextField(blank=True)
    vet_rating = models.IntegerField(choices=RATING_CHOICES)
    clinic_rating = models.IntegerField(choices=RATING_CHOICES)
    service_rating = models.IntegerField(choices=RATING_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Feedback for {self.appointment}"

class AppointmentNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('confirmation', 'Confirmation'),
        ('reminder', 'Reminder'),
        ('cancellation', 'Cancellation'),
        ('reschedule', 'Reschedule'),
    ]
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.appointment}"