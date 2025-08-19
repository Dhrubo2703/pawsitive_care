from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from datetime import datetime

from ..models import Appointment, ServiceType, ClinicBranch, AppointmentFeedback
from ..patterns.builder import AppointmentBuilder
from ..patterns.factory import get_appointment_factory
from ..patterns.repository import AppointmentRepository
from ..patterns.observer import AppointmentSubject, EmailNotificationObserver, ReminderObserver
from ..patterns.strategy import NotificationContext, EmailStrategy
from pets.models import Pet

User = get_user_model()

# Initialize observers
appointment_subject = AppointmentSubject()
appointment_subject.attach(EmailNotificationObserver())
appointment_subject.attach(ReminderObserver())

@login_required
def appointment_list(request):
    """View for listing appointments"""
    repository = AppointmentRepository()
    upcoming_appointments = repository.get_upcoming_appointments(request.user)
    past_appointments = repository.get_appointment_history(request.user)
    
    context = {
        'title': 'Appointments',
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
    }
    return render(request, 'appointments/appointment_list.html', context)

@login_required
def book_appointment(request):
    """View for booking new appointments"""
    if request.method == 'POST':
        # Create appointment using Builder pattern
        builder = AppointmentBuilder()
        
        try:
            appointment = builder\
                .set_pet(get_object_or_404(Pet, id=request.POST.get('pet')))\
                .set_service(get_object_or_404(ServiceType, id=request.POST.get('service_type')))\
                .set_veterinarian(get_object_or_404(User, id=request.POST.get('veterinarian')))\
                .set_datetime(datetime.strptime(request.POST.get('date_time'), '%Y-%m-%d %H:%M'))\
                .set_clinic_branch(get_object_or_404(ClinicBranch, id=request.POST.get('clinic_branch')))\
                .set_notes(request.POST.get('notes', ''))\
                .build()
            
            # Use Factory pattern to create specific appointment type
            factory = get_appointment_factory(appointment.service_type.name)
            # Create a clean dictionary with only the needed fields
            appointment_data = {
                'pet': appointment.pet,
                'service_type': appointment.service_type,
                'veterinarian': appointment.veterinarian,
                'date_time': appointment.date_time,
                'clinic_branch': appointment.clinic_branch,
                'notes': appointment.notes,
                'status': 'scheduled'  # Set initial status
            }
            appointment = factory.create_appointment(**appointment_data)
            
            # Notify observers
            appointment_subject.notify(appointment)
            
            messages.success(request, 'Appointment booked successfully!')
            return redirect('appointments:appointment_summary', appointment_id=appointment.id)
            
        except Exception as e:
            messages.error(request, f'Error booking appointment: {str(e)}')
            return redirect('appointments:book_appointment')
    
    # GET request - show booking form
    context = {
        'pets': Pet.objects.filter(owner=request.user),
        'services': ServiceType.objects.all(),
        'vets': User.objects.filter(groups__name='Veterinarian'),
        'branches': ClinicBranch.objects.filter(is_active=True),
    }
    return render(request, 'appointments/book_appointment.html', context)

@login_required
def appointment_summary(request, appointment_id):
    """View for appointment summary"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    return render(request, 'appointments/appointment_summary.html', {
        'appointment': appointment
    })

@login_required
def reschedule_appointment(request, appointment_id):
    """View for rescheduling appointments"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        try:
            new_datetime = datetime.strptime(request.POST.get('date_time'), '%Y-%m-%dT%H:%M')
            appointment.date_time = new_datetime
            appointment.save()
            
            # Notify observers about the change
            appointment_subject.notify(appointment)
            
            messages.success(request, 'Appointment rescheduled successfully!')
            return redirect('appointments:appointment_summary', appointment_id=appointment.id)
            
        except Exception as e:
            messages.error(request, f'Error rescheduling appointment: {str(e)}')
    
    return render(request, 'appointments/reschedule_appointment.html', {
        'appointment': appointment
    })

@login_required
@require_POST
def cancel_appointment(request, appointment_id):
    """View for canceling appointments"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    appointment.status = 'cancelled'
    appointment.save()
    
    # Notify observers about the cancellation
    appointment_subject.notify(appointment)
    
    messages.success(request, 'Appointment cancelled successfully!')
    return redirect('appointments:appointment_list')

@login_required
def submit_feedback(request, appointment_id):
    """View for submitting appointment feedback"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        feedback = AppointmentFeedback.objects.create(
            appointment=appointment,
            rating=request.POST.get('rating'),
            comments=request.POST.get('comments'),
            vet_rating=request.POST.get('vet_rating'),
            clinic_rating=request.POST.get('clinic_rating'),
            service_rating=request.POST.get('service_rating')
        )
        
        messages.success(request, 'Thank you for your feedback!')
        return redirect('appointments:appointment_list')
    
    return render(request, 'appointments/submit_feedback.html', {
        'appointment': appointment
    })

@login_required
def get_available_slots(request):
    """AJAX view for getting available appointment slots"""
    vet_id = request.GET.get('vet_id')
    date_str = request.GET.get('date')
    
    try:
        vet = User.objects.get(id=vet_id)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        repository = AppointmentRepository()
        available_slots = repository.get_available_slots(vet, date)
        
        return JsonResponse({
            'slots': [slot.strftime('%H:%M') for slot in available_slots]
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
