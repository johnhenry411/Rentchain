    
from django.urls import reverse

def get_dashboard_url(user):
    if user.is_authenticated:
        if user.role == 'client':
            return reverse('client_dashboard')  # Example name for client dashboard view
        elif user.role == 'landlord':
            return reverse('landlord_dashboard')  # Example name for landlord dashboard view
        elif user.role == 'admin':
            return reverse('admin_dashboard')  # Example name for admin dashboard view
    return reverse('login') 