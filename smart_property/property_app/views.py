from django.shortcuts import redirect,render,get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import SignUpForm
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from .models import User,Lease,Property, PropertyImage
from property_app.utils import get_dashboard_url
from .forms import ProfileUpdateForm,PropertyForm, PropertyImageForm
from django.forms import modelformset_factory
from django.views import View
from django.contrib import messages
from django.db.models import Prefetch

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


from django.shortcuts import render, redirect
from django.urls import reverse

from .utils import get_dashboard_url

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            dashboard_url = get_dashboard_url(user)
            return render(request, 'base.html', {'dashboard_url': dashboard_url})
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')



def home(request):
    property_images = PropertyImage.objects.all()
    units= Property.objects.prefetch_related(
        Prefetch('images', queryset=PropertyImage.objects.order_by('uploaded_at'))
    )
    categories = Property.CATEGORY_CHOICES
    properties_by_category = {
        category[1]: Property.objects.filter(category=category[0]).prefetch_related('images')
        for category in categories
    }
    return render(request, 'index.html', {'property_images': property_images, 'properties_by_category': properties_by_category,'units':units})

def base_page(request):
    from property_app.utils import get_dashboard_url
    context = {
        'dashboard_url': get_dashboard_url(request.user) if request.user.is_authenticated else None
    }
    return render(request, 'base.html', context)

@login_required
def update_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')  
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, 'update_profile.html', {'form': form})

@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('landlord'), name='dispatch')
class LandlordDashboardView(View):
    
    def get(self, request, *args, **kwargs):
        if getattr(request.user, 'role', None) != 'landlord':
            return redirect('login')

        properties = Property.objects.filter(landlord=request.user)
        PropertyImageFormSet = modelformset_factory(PropertyImage, form=PropertyImageForm, extra=3)

        property_form = PropertyForm()
        image_formset = PropertyImageFormSet(queryset=PropertyImage.objects.none())

        return render(request, 'landlord_dashboard.html', {
            'properties': properties,
            'property_form': property_form,
            'image_formset': image_formset,
        })

    def post(self, request, *args, **kwargs):
        # Check if the user is a landlord
        if getattr(request.user, 'role', None) != 'landlord':
            return redirect('login')

        PropertyImageFormSet = modelformset_factory(PropertyImage, form=PropertyImageForm, extra=3)
        property_form = PropertyForm(request.POST)
        image_formset = PropertyImageFormSet(request.POST, request.FILES, queryset=PropertyImage.objects.none())

        if property_form.is_valid() and image_formset.is_valid():
            # Save the property instance
            property_instance = property_form.save(commit=False)
            property_instance.landlord = request.user
            property_instance.save()

            # Save the images
            for form in image_formset:
                if form.cleaned_data and form.cleaned_data.get('image'):
                    image = form.save(commit=False)
                    image.property = property_instance
                    image.save()

            messages.success(request, "Property added successfully!")
            return redirect('landlord_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")

        properties = Property.objects.filter(landlord=request.user)
        return render(request, 'landlord_dashboard.html', {
            'properties': properties,
            'property_form': property_form,
            'image_formset': image_formset,
        })

# Edit Property View
@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('landlord'), name='dispatch')
class PropertyEditView(View):
    def get(self, request, property_id, *args, **kwargs):
        property_instance = get_object_or_404(Property, pk=property_id, landlord=request.user)
        property_form = PropertyForm(instance=property_instance)
        PropertyImageFormSet = modelformset_factory(PropertyImage, form=PropertyImageForm, extra=3)
        image_formset = PropertyImageFormSet(queryset=PropertyImage.objects.filter(property=property_instance))

        return render(request, 'edit_property.html', {
            'property_form': property_form,
            'image_formset': image_formset,
            'property_instance': property_instance
        })

    def post(self, request, property_id, *args, **kwargs):
        property_instance = get_object_or_404(Property, pk=property_id, landlord=request.user)
        property_form = PropertyForm(request.POST, instance=property_instance)
        PropertyImageFormSet = modelformset_factory(PropertyImage, form=PropertyImageForm, extra=3)
        image_formset = PropertyImageFormSet(request.POST, request.FILES, queryset=PropertyImage.objects.filter(property=property_instance))

        if property_form.is_valid() and image_formset.is_valid():
            property_instance = property_form.save(commit=False)
            property_instance.save()

            for form in image_formset:
                if form.cleaned_data and form.cleaned_data.get('image'):
                    image = form.save(commit=False)
                    image.property = property_instance
                    image.save()

            messages.success(request, "Property updated successfully!")
            return redirect('landlord_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")

        return render(request, 'edit_property.html', {
            'property_form': property_form,
            'image_formset': image_formset,
            'property_instance': property_instance
        })


# Delete Property View
class PropertyDeleteView(View):
    def post(self, request, property_id, *args, **kwargs):
        property_instance = get_object_or_404(Property, pk=property_id, landlord=request.user)
        property_instance.delete()
        messages.success(request, "Property deleted successfully!")
        return HttpResponseRedirect(reverse('landlord_dashboard'))