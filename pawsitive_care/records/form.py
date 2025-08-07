from django import forms
from .models import PetsMedicalRecord

class PetsMedicalRecordForm(forms.ModelForm):
    class Meta:
        model = PetsMedicalRecord
        fields = ['visit_date', 'treatment', 'prescription', 'vaccination_date', 'diagnosis', 'notes']
        widgets = {
            'visit_date': forms.DateInput(attrs={'type': 'date'}),
            'vaccination_date': forms.DateInput(attrs={'type': 'date'}),
        }
