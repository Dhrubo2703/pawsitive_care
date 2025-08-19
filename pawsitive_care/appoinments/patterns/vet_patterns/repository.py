from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, timedelta
from django.db.models import Q
from ...models import Appointment
from django.core.exceptions import ObjectDoesNotExist

class IAppointmentRepository(ABC):
    """Repository interface for appointment operations"""
    
    @abstractmethod
    def get_by_id(self, appointment_id: int) -> Optional[Appointment]:
        pass
    
    @abstractmethod
    def get_all_by_vet(self, vet_id: int, start_date: datetime, end_date: datetime) -> List[Appointment]:
        pass
    
    @abstractmethod
    def get_all_by_pet(self, pet_id: int) -> List[Appointment]:
        pass
    
    @abstractmethod
    def save(self, appointment: Appointment) -> Appointment:
        pass
    
    @abstractmethod
    def delete(self, appointment_id: int) -> bool:
        pass
    
    @abstractmethod
    def get_upcoming_appointments(self, vet_id: int) -> List[Appointment]:
        pass

class DjangoAppointmentRepository(IAppointmentRepository):
    """Django implementation of the appointment repository"""
    
    def get_by_id(self, appointment_id: int) -> Optional[Appointment]:
        try:
            return Appointment.objects.get(id=appointment_id)
        except ObjectDoesNotExist:
            return None
    
    def get_all_by_vet(self, vet_id: int, start_date: datetime, end_date: datetime) -> List[Appointment]:
        return list(Appointment.objects.filter(
            veterinarian_id=vet_id,
            date_time__range=(start_date, end_date)
        ).order_by('date_time'))
    
    def get_all_by_pet(self, pet_id: int) -> List[Appointment]:
        return list(Appointment.objects.filter(
            pet_id=pet_id
        ).order_by('-date_time'))
    
    def save(self, appointment: Appointment) -> Appointment:
        appointment.save()
        return appointment
    
    def delete(self, appointment_id: int) -> bool:
        try:
            appointment = Appointment.objects.get(id=appointment_id)
            appointment.delete()
            return True
        except ObjectDoesNotExist:
            return False
    
    def get_upcoming_appointments(self, vet_id: int) -> List[Appointment]:
        now = datetime.now()
        return list(Appointment.objects.filter(
            veterinarian_id=vet_id,
            date_time__gte=now
        ).order_by('date_time'))
    
    def get_available_slots(self, vet_id: int, date: datetime) -> List[datetime]:
        """Get available appointment slots for a specific vet on a given day"""
        # Define working hours (8 AM to 6 PM)
        start_hour = 8
        end_hour = 18
        slot_duration = timedelta(minutes=30)
        
        # Get all appointments for the vet on the given day
        day_start = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        
        existing_appointments = Appointment.objects.filter(
            veterinarian_id=vet_id,
            date_time__range=(day_start, day_end)
        ).values_list('date_time', flat=True)
        
        # Generate all possible slots
        available_slots = []
        current_slot = day_start
        
        while current_slot < day_end:
            if current_slot not in existing_appointments:
                available_slots.append(current_slot)
            current_slot += slot_duration
        
        return available_slots
    
    def get_emergency_appointments(self, clinic_branch_id: int) -> List[Appointment]:
        """Get all emergency appointments for a clinic branch"""
        return list(Appointment.objects.filter(
            clinic_branch_id=clinic_branch_id,
            service_type__name__icontains='emergency',
            status__in=['pending', 'confirmed']
        ).order_by('date_time'))
    
    def get_overdue_appointments(self, vet_id: int) -> List[Appointment]:
        """Get appointments that are overdue for completion"""
        now = datetime.now()
        return list(Appointment.objects.filter(
            veterinarian_id=vet_id,
            date_time__lt=now,
            status='pending'
        ).order_by('date_time'))
    
    def get_appointments_by_status(self, vet_id: int, status: str) -> List[Appointment]:
        """Get appointments by status for a specific vet"""
        return list(Appointment.objects.filter(
            veterinarian_id=vet_id,
            status=status
        ).order_by('date_time'))
    
    def get_conflicts(self, vet_id: int, start_time: datetime, end_time: datetime) -> List[Appointment]:
        """Check for appointment conflicts in a time range"""
        return list(Appointment.objects.filter(
            veterinarian_id=vet_id,
            date_time__range=(start_time, end_time)
        ).order_by('date_time'))
    
    def update_status(self, appointment_id: int, new_status: str) -> bool:
        """Update the status of an appointment"""
        try:
            appointment = Appointment.objects.get(id=appointment_id)
            appointment.status = new_status
            appointment.save(update_fields=['status'])
            return True
        except ObjectDoesNotExist:
            return False
