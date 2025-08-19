from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Client-facing views
    path('', views.appointment_list, name='appointment_list'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('summary/<int:appointment_id>/', views.appointment_summary, name='appointment_summary'),
    path('reschedule/<int:appointment_id>/', views.reschedule_appointment, name='reschedule_appointment'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('feedback/<int:appointment_id>/', views.submit_feedback, name='submit_feedback'),
    
    # Vet dashboard appointment views
    path('vet/dashboard/', views.vet_dashboard_appointments, name='vet_dashboard_appointments'),
    path('vet/appointment/<int:appointment_id>/complete/', views.complete_appointment, name='complete_appointment'),
    path('vet/appointment/<int:appointment_id>/reschedule/', views.vet_reschedule_appointment, name='vet_reschedule_appointment'),
    path('vet/appointment/<int:appointment_id>/cancel/', views.vet_cancel_appointment, name='vet_cancel_appointment'),
    path('vet/appointment/<int:appointment_id>/no-show/', views.mark_no_show, name='mark_no_show'),
    path('vet/appointment/<int:appointment_id>/refer/', views.refer_appointment, name='refer_appointment'),
    
    # AJAX endpoints
    path('get-available-slots/', views.get_available_slots, name='get_available_slots'),
]
