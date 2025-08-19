from datetime import datetime, timedelta
from unittest.mock import Mock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from pets.models import Pet
from inventory.models import ClinicBranch
from accounts.models import Veterinarian
from ..models import Appointment
from ..patterns.vet_patterns.factory import AppointmentComponentFactory, AppointmentService
from ..patterns.vet_patterns.observer import (
    AppointmentObserver,
    VetScheduleObserver,
    EmergencyAlertObserver
)

class AppointmentIntegrationTest(TestCase):
    def setUp(self):
        # Create test client
        self.client = Client()
        
        # Create users
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
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
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
        
        # Initialize service
        self.service = AppointmentService()
        self.factory = AppointmentComponentFactory()
        
        # Setup test data
        self.tomorrow = datetime.now() + timedelta(days=1)
        self.next_week = datetime.now() + timedelta(days=7)

    def test_complete_appointment_workflow(self):
        """Test complete workflow from appointment creation to completion"""
        # 1. Create an appointment
        appointment = self.service.create_appointment(
            'regular',
            pet=self.pet,
            vet=self.vet,
            clinic_branch=self.clinic,
            date_time=self.tomorrow
        )
        
        # Verify initial state
        self.assertEqual(appointment.status, 'pending')
        
        # 2. Add observers
        schedule_observer = VetScheduleObserver()
        emergency_observer = EmergencyAlertObserver()
        self.factory.register_observer(schedule_observer)
        self.factory.register_observer(emergency_observer)
        
        # 3. Process appointment through different states
        # Reschedule
        new_time = self.tomorrow + timedelta(hours=2)
        updated_apt = self.service.process_appointment(
            appointment.id,
            'reschedule',
            new_datetime=new_time,
            reason='Schedule conflict'
        )
        self.assertEqual(updated_apt.date_time, new_time)
        
        # Complete with treatment
        completed_apt = self.service.process_appointment(
            appointment.id,
            'complete',
            treatment_notes='Routine checkup completed',
            diagnosis='Healthy',
            follow_up_date=self.next_week
        )
        self.assertEqual(completed_apt.status, 'completed')
        
        # Verify follow-up was created
        follow_up = self.factory.repository.get_all_by_pet(self.pet.id)[0]
        self.assertEqual(follow_up.service_type, 'follow_up')
        self.assertEqual(follow_up.date_time.date(), self.next_week.date())

    def test_emergency_workflow(self):
        """Test emergency appointment workflow"""
        # 1. Create emergency appointment
        emergency_apt = self.service.create_appointment(
            'emergency',
            pet=self.pet,
            clinic_branch=self.clinic,
            description='Sudden illness'
        )
        
        # Verify emergency status
        self.assertEqual(emergency_apt.status, 'urgent')
        self.assertEqual(emergency_apt.service_type, 'emergency')
        self.assertIsNotNone(emergency_apt.veterinarian)
        
        # 2. Process emergency
        completed_emergency = self.service.process_appointment(
            emergency_apt.id,
            'complete',
            treatment_notes='Emergency treatment provided',
            diagnosis='Food poisoning',
            follow_up_date=self.tomorrow
        )
        
        # Verify completion
        self.assertEqual(completed_emergency.status, 'completed')
        
        # Check follow-up creation
        follow_ups = self.factory.repository.get_all_by_pet(self.pet.id)
        self.assertTrue(any(apt.service_type == 'follow_up' for apt in follow_ups))

    def test_concurrent_appointment_handling(self):
        """Test handling of concurrent appointments and conflicts"""
        # Create multiple appointments for same time
        time_slot = self.tomorrow.replace(hour=10, minute=0)
        
        # First appointment
        apt1 = self.service.create_appointment(
            'regular',
            pet=self.pet,
            vet=self.vet,
            clinic_branch=self.clinic,
            date_time=time_slot
        )
        
        # Try to create conflicting appointment
        conflicting_slots = self.service.check_conflicts(
            self.vet.id,
            time_slot,
            time_slot + timedelta(minutes=30)
        )
        self.assertTrue(len(conflicting_slots) > 0)
        
        # Get available slots
        available_slots = self.service.get_available_slots(
            self.vet.id,
            time_slot.date()
        )
        
        # Verify the conflicting slot is not available
        self.assertNotIn(time_slot, available_slots)

    def test_appointment_modification_with_notifications(self):
        """Test appointment modifications with observer notifications"""
        # Create mock observers
        mock_observers = [
            Mock(spec=AppointmentObserver) for _ in range(3)
        ]
        for observer in mock_observers:
            self.factory.register_observer(observer)
        
        # Create and modify appointment
        appointment = self.service.create_appointment(
            'regular',
            pet=self.pet,
            vet=self.vet,
            clinic_branch=self.clinic,
            date_time=self.tomorrow
        )
        
        # Verify creation notification
        for observer in mock_observers:
            observer.update.assert_called_with(appointment, 'created')
            observer.update.reset_mock()
        
        # Modify appointment
        self.service.process_appointment(
            appointment.id,
            'reschedule',
            new_datetime=self.next_week,
            reason='Vet unavailable'
        )
        
        # Verify modification notification
        for observer in mock_observers:
            observer.update.assert_called_once()

    def tearDown(self):
        # Clean up created objects
        Appointment.objects.all().delete()
        Pet.objects.all().delete()
        Veterinarian.objects.all().delete()
        ClinicBranch.objects.all().delete()
        User.objects.all().delete()
