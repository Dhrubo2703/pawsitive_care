from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings

class AppointmentActionStrategy(ABC):
    """Abstract base class for appointment actions"""
    
    @abstractmethod
    def execute(self, appointment, **kwargs):
        pass

class CompleteAppointmentStrategy(AppointmentActionStrategy):
    """Strategy for completing an appointment"""
    
    def execute(self, appointment, **kwargs):
        treatment_notes = kwargs.get('treatment_notes', '')
        diagnosis = kwargs.get('diagnosis', '')
        follow_up_date = kwargs.get('follow_up_date')
        
        appointment.status = 'completed'
        appointment.treatment_notes = treatment_notes
        appointment.diagnosis = diagnosis
        appointment.follow_up_date = follow_up_date
        appointment.save()
        
        # Create follow-up appointment if needed
        if follow_up_date:
            self._schedule_follow_up(appointment, follow_up_date)
    
    def _schedule_follow_up(self, original_appointment, follow_up_date):
        from ..builder import AppointmentBuilder
        
        builder = AppointmentBuilder()
        follow_up = builder\
            .set_pet(original_appointment.pet)\
            .set_veterinarian(original_appointment.veterinarian)\
            .set_service_type(original_appointment.service_type)\
            .set_clinic_branch(original_appointment.clinic_branch)\
            .set_datetime(follow_up_date)\
            .set_notes("Follow-up appointment")\
            .set_status('pending')\
            .build()
        
        follow_up.save()

class RescheduleStrategy(AppointmentActionStrategy):
    """Strategy for rescheduling appointments"""
    
    def execute(self, appointment, **kwargs):
        new_datetime = kwargs.get('new_datetime')
        reason = kwargs.get('reason', '')
        
        if not new_datetime:
            raise ValueError("New datetime is required for rescheduling")
        
        old_datetime = appointment.date_time
        appointment.date_time = new_datetime
        appointment.save(update_fields=['date_time'])
        
        self._notify_rescheduled(appointment, old_datetime, new_datetime, reason)
    
    def _notify_rescheduled(self, appointment, old_datetime, new_datetime, reason):
        # Notify pet owner
        subject = "Appointment Rescheduled"
        message = f"""
        Your appointment has been rescheduled:
        
        Old date/time: {old_datetime.strftime('%B %d, %Y at %I:%M %p')}
        New date/time: {new_datetime.strftime('%B %d, %Y at %I:%M %p')}
        
        Reason: {reason}
        
        Pet: {appointment.pet.name}
        Veterinarian: Dr. {appointment.veterinarian.get_full_name()}
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.pet.owner.email]
        )

class CancellationStrategy(AppointmentActionStrategy):
    """Strategy for cancelling appointments"""
    
    def execute(self, appointment, **kwargs):
        reason = kwargs.get('reason', '')
        notify_client = kwargs.get('notify_client', True)
        
        appointment.status = 'cancelled'
        appointment.cancellation_reason = reason
        appointment.save()
        
        if notify_client:
            self._notify_cancellation(appointment, reason)
    
    def _notify_cancellation(self, appointment, reason):
        subject = "Appointment Cancelled"
        message = f"""
        Your appointment has been cancelled:
        
        Date/time: {appointment.date_time.strftime('%B %d, %Y at %I:%M %p')}
        Pet: {appointment.pet.name}
        Veterinarian: Dr. {appointment.veterinarian.get_full_name()}
        
        Reason: {reason}
        
        Please contact us to reschedule your appointment.
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.pet.owner.email]
        )

class NoShowStrategy(AppointmentActionStrategy):
    """Strategy for handling no-show appointments"""
    
    def execute(self, appointment, **kwargs):
        notes = kwargs.get('notes', '')
        
        appointment.status = 'no_show'
        appointment.notes = f"No-show: {notes}"
        appointment.save()
        
        # Record no-show in patient history
        self._record_no_show(appointment)
        
        # Notify client
        self._notify_no_show(appointment)
    
    def _record_no_show(self, appointment):
        # Add to patient history
        pass
    
    def _notify_no_show(self, appointment):
        subject = "Missed Appointment Notice"
        message = f"""
        We noticed you missed your appointment:
        
        Date/time: {appointment.date_time.strftime('%B %d, %Y at %I:%M %p')}
        Pet: {appointment.pet.name}
        Veterinarian: Dr. {appointment.veterinarian.get_full_name()}
        
        Please contact us to reschedule your appointment.
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.pet.owner.email]
        )

class ReferralStrategy(AppointmentActionStrategy):
    """Strategy for referring appointments to other vets"""
    
    def execute(self, appointment, **kwargs):
        new_vet = kwargs.get('new_vet')
        reason = kwargs.get('reason', '')
        notes = kwargs.get('notes', '')
        
        if not new_vet:
            raise ValueError("New veterinarian is required for referral")
        
        old_vet = appointment.veterinarian
        appointment.veterinarian = new_vet
        appointment.notes = f"Referred by Dr. {old_vet.get_full_name()}: {notes}"
        appointment.save()
        
        self._notify_referral(appointment, old_vet, new_vet, reason)
    
    def _notify_referral(self, appointment, old_vet, new_vet, reason):
        # Notify new vet
        subject = "Appointment Referral"
        message = f"""
        Dr. {old_vet.get_full_name()} has referred an appointment to you:
        
        Pet: {appointment.pet.name}
        Owner: {appointment.pet.owner.get_full_name()}
        Date/time: {appointment.date_time.strftime('%B %d, %Y at %I:%M %p')}
        
        Reason for referral: {reason}
        Notes: {appointment.notes}
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [new_vet.email]
        )
