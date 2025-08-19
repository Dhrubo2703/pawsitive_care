from typing import Optional
from datetime import datetime
from ..models import Appointment

class AppointmentBuilder:
    """Builder pattern for creating appointments step by step"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self._appointment = {
            'pet': None,
            'service_type': None,
            'veterinarian': None,
            'date_time': None,
            'clinic_branch': None,
            'notes': '',
            'status': 'pending'
        }
    
    def set_pet(self, pet):
        self._appointment['pet'] = pet
        return self
    
    def set_service(self, service_type):
        self._appointment['service_type'] = service_type
        return self
    
    def set_veterinarian(self, vet):
        self._appointment['veterinarian'] = vet
        return self
    
    def set_datetime(self, date_time):
        self._appointment['date_time'] = date_time
        return self
    
    def set_clinic_branch(self, branch):
        self._appointment['clinic_branch'] = branch
        return self
    
    def set_notes(self, notes):
        self._appointment['notes'] = notes
        return self
    
    def set_status(self, status):
        self._appointment['status'] = status
        return self
    
    def build(self) -> Appointment:
        """Create and return the Appointment instance"""
        appointment = Appointment(
            pet=self._appointment['pet'],
            service_type=self._appointment['service_type'],
            veterinarian=self._appointment['veterinarian'],
            date_time=self._appointment['date_time'],
            clinic_branch=self._appointment['clinic_branch'],
            notes=self._appointment['notes'],
            status=self._appointment['status']
        )
        self.reset()
        return appointment
