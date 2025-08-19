from django.core.management.base import BaseCommand
from appointments.models import Appointment

class Command(BaseCommand):
    help = 'Deletes all appointments'

    def handle(self, *args, **kwargs):
        Appointment.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted all appointments'))
