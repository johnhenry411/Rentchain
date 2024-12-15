from django.shortcuts import redirect,render,get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import SignUpForm,WalletForm
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from .models import User,Lease,Property, PropertyImage, Proposal,Transaction,Wallet
from property_app.utils import get_dashboard_url
from .forms import ProfileUpdateForm,PropertyForm, PropertyImageForm,ProposalForm  
from django.forms import modelformset_factory
from django.views import View
from django.contrib import messages
from django.db.models import Prefetch
from decimal import Decimal
import uuid
from django.db.models import Q

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
    template_name = 'client_dashboard.html'  # Fixed typo in 'template_name'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['leases'] = Lease.objects.filter(tenant=self.request.user)
        # context['reviews'] = Review.objects.filter(tenant=self.request.user)
        context['proposals'] = Proposal.objects.filter(proposer=self.request.user).select_related('property')
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
    properties = Property.objects.all()
    for property in properties:
        print(property.id) 
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
        # Fetch landlord properties and proposals
        properties = Property.objects.filter(landlord=request.user)
        proposals = Proposal.objects.filter(property__in=properties).select_related('proposer', 'property')

        # Create property image formset
        PropertyImageFormSet = modelformset_factory(PropertyImage, form=PropertyImageForm, extra=3)
        property_form = PropertyForm()
        image_formset = PropertyImageFormSet(queryset=PropertyImage.objects.none())

        return render(request, 'landlord_dashboard.html', {
            'properties': properties,
            'proposals': proposals,
            'property_form': property_form,
            'image_formset': image_formset,
        })

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        print(f"DEBUG: Action received in POST: {action}")  # Debugging
        if action == 'proposal_response':
                return self.handle_proposal_response(request)
        elif action == 'add_property':
                return self.handle_add_property(request)
        return redirect('landlord_dashboard')


    def handle_proposal_response(self, request):
        print("DEBUG: handle_proposal_response called.")
        proposal_id = request.POST.get('proposal_id')
        response_action = request.POST.get('response_action')
        response_message = request.POST.get('response_message', '')

        print(f"DEBUG: Proposal ID: {proposal_id}, Action: {response_action}, Response: {response_message}")

        proposal = get_object_or_404(Proposal, id=proposal_id)

        if response_action == 'accept':
                proposal.status = 'accepted'
        elif response_action == 'reject':
                proposal.status = 'rejected'

        proposal.landlord_response = response_message
        proposal.save()

        messages.success(request, f"Proposal has been {response_action}ed successfully.")
        return HttpResponseRedirect(request.path)






    def handle_add_property(self, request):
        # Initialize forms
        PropertyImageFormSet = modelformset_factory(PropertyImage, form=PropertyImageForm, extra=3)
        property_form = PropertyForm(request.POST)
        image_formset = PropertyImageFormSet(request.POST, request.FILES, queryset=PropertyImage.objects.none())

        if property_form.is_valid() and image_formset.is_valid():
            # Save property
            property_instance = property_form.save(commit=False)
            property_instance.landlord = request.user
            property_instance.save()

            # Save associated images
            for form in image_formset:
                if form.cleaned_data and form.cleaned_data.get('image'):
                    image = form.save(commit=False)
                    image.property = property_instance
                    image.save()

            messages.success(request, "Property added successfully!")
            return redirect('landlord_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")

        # If invalid, re-render with errors
        properties = Property.objects.filter(landlord=request.user)
        proposals = Proposal.objects.filter(property__in=properties).select_related('proposer', 'property')
        return render(request, 'landlord_dashboard.html', {
            'properties': properties,
            'proposals': proposals,
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
    
def property_detail(request, id):
    property = get_object_or_404(Property, id=id)
    return render(request, 'property_detail.html', {'property': property})

def submit_proposal(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    if request.method == 'POST':
        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.property = property
            proposal.proposer = request.user
            proposal.save()
            return redirect('property_detail', id=property.id)
    else:
        form = ProposalForm()
    return render(request, 'submit_proposal.html', {'form': form, 'property': property})

def accept_proposal(request, proposal_id):
    proposal = get_object_or_404(Proposal, id=proposal_id)
    
    proposal.status = 'accepted'
    
    proposal.sign_contract()
    
    # Save the proposal
    proposal.save()

    # Redirect to the contract view
    return redirect('view_contract', proposal_id=proposal.id)

def view_contract(request, proposal_id):
    proposal = get_object_or_404(Proposal, id=proposal_id)

    # Call sign_contract if signatures are missing
    if not proposal.client_signature or not proposal.landlord_signature:
        proposal.sign_contract() 

    # Refresh from database to ensure data consistency
    proposal.refresh_from_db()

    property = proposal.property
    landlord = property.landlord
    client = proposal.proposer

    # Ensure the logged-in user is either the landlord or the client involved
    if request.user != landlord and request.user != client:
        return HttpResponseForbidden("You are not authorized to view this contract.")

    # Prepare contract data
    context = {
        'property': property,
        'landlord': landlord,
        'client': client,
        'proposal': proposal,
        'lease_value': proposal.proposed_price,
    }

    return render(request, 'contract.html', context)


@login_required
def initiate_transaction(request):
    if request.method == 'POST':
        receiver_username = request.POST.get('receiver')
        try:
            amount = Decimal(request.POST.get('amount'))
            if amount <= 0:
                raise ValueError("Invalid transaction amount.")
        except (ValueError, TypeError):
            return render(request, 'transaction_status.html', {
                'message': "Transaction Failed: Invalid amount.",
                'transaction': None
            })

        # Get password confirmation from user
        password = request.POST.get('password')
        
        # Check if the password matches the user's actual password
        user = authenticate(username=request.user.username, password=password)
        if not user:
            return render(request, 'transaction_status.html', {
                'message': "Transaction Failed: Incorrect password. Please try again.",
                'transaction': None
            })
        
        # Try to fetch the receiver
        try:
            receiver = User.objects.get(username=receiver_username)
        except User.DoesNotExist:
            # Handle receiver not found
            return render(request, 'transaction_status.html', {
                'message': f"Transaction Failed: Receiver '{receiver_username}' does not exist.",
                'transaction': None
            })

        # Ensure sender and receiver have wallets
        sender_wallet, _ = Wallet.objects.get_or_create(user=request.user, defaults={"balance": Decimal("0.00")})
        receiver_wallet, _ = Wallet.objects.get_or_create(user=receiver, defaults={"balance": Decimal("0.00")})

        # Check sender's balance
        if sender_wallet.balance >= amount:
            # Perform the transaction
            sender_wallet.balance -= amount
            receiver_wallet.balance += amount
            sender_wallet.save()
            receiver_wallet.save()

            # Log the transaction
            transaction = Transaction.objects.create(
                sender=request.user,
                receiver=receiver,
                amount=amount,
                reference=f"TXN-{uuid.uuid4().hex[:8].upper()}",
                status='completed'
            )
            message = "Transaction Successful"
        else:
            # Log insufficient funds
            transaction = Transaction.objects.create(
                sender=request.user,
                receiver=receiver,
                amount=amount,
                reference=f"TXN-{uuid.uuid4().hex[:8].upper()}",
                status='failed'
            )
            message = "Transaction Failed: Insufficient Funds"

        return render(request, 'transaction_status.html', {'transaction': transaction, 'message': message})

    return render(request, 'transaction_form.html')



# View details of the wallet
@login_required
def wallet_detail(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet = None  # Handle if no wallet exists for this user

    return render(request, 'wallet_detail.html', {'wallet': wallet})

from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: u.is_superuser)
def create_wallet(request):
    if request.method == 'POST':
        # Get the user ID from the form
        user_id = request.POST.get('user_id')
        
        try:
            # Ensure the user exists
            user = User.objects.get(id=user_id)
            
            # Check if the user already has a wallet
            wallet, created = Wallet.objects.get_or_create(user=user)
            
            if not created:
                return render(request, 'index.html', {'message': f"Wallet already exists for {user.username}."})
            
            # If wallet is successfully created
            return redirect('wallet_detail', user_id=user.id)
        
        except User.DoesNotExist:
            return render(request, 'index.html', {'message': 'User does not exist.'})
    
    return render(request, 'create_wallet.html')

from django.shortcuts import render
from django.db.models import Q
from .models import Transaction

def transaction_history(request):
    user = request.user
    transactions = Transaction.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('-timestamp')

    transaction_messages = []
    current_balance = user.wallet.balance

    for transaction in transactions:
        if transaction.status == 'completed':  # Only show completed transactions
            if transaction.sender == user:
                # Calculate balance for sent transactions
                balance = current_balance - transaction.amount
                transaction_messages.append({
                    'type': 'sent',
                    'message':f"🚀 Woohoo! Transaction {transaction.reference} confirmed! KSH.{transaction.amount} just made its way to "
f"{transaction.receiver.username} on {transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')}. Your balance is "
f"still looking fine at {balance} KSH! Keep those transactions rolling! 💸🎉"

                })
            elif transaction.receiver == user:
                # Calculate balance for received transactions
                balance = current_balance + transaction.amount
                transaction_messages.append({
                    'type': 'received',
                    'message':f"Boom! 🎉 Transaction {transaction.reference} confirmed! You’ve just received KSH.{transaction.amount} from "
f"{transaction.sender.username} on {transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')}. "
f"Your balance is now looking pretty: {balance} KSH! Keep the party going! 💸💃🕺"

                })
            # Update the running balance to reflect the completed transaction
            current_balance = balance
        else:
            # For failed transactions, display a simple message
            transaction_messages.append({
                'type': 'failed',
                'message': f"Oops! 😬 Failed transaction {transaction.reference}! KSH.{transaction.amount} tried to reach "
f"{transaction.receiver.username} on {transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')}, but alas... "
f"Transaction failed. Looks like we’ll have to try again! 💔💸"

            })

    context = {
        'transaction_messages': transaction_messages,
    }
    return render(request, 'transaction_history.html', context)
