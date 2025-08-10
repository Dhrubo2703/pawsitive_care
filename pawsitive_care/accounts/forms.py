from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Veterinarian
from appoinments.models import ClinicBranch

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username','email','first_name','last_name','phone','address','password1','password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        """Save the user with role set to 'client' by default"""
        user = super().save(commit=False)
        user.role = 'client'  # All new registrations are clients
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'address']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class VeterinarianAdminForm(forms.ModelForm):
    class Meta:
        model = Veterinarian
        fields = ['clinic_branch', 'specialization', 'license_number', 
                 'years_of_experience', 'can_handle_emergencies', 'bio']
        widgets = {
            'clinic_branch': forms.Select(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'can_handle_emergencies': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Veterinarian
from appoinments.models import ClinicBranch

class VeterinarianForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='vet', veterinarian__isnull=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Veterinarian User'
    )
    
    clinic_branch = forms.ModelChoiceField(
        queryset=ClinicBranch.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    specialization = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    license_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    years_of_experience = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    can_handle_emergencies = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))

    class Meta:
        model = Veterinarian
        fields = ['user', 'clinic_branch', 'specialization', 'license_number', 
                 'years_of_experience', 'can_handle_emergencies', 'bio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update queryset to show username in dropdown
        self.fields['user'].label_from_instance = lambda obj: f"{obj.username} ({obj.get_full_name()})"
        
    def save(self, commit=True):
        veterinarian = super().save(commit=False)
        if commit:
            veterinarian.save()
        return veterinarian

        # Create the veterinarian profile
        veterinarian = super().save(commit=False)
        veterinarian.user = user
        veterinarian.clinic_branch = self.cleaned_data['clinic_branch']
        
        if commit:
            veterinarian.save()
            
        return veterinarian

class VeterinarianForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'address']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'vet'  # Set role to veterinarian
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user