from datetime import datetime, timedelta
from typing import Optional
from ..builder import AppointmentBuilder
from django.core.exceptions import ValidationError

class AppointmentDirector:
    """Director class that uses AppointmentBuilder to construct appointments with common configurations"""
    
    def __init__(self):
        self._builder = AppointmentBuilder()
    
    def create_regular_checkup(self, pet, vet, clinic_branch, date_time):
        """Creates a regular checkup appointment"""
        return self._builder\
            .set_pet(pet)\
            .set_service('regular_checkup')\
            .set_veterinarian(vet)\
            .set_datetime(date_time)\
            .set_clinic_branch(clinic_branch)\
            .set_notes('Regular health checkup')\
            .set_status('pending')\
            .build()
    
    def create_emergency_appointment(self, pet, clinic_branch, description):
        """Creates an emergency appointment with the next available vet"""
        from ...models import Veterinarian
        
        # Find available vet for emergency
        available_vet = self._find_available_emergency_vet(clinic_branch)
        if not available_vet:
            raise ValidationError("No veterinarians available for emergency")
        
        return self._builder\
            .set_pet(pet)\
            .set_service('emergency')\
            .set_veterinarian(available_vet)\
            .set_datetime(datetime.now())\
            .set_clinic_branch(clinic_branch)\
            .set_notes(f'Emergency: {description}')\
            .set_status('urgent')\
            .build()
    
    def create_follow_up(self, original_appointment, follow_up_date):
        """Creates a follow-up appointment based on an original appointment"""
        return self._builder\
            .set_pet(original_appointment.pet)\
            .set_service('follow_up')\
            .set_veterinarian(original_appointment.veterinarian)\
            .set_datetime(follow_up_date)\
            .set_clinic_branch(original_appointment.clinic_branch)\
            .set_notes(f'Follow-up for appointment from {original_appointment.date_time.date()}')\
            .set_status('pending')\
            .build()
    
    def create_vaccination(self, pet, vet, clinic_branch, vaccine_type, date_time):
        """Creates a vaccination appointment"""
        return self._builder\
            .set_pet(pet)\
            .set_service('vaccination')\
            .set_veterinarian(vet)\
            .set_datetime(date_time)\
            .set_clinic_branch(clinic_branch)\
            .set_notes(f'Vaccination: {vaccine_type}')\
            .set_status('pending')\
            .build()
    
    def create_surgery(self, pet, vet, clinic_branch, surgery_type, date_time, pre_op_notes=""):
        """Creates a surgery appointment with necessary pre-operation checks"""
        notes = f"Surgery Type: {surgery_type}\nPre-op Notes: {pre_op_notes}"
        
        return self._builder\
            .set_pet(pet)\
            .set_service('surgery')\
            .set_veterinarian(vet)\
            .set_datetime(date_time)\
            .set_clinic_branch(clinic_branch)\
            .set_notes(notes)\
            .set_status('scheduled')\
            .build()
    
    def _find_available_emergency_vet(self, clinic_branch):
        """Helper method to find an available vet for emergency"""
        from ...models import Veterinarian
        from django.db.models import Q
        from datetime import datetime, timedelta
        
        current_time = datetime.now()
        
        # Find vets who are:
        # 1. Working at this branch
        # 2. Not currently in another appointment
        # 3. Have emergency handling capability
        available_vets = Veterinarian.objects.filter(
            Q(clinic_branch=clinic_branch) &
            Q(can_handle_emergencies=True) &
            ~Q(appointment__date_time__range=(
                current_time - timedelta(hours=1),
                current_time + timedelta(hours=1)
            ))
        ).first()
        
        return available_vets
