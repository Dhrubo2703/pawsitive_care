from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Client URLs
    path('book/', views.book_appointment, name='book_appointment'),
    path('my-appointments/', views.client_appointments, name='client_appointments'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    
    # Vet URLs
    path('schedule/', views.vet_schedule, name='vet_schedule'),
    path('update-status/<int:appointment_id>/', views.update_appointment_status, name='update_status'),
    
    # Staff URLs
    path('calendar/', views.staff_calendar, name='staff_calendar'),
    path('manage/', views.manage_appointment, name='create_appointment'),
    path('manage/<int:appointment_id>/', views.manage_appointment, name='edit_appointment'),
    path('get-client-pets/<int:client_id>/', views.get_client_pets, name='get_client_pets'),
]
