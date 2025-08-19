from django.contrib import admin
from .models import Appointment, AppointmentType

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('appointment_id', 'pet', 'vet', 'client', 'date', 'time', 'appointment_type', 'status')
    list_filter = ('status', 'appointment_type', 'date', 'vet')
    search_fields = ('pet__name', 'vet__username', 'client__username')
    ordering = ('-date', 'time')

@admin.register(AppointmentType)
class AppointmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_cost')
    search_fields = ('name',)
