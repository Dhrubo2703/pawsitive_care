from datetime import datetime

class AppointmentFactory:
    @staticmethod
    def create_appointment(appointment_data):
        """
        Create an appointment using the scheduler
        
        appointment_data should contain:
        - pet
        - vet
        - client
        - date
        - time
        - notes (optional)
        """
        from .scheduler import AppointmentScheduler
        
        scheduler = AppointmentScheduler()
        
        # Parse date and time if they're strings
        if isinstance(appointment_data['date'], str):
            appointment_data['date'] = datetime.strptime(
                appointment_data['date'], '%Y-%m-%d'
            ).date()
        
        if isinstance(appointment_data['time'], str):
            appointment_data['time'] = datetime.strptime(
                appointment_data['time'], '%H:%M'
            ).time()
        
        return scheduler.schedule_appointment(
            pet=appointment_data['pet'],
            vet=appointment_data['vet'],
            client=appointment_data['client'],
            date=appointment_data['date'],
            time=appointment_data['time'],
            appointment_type=appointment_data.get('appointment_type', 'GENERAL'),
            notes=appointment_data.get('notes', '')
        )
