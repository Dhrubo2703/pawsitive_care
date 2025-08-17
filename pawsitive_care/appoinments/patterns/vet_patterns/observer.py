from abc import ABC, abstractmethod
from django.db.models.signals import post_save
from django.dispatch import receiver
from ...models import Appointment
from django.core.mail import send_mail
from django.conf import settings

class AppointmentObserver(ABC):
    """Abstract base class for appointment observers"""
    
    @abstractmethod
    def update(self, appointment, changed_fields=None):
        pass

class VetScheduleObserver(AppointmentObserver):
    """Observer for updating vet's schedule"""
    
    def update(self, appointment, changed_fields=None):
        # Update vet's schedule and availability
        if changed_fields and ('date_time' in changed_fields or 'status' in changed_fields):
            # Update vet's calendar
            self._update_vet_calendar(appointment)
            # Send notification to vet
            self._notify_vet(appointment)
    
    def _update_vet_calendar(self, appointment):
        # Logic to update vet's calendar
        pass
    
    def _notify_vet(self, appointment):
        subject = f"Appointment Update - {appointment.status.title()}"
        message = self._get_notification_message(appointment)
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.veterinarian.email]
        )
    
    def _get_notification_message(self, appointment):
        return f"""
        Appointment Update:
        Pet: {appointment.pet.name}
        Owner: {appointment.pet.owner.get_full_name()}
        Date: {appointment.date_time.strftime('%B %d, %Y at %I:%M %p')}
        Status: {appointment.status.title()}
        """

class EmergencyAlertObserver(AppointmentObserver):
    """Observer for emergency appointments"""
    
    def update(self, appointment, changed_fields=None):
        if appointment.is_emergency and appointment.status == 'pending':
            self._send_emergency_alert(appointment)
    
    def _send_emergency_alert(self, appointment):
        subject = "⚠️ EMERGENCY Appointment Alert"
        message = f"""
        Emergency appointment requested!
        
        Pet: {appointment.pet.name}
        Owner: {appointment.pet.owner.get_full_name()}
        Contact: {appointment.pet.owner.phone_number}
        Date: {appointment.date_time.strftime('%B %d, %Y at %I:%M %p')}
        Notes: {appointment.notes}
        
        Please respond ASAP.
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.veterinarian.email],
            priority='high'
        )

class AppointmentReminderObserver(AppointmentObserver):
    """Observer for appointment reminders"""
    
    def update(self, appointment, changed_fields=None):
        if appointment.status == 'confirmed':
            self._schedule_reminders(appointment)
    
    def _schedule_reminders(self, appointment):
        # Schedule reminders at different intervals
        self._schedule_reminder(appointment, hours=24)
        self._schedule_reminder(appointment, hours=1)
    
    def _schedule_reminder(self, appointment, hours):
        # Logic to schedule reminder using Celery or similar
        pass

class AppointmentSubject:
    """Subject that maintains the list of observers and notifies them of changes"""
    
    _observers = []
    
    @classmethod
    def attach(cls, observer: AppointmentObserver):
        if observer not in cls._observers:
            cls._observers.append(observer)
    
    @classmethod
    def detach(cls, observer: AppointmentObserver):
        cls._observers.remove(observer)
    
    @classmethod
    def notify(cls, appointment, changed_fields=None):
        for observer in cls._observers:
            observer.update(appointment, changed_fields)

# Signal receiver to trigger notifications
@receiver(post_save, sender=Appointment)
def appointment_changed(sender, instance, created, **kwargs):
    """Handle appointment changes and notify observers"""
    AppointmentSubject.notify(instance, kwargs.get('update_fields'))
