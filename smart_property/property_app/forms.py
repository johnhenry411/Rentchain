from django import forms
from .models import User,Property,PropertyImage,Proposal

from django.contrib.auth.forms import AuthenticationForm

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match!")
class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )
    
from .models import Profile

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture', 'phone_number', 'address']

class PropertyForm(forms.ModelForm):
    class Meta:
        model=Property
        fields = ['name', 'description', 'price', 'location','category','t_type','number_of_units','beds','baths','size']
        
class PropertyImageForm(forms.ModelForm):
    class Meta:
        model = PropertyImage
        fields = ['image']
        
class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = ['proposed_price', 'message']
        widgets = {
            'proposed_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Propose your price'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Leave a message (optional)'}),
        }