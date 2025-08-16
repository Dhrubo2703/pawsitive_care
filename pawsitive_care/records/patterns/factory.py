from pets.models import Pet

# Abstract Creator
class MedicalRecordCreator:
    def create(self, form_data, user):
        raise NotImplementedError


# Concrete Creator 1 — new record
class NewMedicalRecordFactory:
    def create(self, form_data, user):
        pet = Pet.objects.get(id=form_data.get('pet'))
        return {
            'pet': pet,
            'vaterian': user,
            'visit_date': form_data.get('visit_date'),
            'treatment': form_data.get('treatment'),
            'prescription': form_data.get('prescription'),
            'vaccination_date': form_data.get('vaccination_date'),
            'diagnosis': form_data.get('diagnosis'),
            'notes': form_data.get('notes'),
            'created_at': form_data.get('created_at'),
        }


# Concrete Creator 2 — load existing record
class PreviousMedicalRecordFactory(MedicalRecordCreator):
    def create(self, form_data, user):
        record_id = form_data.get('record_id')
        record = PetsMedicalRecord.objects.get(pk=record_id)
        return {
            'pet': record.pet,
            'vaterian': user,  # Or keep original vet if needed
            'visit_date': record.visit_date,
            'treatment': record.treatment,
            'prescription': record.prescription,
            'vaccination_date': record.vaccination_date,
            'diagnosis': record.diagnosis,
            'notes': record.notes,
            'created_at': record.created_at,
        }

FACTORY_REGISTRY = {
    "new": NewMedicalRecordFactory(),
    "previous": PreviousMedicalRecordFactory()
}

def get_factory(mode: str) -> MedicalRecordCreator:
    factory = FACTORY_REGISTRY.get(mode)
    if not factory:
        raise ValueError(f"Unknown record creation mode: {mode}")
    return factory
