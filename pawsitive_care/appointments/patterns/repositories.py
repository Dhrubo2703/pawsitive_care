class AppointmentRepository:
    @staticmethod
    def get_client_appointments(client, include_past=False):
        from ..models import Appointment
        from django.utils import timezone
        
        queryset = Appointment.objects.filter(client=client)
        if not include_past:
            queryset = queryset.filter(date__gte=timezone.now().date())
        return queryset.order_by('date', 'time')
    
    @staticmethod
    def get_vet_appointments(vet, include_past=False):
        from ..models import Appointment
        from django.utils import timezone
        
        queryset = Appointment.objects.filter(vet=vet)
        if not include_past:
            queryset = queryset.filter(date__gte=timezone.now().date())
        return queryset.order_by('date', 'time')
    
    @staticmethod
    def get_pet_appointments(pet, include_past=False):
        from ..models import Appointment
        from django.utils import timezone
        
        queryset = Appointment.objects.filter(pet=pet)
        if not include_past:
            queryset = queryset.filter(date__gte=timezone.now().date())
        return queryset.order_by('date', 'time')
    
    @staticmethod
    def get_appointment_by_id(appointment_id):
        from ..models import Appointment
        return Appointment.objects.get(appointment_id=appointment_id)
    
    @staticmethod
    def cancel_appointment(appointment_id):
        from .scheduler import AppointmentScheduler
        appointment = AppointmentRepository.get_appointment_by_id(appointment_id)
        scheduler = AppointmentScheduler()
        scheduler.update_appointment_status(appointment, 'CANCELLED')
        return appointment
    
    @staticmethod
    def complete_appointment(appointment_id):
        from .scheduler import AppointmentScheduler
        appointment = AppointmentRepository.get_appointment_by_id(appointment_id)
        scheduler = AppointmentScheduler()
        scheduler.update_appointment_status(appointment, 'COMPLETED')
        return appointment
