from django.core.mail import send_mail
from django.conf import settings

class RecordObserver:
    def __init__(self):
        self.subscribers = []

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def notify(self, record):
        for callback in self.subscribers:
            callback(record)

class EmailNotificationObserver:
    def __call__(self, record):
        subject = f"New Medical Record Created - #{record.record_id}"
        message = (
            f"A new medical record has been created for pet: {record.pet.name}\n"
            f"Owner: {record.pet.owner.get_full_name()} ({record.pet.owner.phone})\n"
            f"Veterinarian: {record.vaterian.get_full_name()}\n"
            f"Visit Date: {record.visit_date}\n"
            f"Diagnosis: {record.diagnosis}\n"
            f"Treatment: {record.treatment}"
        )
        
        recipient_list = [record.pet.owner.email]  # Send to pet owner
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)