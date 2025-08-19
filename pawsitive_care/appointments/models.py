from django.db import models
from django.conf import settings
from pets.models import Pet

class AppointmentType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.name} (${self.base_cost})"

class Appointment(models.Model):
    APPOINTMENT_STATUS = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('PENDING', 'Pending Reassignment'),
    ]
    
    APPOINTMENT_TYPES = [
        ('GENERAL', 'General Checkup'),
        ('VACCINATION', 'Vaccination'),
        ('SURGERY', 'Surgery'),
        ('ILLNESS', 'Illness / Injury'),
        ('FOLLOWUP', 'Follow-up'),
        ('OTHER', 'Others'),
    ]
    
    appointment_id = models.AutoField(primary_key=True)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='appointments')
    vet = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vet_appointments', limit_choices_to={'role': 'vet'})
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_appointments')
    date = models.DateField()
    time = models.TimeField()
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPES, default='GENERAL')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=APPOINTMENT_STATUS, default='SCHEDULED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return f"Appointment #{self.appointment_id} - {self.pet.name} with Dr. {self.vet.get_full_name()}"
