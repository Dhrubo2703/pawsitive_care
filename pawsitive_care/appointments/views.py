from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from pets.models import Pet  # Add this import
from datetime import datetime, timedelta

from accounts.decorators import client_required, vet_required, staff_required
from .patterns.factories import AppointmentFactory
from .patterns.repositories import AppointmentRepository
from .patterns.scheduler import AppointmentScheduler
from .patterns.views import DayViewStrategy, WeekViewStrategy, MonthViewStrategy
from .models import Appointment
from pets.models import Pet

# Client Views
@login_required
@client_required
def book_appointment(request):
    """Allow clients to book new appointments"""
    if request.method == 'POST':
        try:
            # Get the Pet and Vet instances
            pet_id = request.POST.get('pet')
            vet_id = request.POST.get('vet')
            
            pet = Pet.objects.get(id=pet_id)
            User = get_user_model()
            vet = User.objects.get(id=vet_id)
            
            appointment_data = {
                'pet': pet,  # Pass the Pet instance
                'vet': vet,  # Pass the User (vet) instance
                'client': request.user,
                'date': request.POST.get('date'),
                'time': request.POST.get('time'),
                'appointment_type': request.POST.get('appointment_type', 'GENERAL'),
                'notes': request.POST.get('notes', '')
            }
            
            appointment = AppointmentFactory.create_appointment(appointment_data)
            
            if appointment:
                messages.success(request, 'Appointment booked successfully!')
                return redirect('appointments:client_appointments')
            else:
                messages.error(request, 'Selected time slot is not available.')
        except Exception as e:
            messages.error(request, f'Error booking appointment: {str(e)}')
    
    try:
        # Get user's pets for the form
        pets = Pet.objects.filter(owner=request.user)
        
        # Get all veterinarians
        User = get_user_model()
        vets = User.objects.filter(role='vet', is_active=True)
        
        return render(request, 'appointments/book_appointment.html', {
            'pets': pets,
            'vets': vets,
            'today': timezone.now().date(),
            'appointment_types': Appointment.APPOINTMENT_TYPES
        })
    except Exception as e:
        messages.error(request, f'Error loading form: {str(e)}')
        return redirect('accounts:client_dashboard')

@login_required
@client_required
def client_appointments(request):
    """View client's appointments"""
    appointments = AppointmentRepository.get_client_appointments(request.user)
    return render(request, 'appointments/client_appointments.html', {
        'appointments': appointments
    })

@login_required
@client_required
def cancel_appointment(request, appointment_id):
    """Cancel a client's appointment"""
    try:
        # Get the appointment and verify ownership
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
        
        if appointment.client != request.user:
            messages.error(request, 'You can only cancel your own appointments.')
            return redirect('appointments:client_appointments')
            
        if appointment.status != 'SCHEDULED':
            messages.error(request, 'Only scheduled appointments can be cancelled.')
            return redirect('appointments:client_appointments')
        
        # Delete the appointment
        appointment.delete()
        messages.success(request, 'Your appointment has been cancelled successfully.')
        
    except Exception as e:
        messages.error(request, f'Error cancelling appointment: {str(e)}')
    
    return redirect('appointments:client_appointments')

# Vet Views
@login_required
@vet_required
def vet_schedule(request):
    """View vet's schedule"""
    view_type = request.GET.get('view', 'day')
    date_str = request.GET.get('date')
    
    try:
        if not date_str:
            selected_date = timezone.now().date()
        else:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.now().date()
    
    # Get appointments based on view type
    if view_type == 'day':
        appointments = Appointment.objects.filter(
            vet=request.user,
            date=selected_date,
            status='SCHEDULED'
        ).select_related('pet', 'client').order_by('time')
        prev_date = selected_date - timedelta(days=1)
        next_date = selected_date + timedelta(days=1)
    elif view_type == 'week':
        week_start = selected_date - timedelta(days=selected_date.weekday())
        week_end = week_start + timedelta(days=6)
        appointments = Appointment.objects.filter(
            vet=request.user,
            date__range=[week_start, week_end],
            status='SCHEDULED'
        ).select_related('pet', 'client').order_by('date', 'time')
        prev_date = selected_date - timedelta(days=7)
        next_date = selected_date + timedelta(days=7)
    else:  # month view
        appointments = Appointment.objects.filter(
            vet=request.user,
            date__year=selected_date.year,
            date__month=selected_date.month,
            status='SCHEDULED'
        ).select_related('pet', 'client').order_by('date', 'time')
        prev_date = (selected_date.replace(day=1) - timedelta(days=1)).replace(day=1)
        next_date = (selected_date.replace(day=28) + timedelta(days=4)).replace(day=1)
    
    return render(request, 'appointments/vet_schedule.html', {
        'appointments': appointments,
        'view_type': view_type,
        'current_date': selected_date,
        'prev_date': prev_date,
        'next_date': next_date,
        'today': timezone.now().date()
    })

@login_required
def update_appointment_status(request, appointment_id):
    """Update appointment status or delete appointment"""
    if request.method == 'POST':
        status = request.POST.get('status')
        try:
            appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
            
            # For client cancellations
            if request.user.role == 'client':
                if appointment.client != request.user:
                    messages.error(request, 'You can only cancel your own appointments.')
                    return redirect('appointments:client_appointments')
                
                if status == 'CANCELLED':
                    # Delete the appointment for client cancellations
                    appointment.delete()
                    messages.success(request, 'Your appointment has been cancelled successfully.')
                    return redirect('appointments:client_appointments')
            
            # For vet/staff updates
            elif request.user.role in ['vet', 'staff']:
                if status == 'COMPLETED':
                    appointment.status = 'COMPLETED'
                    messages.success(request, 'Appointment marked as completed.')
                elif status == 'PENDING':
                    appointment.status = 'PENDING'
                    messages.warning(request, 'Appointment marked as pending reassignment.')
                else:
                    messages.error(request, 'Invalid status update requested.')
                    return redirect('appointments:staff_calendar')
                
                appointment.save()
            else:
                messages.error(request, 'You do not have permission to update appointments.')
                return redirect('appointments:client_appointments')
                
        except Appointment.DoesNotExist:
            messages.error(request, 'Appointment not found.')
        except Exception as e:
            messages.error(request, f'Error updating appointment: {str(e)}')
    
    # Redirect based on user role
    if request.user.role == 'client':
        return redirect('appointments:client_appointments')
    elif request.user.role == 'vet':
        return redirect('appointments:vet_schedule')
    else:
        return redirect('appointments:staff_calendar')
    
    # Return to appropriate view based on user role
    if request.user.role == 'client':
        return redirect('appointments:client_appointments')
    elif request.user.role == 'vet':
        return redirect('appointments:vet_schedule')
    else:
        return redirect('appointments:staff_calendar')

# Staff Views
@login_required
@staff_required
def staff_calendar(request):
    """View and manage all appointments"""
    view_type = request.GET.get('view', 'day')
    date_str = request.GET.get('date', timezone.now().strftime('%Y-%m-%d'))
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.now().date()
    
    # Get all appointments based on view type
    # Get pending appointments (these are shown regardless of date)
    pending_appointments = Appointment.objects.filter(
        status='PENDING'
    ).select_related('pet', 'vet', 'client').order_by('date', 'time')

    # Get all appointments based on view type
    if view_type == 'day':
        all_appointments = Appointment.objects.filter(
            date=selected_date
        ).select_related('pet', 'vet', 'client').order_by('time')
        prev_date = selected_date - timedelta(days=1)
        next_date = selected_date + timedelta(days=1)
    elif view_type == 'week':
        week_start = selected_date - timedelta(days=selected_date.weekday())
        week_end = week_start + timedelta(days=6)
        all_appointments = Appointment.objects.filter(
            date__range=[week_start, week_end]
        ).select_related('pet', 'vet', 'client').order_by('date', 'time')
        prev_date = selected_date - timedelta(days=7)
        next_date = selected_date + timedelta(days=7)
    else:  # month view
        all_appointments = Appointment.objects.filter(
            date__year=selected_date.year,
            date__month=selected_date.month
        ).select_related('pet', 'vet', 'client').order_by('date', 'time')
        prev_date = (selected_date.replace(day=1) - timedelta(days=1)).replace(day=1)
        next_date = (selected_date.replace(day=28) + timedelta(days=4)).replace(day=1)
    
    # Get all veterinarians for filtering
    User = get_user_model()
    vets = User.objects.filter(role='vet', is_active=True)
    
    return render(request, 'appointments/staff_calendar.html', {
        'all_appointments': all_appointments,
        'pending_appointments': pending_appointments,
        'view_type': view_type,
        'current_date': selected_date,
        'prev_date': prev_date,
        'next_date': next_date,
        'today': timezone.now().date(),
        'vets': vets
    })

@login_required
@staff_required
def manage_appointment(request, appointment_id=None):
    """Create or edit appointments"""
    appointment = None
    if appointment_id:
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    
    if request.method == 'POST':
        try:
            User = get_user_model()
            
            if appointment:
                # For existing appointments (reassignment), update vet, date and time
                vet = User.objects.get(id=request.POST.get('vet'))
                new_date = request.POST.get('date')
                new_time = request.POST.get('time')
                
                # Check if the new time slot is available
                existing_appointment = Appointment.objects.filter(
                    vet=vet,
                    date=new_date,
                    time=new_time
                ).exclude(appointment_id=appointment.appointment_id).first()
                
                if existing_appointment:
                    messages.error(request, 'Selected time slot is not available for this veterinarian.')
                    return redirect('appointments:staff_calendar')
                
                # Update appointment details
                appointment.vet = vet
                appointment.date = new_date
                appointment.time = new_time
                
                # If appointment was pending and is being reassigned, mark it as scheduled
                if appointment.status == 'PENDING':
                    appointment.status = 'SCHEDULED'
                
                appointment.save()
                messages.success(request, 'Appointment reassigned successfully!')
                return redirect('appointments:staff_calendar')
            
            # For new appointments, we need all the data
            pet = Pet.objects.get(id=request.POST.get('pet'))
            vet = User.objects.get(id=request.POST.get('vet'))
            client = User.objects.get(id=request.POST.get('client'))
            
            # Prepare appointment data
            appointment_data = {
                'pet': pet,
                'vet': vet,
                'client': client,
                'date': request.POST.get('date'),
                'time': request.POST.get('time'),
                'notes': request.POST.get('notes', ''),
            }
            
            # Create new appointment
            appointment = AppointmentFactory.create_appointment(appointment_data)
            if appointment:
                messages.success(request, 'Appointment created successfully!')
            else:
                messages.error(request, 'Selected time slot is not available.')
            
            return redirect('appointments:staff_calendar')
            
        except Exception as e:
            messages.error(request, f'Error managing appointment: {str(e)}')
    
    try:
        # Get all active clients and vets
        User = get_user_model()
        clients = User.objects.filter(role='client', is_active=True)
        vets = User.objects.filter(role='vet', is_active=True)
        
        context = {
            'clients': clients,
            'vets': vets,
            'today': timezone.now().date(),
        }
        
        if appointment:
            context.update({
                'appointment': appointment,
                'selected_client': appointment.client,
                'selected_pet': appointment.pet,
                'client_pets': Pet.objects.filter(owner=appointment.client),
            })
        
        return render(request, 'appointments/manage_appointment.html', context)
    except Exception as e:
        messages.error(request, f'Error loading appointment form: {str(e)}')
        return redirect('appointments:staff_calendar')
    
    try:
        # Get all active clients and vets
        User = get_user_model()
        clients = User.objects.filter(role='client', is_active=True)
        vets = User.objects.filter(role='vet', is_active=True)
        
        context = {
            'clients': clients,
            'vets': vets,
            'today': timezone.now().date(),
        }
        
        if appointment:
            context.update({
                'appointment': appointment,
                'selected_client': appointment.client,
                'selected_pet': appointment.pet,
                'client_pets': Pet.objects.filter(owner=appointment.client),
            })
        
        return render(request, 'appointments/manage_appointment.html', context)
    except Exception as e:
        messages.error(request, f'Error loading appointment form: {str(e)}')
        return redirect('appointments:staff_calendar')


@login_required
@staff_required
def get_client_pets(request, client_id):
    """AJAX endpoint to get a client's pets"""
    try:
        pets = Pet.objects.filter(owner_id=client_id).values('id', 'name', 'species')
        return JsonResponse({'pets': list(pets)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
