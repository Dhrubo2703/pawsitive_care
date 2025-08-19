from typing import Optional, Dict, Type
from datetime import datetime
from abc import ABC, abstractmethod
from ..builder import AppointmentBuilder
from .appointment_director import AppointmentDirector
from .strategy import (
    AppointmentActionStrategy,
    CompleteAppointmentStrategy,
    RescheduleStrategy,
    CancellationStrategy,
    NoShowStrategy,
    ReferralStrategy
)
from .repository import IAppointmentRepository, DjangoAppointmentRepository
from .observer import AppointmentObserver

class AppointmentComponentFactory:
    """Factory for creating and managing appointment-related components"""
    
    _instance = None
    _strategies: Dict[str, Type[AppointmentActionStrategy]] = {
        'complete': CompleteAppointmentStrategy,
        'reschedule': RescheduleStrategy,
        'cancel': CancellationStrategy,
        'no_show': NoShowStrategy,
        'refer': ReferralStrategy
    }
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize factory components"""
        self._builder = AppointmentBuilder()
        self._director = AppointmentDirector()
        self._repository = DjangoAppointmentRepository()
        self._observers = []
    
    @property
    def builder(self) -> AppointmentBuilder:
        """Get the appointment builder instance"""
        return self._builder
    
    @property
    def director(self) -> AppointmentDirector:
        """Get the appointment director instance"""
        return self._director
    
    @property
    def repository(self) -> IAppointmentRepository:
        """Get the appointment repository instance"""
        return self._repository
    
    def get_strategy(self, strategy_type: str) -> AppointmentActionStrategy:
        """Get a strategy instance by type"""
        strategy_class = self._strategies.get(strategy_type)
        if not strategy_class:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        return strategy_class()
    
    def register_observer(self, observer: AppointmentObserver):
        """Register an observer for appointment events"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def unregister_observer(self, observer: AppointmentObserver):
        """Unregister an observer"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self, appointment, event_type: str):
        """Notify all observers of an appointment event"""
        for observer in self._observers:
            observer.update(appointment, event_type)

class AppointmentService:
    """High-level service that uses the factory to manage appointments"""
    
    def __init__(self):
        self.factory = AppointmentComponentFactory()
    
    def create_appointment(self, appointment_type: str, **kwargs):
        """Create an appointment using the appropriate method"""
        if appointment_type == 'regular':
            appointment = self.factory.director.create_regular_checkup(
                kwargs['pet'],
                kwargs['vet'],
                kwargs['clinic_branch'],
                kwargs['date_time']
            )
        elif appointment_type == 'emergency':
            appointment = self.factory.director.create_emergency_appointment(
                kwargs['pet'],
                kwargs['clinic_branch'],
                kwargs['description']
            )
        elif appointment_type == 'follow_up':
            appointment = self.factory.director.create_follow_up(
                kwargs['original_appointment'],
                kwargs['follow_up_date']
            )
        elif appointment_type == 'vaccination':
            appointment = self.factory.director.create_vaccination(
                kwargs['pet'],
                kwargs['vet'],
                kwargs['clinic_branch'],
                kwargs['vaccine_type'],
                kwargs['date_time']
            )
        elif appointment_type == 'surgery':
            appointment = self.factory.director.create_surgery(
                kwargs['pet'],
                kwargs['vet'],
                kwargs['clinic_branch'],
                kwargs['surgery_type'],
                kwargs['date_time'],
                kwargs.get('pre_op_notes', '')
            )
        else:
            raise ValueError(f"Unknown appointment type: {appointment_type}")
        
        # Save the appointment
        saved_appointment = self.factory.repository.save(appointment)
        
        # Notify observers
        self.factory.notify_observers(saved_appointment, 'created')
        
        return saved_appointment
    
    def process_appointment(self, appointment_id: int, action: str, **kwargs):
        """Process an appointment using the appropriate strategy"""
        # Get the appointment
        appointment = self.factory.repository.get_by_id(appointment_id)
        if not appointment:
            raise ValueError(f"Appointment not found: {appointment_id}")
        
        # Get and execute the strategy
        strategy = self.factory.get_strategy(action)
        strategy.execute(appointment, **kwargs)
        
        # Save changes
        saved_appointment = self.factory.repository.save(appointment)
        
        # Notify observers
        self.factory.notify_observers(saved_appointment, action)
        
        return saved_appointment
    
    def get_vet_schedule(self, vet_id: int, start_date: datetime, end_date: datetime):
        """Get a vet's schedule for a date range"""
        return self.factory.repository.get_all_by_vet(vet_id, start_date, end_date)
    
    def get_available_slots(self, vet_id: int, date: datetime):
        """Get available appointment slots for a vet"""
        return self.factory.repository.get_available_slots(vet_id, date)
    
    def check_conflicts(self, vet_id: int, start_time: datetime, end_time: datetime):
        """Check for scheduling conflicts"""
        return self.factory.repository.get_conflicts(vet_id, start_time, end_time)
