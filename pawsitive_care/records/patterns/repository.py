from records.models import PetsMedicalRecord

class MedicalRecordRepository:
    def get_all_records(self):
        return PetsMedicalRecord.objects.select_related('pet', 'vaterian').all()

    def get_record_by_id(self, record_id, user):
        return PetsMedicalRecord.objects.get(id=record_id, pet__owner=user)

    def get_records_by_owner(self, user):
        return PetsMedicalRecord.objects.filter(pet__owner=user).select_related('pet', 'vaterian')

    def create_record(self, record_data):
        return PetsMedicalRecord.objects.create(**record_data)
    def get_records_by_pet_id(self, pet_id):
        return PetsMedicalRecord.objects.filter(pet_id=pet_id).select_related('pet', 'vaterian')
