from abc import ABC, abstractmethod
from django.core.mail import send_mail
from django.conf import settings
from ..models import AppointmentNotification

class AppointmentObserver(ABC):
    """Abstract base class for appointment observers"""
    
    @abstractmethod
    def update(self, appointment):
        pass

class EmailNotificationObserver(AppointmentObserver):
    """Sends email notifications for appointment events"""
    
    def update(self, appointment):
        subject = f"Appointment Update - {appointment.status.title()}"
        message = self._get_message(appointment)
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [appointment.pet.owner.email]
        
        send_mail(subject, message, from_email, recipient_list)
        
        # Log notification
        AppointmentNotification.objects.create(
            appointment=appointment,
            notification_type='confirmation' if appointment.status == 'confirmed' else 'update',
            message=message,
            is_sent=True
        )
    
    def _get_message(self, appointment):
        status_messages = {
            'confirmed': f"Your appointment with Dr. {appointment.veterinarian.get_full_name()} has been confirmed for {appointment.date_time}.",
            'cancelled': f"Your appointment with Dr. {appointment.veterinarian.get_full_name()} for {appointment.date_time} has been cancelled.",
            'completed': f"Thank you for visiting us! Your appointment with Dr. {appointment.veterinarian.get_full_name()} has been completed.",
            'pending': f"Your appointment request with Dr. {appointment.veterinarian.get_full_name()} for {appointment.date_time} is pending confirmation.",
        }
        return status_messages.get(appointment.status, "Your appointment status has been updated.")

class ReminderObserver(AppointmentObserver):
    """Sends appointment reminders"""
    
    def update(self, appointment):
        if appointment.status != 'confirmed':
            return
            
        message = f"Reminder: You have an appointment with Dr. {appointment.veterinarian.get_full_name()} tomorrow at {appointment.date_time.strftime('%I:%M %p')}"
        
        AppointmentNotification.objects.create(
            appointment=appointment,
            notification_type='reminder',
            message=message,
            is_sent=True
        )
        
        # Send email
        send_mail(
            "Appointment Reminder",
            message,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.pet.owner.email]
        )

class AppointmentSubject:
    """Subject class that maintains a list of observers and notifies them of changes"""
    
    _observers = []
    
    @classmethod
    def attach(cls, observer):
        if observer not in cls._observers:
            cls._observers.append(observer)
    
    @classmethod
    def detach(cls, observer):
        cls._observers.remove(observer)
    
    @classmethod
    def notify(cls, appointment):
        for observer in cls._observers:
            observer.update(appointment)
