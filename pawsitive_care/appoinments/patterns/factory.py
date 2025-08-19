from abc import ABC, abstractmethod
from ..models import Appointment, ServiceType

class AppointmentFactory(ABC):
    """Abstract Factory for creating different types of appointments"""
    
    @abstractmethod
    def create_appointment(self, **kwargs):
        pass
    
    def _get_service_type(self, service_name):
        return ServiceType.objects.get(name=service_name)

class GeneralCheckupFactory(AppointmentFactory):
    def create_appointment(self, **kwargs):
        return Appointment.objects.create(**kwargs)

class VaccinationFactory(AppointmentFactory):
    def create_appointment(self, **kwargs):
        return Appointment.objects.create(**kwargs)

class SurgeryFactory(AppointmentFactory):
    def create_appointment(self, **kwargs):
        return Appointment.objects.create(**kwargs)

class GroomingFactory(AppointmentFactory):
    def create_appointment(self, **kwargs):
        return Appointment.objects.create(**kwargs)

def get_appointment_factory(service_type):
    """Factory method to get the appropriate appointment factory"""
    factories = {
        'General Checkup': GeneralCheckupFactory(),
        'Vaccination': VaccinationFactory(),
        'Surgery': SurgeryFactory(),
        'Grooming': GroomingFactory(),
    }
    return factories.get(service_type)
