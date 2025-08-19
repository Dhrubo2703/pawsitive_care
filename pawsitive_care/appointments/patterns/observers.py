from abc import ABC, abstractmethod
from django.core.mail import send_mail
from django.conf import settings

class AppointmentObserver(ABC):
    @abstractmethod
    def update(self, appointment):
        pass

class EmailNotificationObserver(AppointmentObserver):
    def update(self, appointment):
        # Send email to client
        self._send_client_email(appointment)
        # Send email to vet
        self._send_vet_email(appointment)
    
    def _send_client_email(self, appointment):
        subject = f'Appointment Update - {appointment.status}'
        message = self._get_client_message(appointment)
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.client.email],
            fail_silently=True,
        )
    
    def _send_vet_email(self, appointment):
        subject = f'Appointment Update - {appointment.status}'
        message = self._get_vet_message(appointment)
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.vet.email],
            fail_silently=True,
        )
    
    def _get_client_message(self, appointment):
        if appointment.status == 'SCHEDULED':
            return f'''Your appointment has been scheduled:
                    Pet: {appointment.pet.name}
                    Date: {appointment.date}
                    Time: {appointment.time}
                    Vet: Dr. {appointment.vet.get_full_name()}'''
        elif appointment.status == 'CANCELLED':
            return f'Your appointment for {appointment.pet.name} on {appointment.date} has been cancelled.'
        else:
            return f'Your appointment for {appointment.pet.name} has been marked as {appointment.status}.'
    
    def _get_vet_message(self, appointment):
        if appointment.status == 'SCHEDULED':
            return f'''New appointment scheduled:
                    Pet: {appointment.pet.name}
                    Owner: {appointment.client.get_full_name()}
                    Date: {appointment.date}
                    Time: {appointment.time}'''
        elif appointment.status == 'CANCELLED':
            return f'Appointment for {appointment.pet.name} on {appointment.date} has been cancelled.'
        else:
            return f'Appointment for {appointment.pet.name} has been marked as {appointment.status}.'
