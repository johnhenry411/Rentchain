from django.urls import reverse

def dashboard_url(request):
    if request.user.is_authenticated:
        if request.user.role == 'client':
            return {'dashboard_url': reverse('client_dashboard')}
        elif request.user.role == 'landlord':
            return {'dashboard_url': reverse('landlord_dashboard')}
        elif request.user.role == 'admin':
            return {'dashboard_url': reverse('admin_dashboard')}
    return {'dashboard_url': None}
