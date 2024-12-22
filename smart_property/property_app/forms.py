from django import forms
from .models import User,Property,PropertyImage,Proposal
from .models import Proposal, Contract
from datetime import date, timedelta
from django.contrib.auth.forms import AuthenticationForm

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['username','first_name','last_name', 'email', 'password', 'role']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match!")
class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A unique name to be used for transactions'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )
    
from .models import Profile

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture', 'phone_number', 'address']

from django import forms
from .models import Property

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'name',
            'description',
            'price',
            'location',
            'category',
            't_type',
            'number_of_units',
            'beds',
            'baths',
            'size',
            'status',
            'furnishing_status',
            'nearby_features',
            'utilities',
            'contact_number',
        ]

        
class PropertyImageForm(forms.ModelForm):
    class Meta:
        model = PropertyImage
        fields = ['image']
        
class ProposalForm(forms.ModelForm):
    # Adding fields that will be used for the contract
    lease_value = forms.DecimalField(
        max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Lease value'
        })
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date'
        }),
        initial=date.today
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date'
        }),
        initial=date.today() + timedelta(days=365)
    )

    class Meta:
        model = Proposal
        fields = ['proposed_price', 'message', 'lease_value', 'start_date', 'end_date']
        widgets = {
            'proposed_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Propose your price'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Leave a message (optional)',
                'rows': 4
            }),
        }

    def save(self, commit=True):
        # Save the Proposal instance first
        proposal = super().save(commit=False)
        
        if commit:
            proposal.save()  # Save the proposal instance

            # Create a corresponding Contract using form data
            Contract.objects.create(
                proposal=proposal,
                landlord=proposal.property.landlord,  # Derived from property
                client=proposal.proposer,            # Derived from the proposal
                property=proposal.property,
                lease_value=self.cleaned_data['lease_value'],
                start_date=self.cleaned_data['start_date'],
                end_date=self.cleaned_data['end_date']
            )
        return proposal
        
from django import forms
from .models import Wallet
from property_app.models import User

class WalletForm(forms.ModelForm):
    class Meta:
        model = Wallet
        fields = ['balance']
