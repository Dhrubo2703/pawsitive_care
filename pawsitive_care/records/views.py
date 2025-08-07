from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from pets.models import Pet
from .models import PetsMedicalRecord
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from .patterns.factory import MedicalRecordFactory
from .patterns.repository import MedicalRecordRepository
from .patterns.observer import RecordObserver
from .form import PetsMedicalRecordForm
from django.utils import timezone

User = get_user_model()

repository = MedicalRecordRepository()
factory = MedicalRecordFactory()
observer = RecordObserver()

@login_required
def add_record(request):
    if request.method == 'POST':
        try:
            record_data = factory.create(request.POST, request.user)
            record = repository.create_record(record_data)
            observer.notify(record)

            return render(request, 'add_record.html', {
                'success': True,
                'pets': Pet.objects.all(),
                'user': request.user
            })

        except Pet.DoesNotExist:
            messages.error(request, "Selected pet does not exist.")
        except Exception as e:
            messages.error(request, f"Error adding record: {str(e)}")

    return render(request, 'add_record.html', {
        'pets': Pet.objects.all(),
        'user': request.user
    })

@login_required
def view_records(request):
    pet_id = request.GET.get('pet_id')
    if pet_id:
        records = PetsMedicalRecord.objects.filter(pet__id=pet_id)
    else:
        records = PetsMedicalRecord.objects.all()

    context = {
        'records': records,
        'title': 'All Medical Records',
    }
    return render(request, 'view_records.html', context)


@login_required
def my_pet_records(request):
    records = repository.get_records_by_owner(request.user)
    return render(request, 'my_pet_records.html', {
        'records': records,
        'title': 'My Pet Records'
    })

@login_required
def record_detail(request, record_id):
    record = get_object_or_404(PetsMedicalRecord, id=record_id, pet__owner=request.user)
    return render(request, 'record_detail.html', {
        'record': record,
        'title': 'Record Details'
    })


#record detail

@login_required
def record_detail(request, record_id):
    record = get_object_or_404(PetsMedicalRecord, pk=record_id)

    # Get primary photo or None
    primary_photo = record.pet.photos.filter(is_primary=True).first()

    user = request.user
    is_veterian = record.vaterian == user
    is_staff = user.is_staff
    is_client = not is_veterian and not is_staff  # Assuming clients are neither staff nor veterinarians

    context = {
        'record': record,
        'primary_photo': primary_photo,
        'title': 'Record Details',
        'is_veterian': is_veterian,
        'is_staff': is_staff,
        'is_client': is_client,
        'now': timezone.now(),
    }
    return render(request, 'record_detail.html', context)

@login_required
def update_record(request, record_id):
    record = get_object_or_404(PetsMedicalRecord, record_id=record_id)

    if record.vaterian != request.user:
        return HttpResponseForbidden("You are not allowed to edit this record.")

    if request.method == 'POST':
        form = PetsMedicalRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('records:record_detail', record_id=record.record_id)  # Use record.record_id here
    else:
        form = PetsMedicalRecordForm(instance=record)

    return render(request, 'update_record.html', {'form': form, 'record': record})


@login_required
def delete_record(request, record_id):
    record = get_object_or_404(PetsMedicalRecord, record_id=record_id)

    if request.user != record.vaterian and not request.user.is_staff:
        return HttpResponseForbidden("You are not allowed to delete this record.")

    if request.method == 'POST':
        record.delete()
        messages.success(request, "Record deleted successfully.")
        return redirect('records:view_records')

    return render(request, 'confirm_delete.html', {'record': record})