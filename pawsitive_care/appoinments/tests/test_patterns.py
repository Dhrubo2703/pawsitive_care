import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from django.test import TestCase
from django.contrib.auth.models import User
from pets.models import Pet
from inventory.models import ClinicBranch
from accounts.models import Veterinarian
from ..models import Appointment
from ..patterns.vet_patterns.factory import AppointmentComponentFactory, AppointmentService
from ..patterns.vet_patterns.strategy import (
    CompleteAppointmentStrategy,
    RescheduleStrategy,
    CancellationStrategy
)
from ..patterns.vet_patterns.observer import AppointmentObserver
from ..patterns.builder import AppointmentBuilder

class AppointmentPatternsTest(TestCase):
    def setUp(self):
        # Create test users
        self.owner = User.objects.create_user(
            username='pet_owner',
            password='test123',
            email='owner@test.com'
        )
        self.vet_user = User.objects.create_user(
            username='vet',
            password='test123',
            email='vet@test.com'
        )
        
        # Create clinic branch
        self.clinic = ClinicBranch.objects.create(
            name='Test Clinic',
            address='123 Test St',
            phone='1234567890'
        )
        
        # Create veterinarian
        self.vet = Veterinarian.objects.create(
            user=self.vet_user,
            clinic_branch=self.clinic,
            specialization='General',
            can_handle_emergencies=True
        )
        
        # Create pet
        self.pet = Pet.objects.create(
            name='TestPet',
            species='Dog',
            breed='Mixed',
            owner=self.owner
        )
        
        # Initialize factory and service
        self.factory = AppointmentComponentFactory()
        self.service = AppointmentService()
        
        # Test appointment data
        self.appointment_time = datetime.now() + timedelta(days=1)

    def test_builder_pattern(self):
        """Test the AppointmentBuilder pattern"""
        builder = AppointmentBuilder()
        
        # Test building an appointment
        appointment = builder\
            .set_pet(self.pet)\
            .set_service('checkup')\
            .set_veterinarian(self.vet)\
            .set_datetime(self.appointment_time)\
            .set_clinic_branch(self.clinic)\
            .set_notes('Test appointment')\
            .build()
        
        # Verify all fields are set correctly
        self.assertEqual(appointment.pet, self.pet)
        self.assertEqual(appointment.service_type, 'checkup')
        self.assertEqual(appointment.veterinarian, self.vet)
        self.assertEqual(appointment.date_time, self.appointment_time)
        self.assertEqual(appointment.clinic_branch, self.clinic)
        self.assertEqual(appointment.notes, 'Test appointment')
        self.assertEqual(appointment.status, 'pending')

    def test_strategy_pattern(self):
        """Test the Strategy pattern implementations"""
        # Create a test appointment
        appointment = self.factory.director.create_regular_checkup(
            self.pet,
            self.vet,
            self.clinic,
            self.appointment_time
        )
        appointment.save()
        
        # Test Complete Strategy
        complete_strategy = CompleteAppointmentStrategy()
        complete_strategy.execute(appointment, 
                                treatment_notes='Test treatment',
                                diagnosis='Test diagnosis')
        self.assertEqual(appointment.status, 'completed')
        self.assertEqual(appointment.treatment_notes, 'Test treatment')
        
        # Test Reschedule Strategy
        new_time = self.appointment_time + timedelta(days=1)
        reschedule_strategy = RescheduleStrategy()
        reschedule_strategy.execute(appointment,
                                  new_datetime=new_time,
                                  reason='Test reschedule')
        self.assertEqual(appointment.date_time, new_time)
        
        # Test Cancel Strategy
        cancel_strategy = CancellationStrategy()
        cancel_strategy.execute(appointment,
                              reason='Test cancellation',
                              notify_client=False)
        self.assertEqual(appointment.status, 'cancelled')
        self.assertEqual(appointment.cancellation_reason, 'Test cancellation')

    def test_observer_pattern(self):
        """Test the Observer pattern"""
        # Create a mock observer
        mock_observer = Mock(spec=AppointmentObserver)
        self.factory.register_observer(mock_observer)
        
        # Create an appointment and verify observer was notified
        appointment = self.service.create_appointment(
            'regular',
            pet=self.pet,
            vet=self.vet,
            clinic_branch=self.clinic,
            date_time=self.appointment_time
        )
        
        # Verify observer was notified
        mock_observer.update.assert_called_once()
        args = mock_observer.update.call_args[0]
        self.assertEqual(args[0], appointment)
        self.assertEqual(args[1], 'created')

    def test_factory_and_service(self):
        """Test the Factory and Service patterns"""
        # Test creating different types of appointments
        
        # Regular appointment
        regular_apt = self.service.create_appointment(
            'regular',
            pet=self.pet,
            vet=self.vet,
            clinic_branch=self.clinic,
            date_time=self.appointment_time
        )
        self.assertEqual(regular_apt.service_type, 'regular_checkup')
        
        # Emergency appointment
        emergency_apt = self.service.create_appointment(
            'emergency',
            pet=self.pet,
            clinic_branch=self.clinic,
            description='Test emergency'
        )
        self.assertEqual(emergency_apt.service_type, 'emergency')
        self.assertEqual(emergency_apt.status, 'urgent')
        
        # Test appointment processing
        self.service.process_appointment(
            regular_apt.id,
            'complete',
            treatment_notes='Test treatment',
            diagnosis='Test diagnosis'
        )
        updated_apt = self.factory.repository.get_by_id(regular_apt.id)
        self.assertEqual(updated_apt.status, 'completed')

    def test_repository_pattern(self):
        """Test the Repository pattern"""
        # Create test appointments
        apt1 = self.service.create_appointment(
            'regular',
            pet=self.pet,
            vet=self.vet,
            clinic_branch=self.clinic,
            date_time=self.appointment_time
        )
        
        apt2 = self.service.create_appointment(
            'regular',
            pet=self.pet,
            vet=self.vet,
            clinic_branch=self.clinic,
            date_time=self.appointment_time + timedelta(days=1)
        )
        
        # Test repository methods
        repository = self.factory.repository
        
        # Test get_by_id
        retrieved_apt = repository.get_by_id(apt1.id)
        self.assertEqual(retrieved_apt, apt1)
        
        # Test get_all_by_vet
        vet_appointments = repository.get_all_by_vet(
            self.vet.id,
            datetime.now(),
            datetime.now() + timedelta(days=7)
        )
        self.assertEqual(len(vet_appointments), 2)
        
        # Test get_all_by_pet
        pet_appointments = repository.get_all_by_pet(self.pet.id)
        self.assertEqual(len(pet_appointments), 2)
        
        # Test get_available_slots
        slots = repository.get_available_slots(self.vet.id, self.appointment_time.date())
        self.assertTrue(len(slots) > 0)

    def tearDown(self):
        # Clean up created objects
        Appointment.objects.all().delete()
        Pet.objects.all().delete()
        Veterinarian.objects.all().delete()
        ClinicBranch.objects.all().delete()
        User.objects.all().delete()
