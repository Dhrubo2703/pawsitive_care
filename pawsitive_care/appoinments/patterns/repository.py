from django.db.models import Q
from datetime import datetime, timedelta
from ..models import Appointment, AppointmentFeedback

class AppointmentRepository:
    """Repository pattern for appointment-related database operations"""
    
    @staticmethod
    def get_upcoming_appointments(user, limit=None):
        """Get upcoming appointments for a user"""
        now = datetime.now()
        appointments = Appointment.objects.filter(
            Q(pet__owner=user) | Q(veterinarian=user),
            date_time__gte=now,
            status__in=['pending', 'confirmed']
        ).order_by('date_time')
        
        if limit:
            appointments = appointments[:limit]
        return appointments
    
    @staticmethod
    def get_appointment_history(user, limit=None):
        """Get past appointments for a user"""
        now = datetime.now()
        appointments = Appointment.objects.filter(
            Q(pet__owner=user) | Q(veterinarian=user),
            date_time__lt=now
        ).order_by('-date_time')
        
        if limit:
            appointments = appointments[:limit]
        return appointments
    
    @staticmethod
    def get_available_slots(vet, date, duration=timedelta(minutes=30)):
        """Get available appointment slots for a veterinarian on a specific date"""
        # Get all appointments for the vet on the given date
        existing_appointments = Appointment.objects.filter(
            veterinarian=vet,
            date_time__date=date,
            status='confirmed'
        ).order_by('date_time')
        
        # Generate all possible slots
        start_time = datetime.combine(date, datetime.min.time().replace(hour=9))  # 9 AM
        end_time = datetime.combine(date, datetime.min.time().replace(hour=17))   # 5 PM
        
        slots = []
        current_slot = start_time
        
        while current_slot + duration <= end_time:
            # Check if slot conflicts with existing appointments
            is_available = True
            for appt in existing_appointments:
                if (current_slot < appt.date_time + duration and 
                    current_slot + duration > appt.date_time):
                    is_available = False
                    break
            
            if is_available:
                slots.append(current_slot)
            
            current_slot += duration
        
        return slots
    
    @staticmethod
    def get_feedback_stats(vet):
        """Get aggregate feedback statistics for a veterinarian"""
        feedbacks = AppointmentFeedback.objects.filter(
            appointment__veterinarian=vet
        )
        
        if not feedbacks.exists():
            return {
                'average_rating': 0,
                'total_reviews': 0,
                'rating_distribution': {i: 0 for i in range(1, 6)}
            }
        
        total_reviews = feedbacks.count()
        avg_rating = sum(f.vet_rating for f in feedbacks) / total_reviews
        
        distribution = {i: len([f for f in feedbacks if f.vet_rating == i]) 
                       for i in range(1, 6)}
        
        return {
            'average_rating': round(avg_rating, 1),
            'total_reviews': total_reviews,
            'rating_distribution': distribution
        }
