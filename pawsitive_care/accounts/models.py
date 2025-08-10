from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('vet', 'Veterinarian'),
        ('staff', 'Staff'),
        ('client', 'Client'),
    ]
    
    phone = models.CharField(max_length=20, blank=False)
    address = models.TextField(blank=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_vet(self):
        return self.role == 'vet'
    
    def is_staff_member(self):
        return self.role == 'staff'
    
    def is_client(self):
        return self.role == 'client'


class Veterinarian(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='veterinarian'
    )
    clinic_branch = models.ForeignKey(
        'appoinments.ClinicBranch',  # Changed from inventory to appoinments app
        on_delete=models.SET_NULL,
        null=True,
        related_name='veterinarians'
    )
    specialization = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, unique=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    can_handle_emergencies = models.BooleanField(default=False)
    bio = models.TextField(blank=True)
    available_days = models.CharField(max_length=100, blank=True)  # Store as comma-separated days
    work_start_time = models.TimeField(null=True, blank=True)
    work_end_time = models.TimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"
    
    def get_full_name(self):
        return self.user.get_full_name()
    
    def get_email(self):
        return self.user.email
    
    class Meta:
        verbose_name = 'Veterinarian'
        verbose_name_plural = 'Veterinarians'
        ordering = ['user__first_name', 'user__last_name']
