from datetime import datetime, timedelta
from django.db.models import Q

class AppointmentScheduler:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppointmentScheduler, cls).__new__(cls)
            cls._instance.observers = []
        return cls._instance
    
    def add_observer(self, observer):
        self.observers.append(observer)
    
    def remove_observer(self, observer):
        self.observers.remove(observer)
    
    def notify_observers(self, appointment):
        for observer in self.observers:
            observer.update(appointment)
    
    def check_availability(self, vet, date, time):
        """Check if the vet is available at the given time"""
        from ..models import Appointment
        
        # Convert time to datetime for easier comparison
        appointment_datetime = datetime.combine(date, time)
        
        # Check 30 minutes before and after the requested time
        start_time = appointment_datetime - timedelta(minutes=30)
        end_time = appointment_datetime + timedelta(minutes=30)
        
        existing_appointments = Appointment.objects.filter(
            vet=vet,
            date=date,
            time__range=(start_time.time(), end_time.time()),
            status='SCHEDULED'
        )
        
        return not existing_appointments.exists()
    
    def schedule_appointment(self, pet, vet, client, date, time, appointment_type='GENERAL', notes=""):
        """Schedule a new appointment if the time slot is available"""
        from ..models import Appointment
        
        if self.check_availability(vet, date, time):
            appointment = Appointment.objects.create(
                pet=pet,
                vet=vet,
                appointment_type=appointment_type,
                client=client,
                date=date,
                time=time,
                notes=notes
            )
            self.notify_observers(appointment)
            return appointment
        return None
    
    def update_appointment_status(self, appointment, new_status):
        """Update the status of an appointment"""
        appointment.status = new_status
        appointment.save()
        self.notify_observers(appointment)
