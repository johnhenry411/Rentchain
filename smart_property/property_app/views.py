from django.shortcuts import redirect,render
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import SignUpForm
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from .models import User, Property, Lease, Review

def role_required(role):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.role == role:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You are not authorized to access this page.")
        return _wrapped_view
    return decorator

@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('client'), name='dispatch')
class ClientDashboardView(TemplateView):
    template_name = 'client_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['leases'] = Lease.objects.filter(tenant=self.request.user)
        context['reviews'] = Review.objects.filter(tenant=self.request.user)
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('landlord'), name='dispatch')
class LandlordDashboardView(TemplateView):
    template_name = 'landlord_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['properties'] = Property.objects.filter(landlord=self.request.user)
        context['leases'] = Lease.objects.filter(property__landlord=self.request.user)
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('admin'), name='dispatch')
class AdminDashboardView(TemplateView):
    template_name = 'admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all()
        context['properties'] = Property.objects.all()
        context['leases'] = Lease.objects.all()
        context['reviews'] = Review.objects.all()
        return context


def client_signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Create the user object without saving to DB yet
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Set the password
            user.save()  # Save the user first

            user.setup_roles()  # Now call setup_roles() after saving the user

            return redirect('login')  # Redirect to login page after successful signup
    else:
        form = SignUpForm()
    
    return render(request, 'signup.html', {'form': form})



def role_based_redirect(user):
    if user.role == 'admin':
        return redirect('admin_dashboard')
    elif user.role == 'landlord':
        return redirect('landlord_dashboard')
    elif user.role == 'client':
        return redirect('client_dashboard')
    else:
        return HttpResponse("Unauthorized user", status=403)


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return role_based_redirect(user)  # Call the redirect function
        else:
            return HttpResponse("Invalid credentials")
    return render(request, 'login.html')


def home(request):
    tenant=Property.objects.all()
    return render(request, 'index.html',{'tenant':tenant})