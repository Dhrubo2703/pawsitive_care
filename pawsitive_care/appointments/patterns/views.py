from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from django.db.models import Q

class CalendarViewStrategy(ABC):
    @abstractmethod
    def get_appointments(self, date, **filters):
        pass

class DayViewStrategy(CalendarViewStrategy):
    def get_appointments(self, date, **filters):
        from ..models import Appointment
        return Appointment.objects.filter(
            date=date,
            status='SCHEDULED',
            **filters
        ).order_by('time')

class WeekViewStrategy(CalendarViewStrategy):
    def get_appointments(self, date, **filters):
        from ..models import Appointment
        week_start = date - timedelta(days=date.weekday())
        week_end = week_start + timedelta(days=6)
        return Appointment.objects.filter(
            date__range=[week_start, week_end],
            status='SCHEDULED',
            **filters
        ).order_by('date', 'time')

class MonthViewStrategy(CalendarViewStrategy):
    def get_appointments(self, date, **filters):
        from ..models import Appointment
        return Appointment.objects.filter(
            date__year=date.year,
            date__month=date.month,
            status='SCHEDULED',
            **filters
        ).order_by('date', 'time')
