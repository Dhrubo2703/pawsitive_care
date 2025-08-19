from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from accounts.models import Veterinarian
from datetime import datetime, timedelta
from django.contrib import messages
from accounts.decorators import vet_required
from ..patterns.vet_patterns.factory import AppointmentComponentFactory, AppointmentService
from ..models import Appointment

@login_required
@vet_required
def vet_dashboard_appointments(request):
    """Main view for vet's appointment dashboard"""
    service = AppointmentService()
    try:
        vet = request.user.veterinarian
    except Veterinarian.DoesNotExist:
        messages.error(request, "Veterinarian profile not found. Please contact an administrator.")
        return redirect('accounts:vet_dashboard')
    
    # Get date range for filtering
    today = timezone.now().date()
    date_filter = request.GET.get('date_filter', 'today')
    
    if date_filter == 'today':
        start_date = today
        end_date = today + timedelta(days=1)
    elif date_filter == 'week':
        start_date = today
        end_date = today + timedelta(days=7)
    elif date_filter == 'month':
        start_date = today
        end_date = today + timedelta(days=30)
    else:
        start_date = today
        end_date = today + timedelta(days=1)

    # Get appointments using our service
    appointments = service.get_vet_schedule(
        vet.id,
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time())
    )
    
    # Get emergency appointments for the clinic
    emergency_appointments = service.factory.repository.get_emergency_appointments(vet.clinic_branch.id)
    
    # Get overdue appointments
    overdue_appointments = service.factory.repository.get_overdue_appointments(vet.id)
    
    context = {
        'appointments': appointments,
        'emergency_appointments': emergency_appointments,
        'overdue_appointments': overdue_appointments,
        'date_filter': date_filter,
        'today': today,
    }
    
    return render(request, 'appointments/vet_dashboard/appointments.html', context)

@login_required
@vet_required
def complete_appointment(request, appointment_id):
    """Complete an appointment with treatment notes and diagnosis"""
    service = AppointmentService()
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        treatment_notes = request.POST.get('treatment_notes')
        diagnosis = request.POST.get('diagnosis')
        follow_up_date = request.POST.get('follow_up_date')
        
        try:
            if follow_up_date:
                follow_up_date = datetime.strptime(follow_up_date, '%Y-%m-%d').date()
            
            service.process_appointment(
                appointment_id,
                'complete',
                treatment_notes=treatment_notes,
                diagnosis=diagnosis,
                follow_up_date=follow_up_date
            )
            messages.success(request, 'Appointment completed successfully.')
            
        except Exception as e:
            messages.error(request, f'Error completing appointment: {str(e)}')
        
        return redirect('appointments:vet_dashboard_appointments')
    
    context = {
        'appointment': appointment,
        'today': timezone.now().date(),
    }
    return render(request, 'appointments/vet_dashboard/complete_appointment.html', context)

@login_required
@vet_required
def vet_reschedule_appointment(request, appointment_id):
    """Reschedule an appointment from vet dashboard"""
    service = AppointmentService()
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        new_date = request.POST.get('new_date')
        new_time = request.POST.get('new_time')
        reason = request.POST.get('reason')
        
        try:
            new_datetime = datetime.strptime(f"{new_date} {new_time}", '%Y-%m-%d %H:%M')
            
            service.process_appointment(
                appointment_id,
                'reschedule',
                new_datetime=new_datetime,
                reason=reason
            )
            messages.success(request, 'Appointment rescheduled successfully.')
            
        except Exception as e:
            messages.error(request, f'Error rescheduling appointment: {str(e)}')
        
        return redirect('appointments:vet_dashboard_appointments')
    
    # Get available slots for the selected date
    available_slots = service.get_available_slots(
        appointment.veterinarian.id,
        timezone.now().date()
    )
    
    context = {
        'appointment': appointment,
        'available_slots': available_slots,
        'today': timezone.now().date(),
    }
    return render(request, 'appointments/vet_dashboard/reschedule_appointment.html', context)

@login_required
@vet_required
def vet_cancel_appointment(request, appointment_id):
    """Cancel an appointment from vet dashboard"""
    service = AppointmentService()
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        notify_client = request.POST.get('notify_client') == 'on'
        
        try:
            service.process_appointment(
                appointment_id,
                'cancel',
                reason=reason,
                notify_client=notify_client
            )
            messages.success(request, 'Appointment cancelled successfully.')
            
        except Exception as e:
            messages.error(request, f'Error cancelling appointment: {str(e)}')
        
        return redirect('appointments:vet_dashboard_appointments')
    
    context = {
        'appointment': appointment,
    }
    return render(request, 'appointments/vet_dashboard/cancel_appointment.html', context)

@login_required
@vet_required
def mark_no_show(request, appointment_id):
    """Mark an appointment as no-show"""
    if request.method == 'POST':
        service = AppointmentService()
        notes = request.POST.get('notes', '')
        
        try:
            service.process_appointment(
                appointment_id,
                'no_show',
                notes=notes
            )
            messages.success(request, 'Appointment marked as no-show.')
            
        except Exception as e:
            messages.error(request, f'Error marking appointment as no-show: {str(e)}')
    
    return redirect('appointments:vet_dashboard_appointments')

@login_required
@vet_required
def refer_appointment(request, appointment_id):
    """Refer an appointment to another vet"""
    service = AppointmentService()
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        new_vet_id = request.POST.get('new_vet')
        reason = request.POST.get('reason')
        notes = request.POST.get('notes', '')
        
        try:
            from accounts.models import Veterinarian
            new_vet = get_object_or_404(Veterinarian, id=new_vet_id)
            
            service.process_appointment(
                appointment_id,
                'refer',
                new_vet=new_vet,
                reason=reason,
                notes=notes
            )
            messages.success(request, 'Appointment referred successfully.')
            
        except Exception as e:
            messages.error(request, f'Error referring appointment: {str(e)}')
        
        return redirect('appointments:vet_dashboard_appointments')
    
    from accounts.models import Veterinarian
    available_vets = Veterinarian.objects.exclude(id=appointment.veterinarian.id)
    
    context = {
        'appointment': appointment,
        'available_vets': available_vets,
    }
    return render(request, 'appointments/vet_dashboard/refer_appointment.html', context)

@login_required
@vet_required
def get_available_slots(request):
    """AJAX endpoint to get available slots for a date"""
    date_str = request.GET.get('date')
    vet_id = request.GET.get('vet_id')
    
    if not date_str or not vet_id:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        service = AppointmentService()
        slots = service.get_available_slots(int(vet_id), date)
        
        # Format slots for JSON response
        formatted_slots = [
            {
                'time': slot.strftime('%H:%M'),
                'display_time': slot.strftime('%I:%M %p')
            }
            for slot in slots
        ]
        
        return JsonResponse({'slots': formatted_slots})
        
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
