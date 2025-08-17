from abc import ABC, abstractmethod
from django.core.mail import send_mail
from django.conf import settings

class NotificationStrategy(ABC):
    """Abstract base class for notification strategies"""
    
    @abstractmethod
    def send_notification(self, appointment, message):
        pass

class EmailStrategy(NotificationStrategy):
    """Email notification strategy"""
    
    def send_notification(self, appointment, message):
        send_mail(
            subject=f"Appointment {appointment.status.title()}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.pet.owner.email]
        )

class SMSStrategy(NotificationStrategy):
    """SMS notification strategy"""
    
    def send_notification(self, appointment, message):
        # Implement SMS sending logic here
        # This is a placeholder for actual SMS implementation
        pass

class PushNotificationStrategy(NotificationStrategy):
    """Push notification strategy"""
    
    def send_notification(self, appointment, message):
        # Implement push notification logic here
        # This is a placeholder for actual push notification implementation
        pass

class NotificationContext:
    """Context class that uses a notification strategy"""
    
    def __init__(self, strategy: NotificationStrategy):
        self._strategy = strategy
    
    def set_strategy(self, strategy: NotificationStrategy):
        self._strategy = strategy
    
    def send_notification(self, appointment, message):
        return self._strategy.send_notification(appointment, message)
