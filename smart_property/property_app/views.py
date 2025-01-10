from django.shortcuts import redirect,render,get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import SignUpForm,WalletForm
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from .models import User,Lease,Property, PropertyImage, Proposal,Transaction,Wallet,Contract,Review,Profile
from property_app.utils import get_dashboard_url
from .forms import PropertyForm, PropertyImageForm,ProposalForm  
from django.forms import modelformset_factory
from django.views import View
from django.contrib import messages
from django.db.models import Prefetch, Sum
from decimal import Decimal
import uuid
from django.db.models import Q
import logging
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from datetime import date, timedelta

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG) 

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

@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('client'), name='dispatch')
class ClientDashboardView(TemplateView):
    template_name = 'client_dashboard.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Fetch or create the user's profile
        profile = get_object_or_404(Profile, user=user)
        
        # Properties owned by the current user
        context['owned_properties'] = Property.objects.filter(current_owner=user)
        
        # Add data to context
        context['proposals'] = Proposal.objects.filter(proposer=user).select_related('property')
        context['user'] = user
        context['profile'] = profile
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
        context['proposals']=Proposal.objects.all()
        context['contracts']=Contract.objects.all()
        context['wallets']=Wallet.objects.all()
        context['transactions']=Transaction.objects.all()
        context['total_wallet_balance'] = Wallet.objects.aggregate(total_balance=Sum('balance'))['total_balance'] or 0
        return context

def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.delete()
    return redirect('admin_dashboard')

class WalletListView(View):
    template_name = 'manage_wallets.html'

    def get(self, request, *args, **kwargs):
        wallets = Wallet.objects.select_related('user')  
        return render(request, self.template_name, {'wallets': wallets})

class TransactionListView(View):
    template_name = 'view_transactions.html'

    def get(self, request, *args, **kwargs):
        transactions = Transaction.objects.select_related('sender', 'receiver', 'property')        
        return render(request, self.template_name, {'transactions': transactions})

class PropertyListView(View):
    template_name = 'manage_property.html'

    def get(self, request, *args, **kwargs):
        properties = Property.objects.all()
        return render(request, self.template_name, {'properties': properties})

class ContractListView(View):
    template_name = 'manage_contracts.html'

    def get(self, request, *args, **kwargs):
        contracts = Contract.objects.select_related('proposal')  
        return render(request, self.template_name, {'contracts': contracts})

class ProposalListView(View):
    template_name = 'manage_proposals.html'

    def get(self, request, *args, **kwargs):
        proposals = Proposal.objects.all() 
        return render(request, self.template_name, {'proposals': proposals})

import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

def client_signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Create the profile instance
            profile = Profile.objects.create(user=user)

            # Generate QR code
            qr_data = f"http://localhost:8000/initiate_transaction/qr/{user.id}"  # Pass user ID in the URL
            qr = qrcode.make(qr_data)

            # Save QR code to the profile
            try:
                qr_io = BytesIO()
                qr.save(qr_io, format='PNG')
                qr_file_name = f"{user.username}_qr.png"
                profile.qr_code.save(qr_file_name, ContentFile(qr_io.getvalue()), save=True)
                print(f"QR code saved successfully: {qr_file_name}")
            except Exception as e:
                print(f"Error generating QR code: {e}")

            # Additional setup for the user (setup_roles is assumed to be a method in your user model)
            user.setup_roles()  # Call setup_roles() after saving the user
            return redirect('login')
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
        print(property.id,property.name) 
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



@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('landlord'), name='dispatch')
class LandlordDashboardView(View):

    def get(self, request, *args, **kwargs):
        # Fetch landlord properties and proposals
        properties = Property.objects.filter(landlord=request.user)
        proposals = Proposal.objects.filter(property__in=properties).select_related('proposer', 'property')

        # Create property image formset
        PropertyImageFormSet = modelformset_factory(PropertyImage, form=PropertyImageForm, extra=10)
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
    logger.debug(f"Starting proposal submission for property ID: {property_id}")
    if not request.user.is_authenticated:
        return redirect('login')

    property = get_object_or_404(Property, id=property_id)

    if request.method == 'POST':
        # Pass the property price to the form
        form = ProposalForm(request.POST, property_price=property.price)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.property = property
            proposal.proposer = request.user
            proposal.save()

            # Create the related contract
            contract = Contract.objects.create(
                proposal=proposal,
                landlord=property.landlord,
                client=request.user,
                property_ref=property,
                lease_value=form.cleaned_data['proposed_price'],
                start_date=form.cleaned_data.get('start_date', None),
                end_date=form.cleaned_data.get('end_date', None),
            )

            logger.debug(f"Proposal created with ID: {proposal.id}, attempting to create contract...")
            logger.debug(f"Contract created with ID: {contract.id}")

            return redirect('property_detail', id=property.id)
    else:
        # Pass the property price to the form for GET requests
        form = ProposalForm(property_price=property.price)

    return render(request, 'submit_proposal.html', {'form': form, 'property': property})

from django.db import transaction

def accept_proposal(request, proposal_id):
    try:
        with transaction.atomic():
            proposal = get_object_or_404(Proposal, id=proposal_id)
            proposal.status = 'accepted'
            proposal.save()

            # Create or fetch the contract
            contract, created = Contract.objects.get_or_create(
                proposal=proposal,
                defaults={
                    'landlord': proposal.property.landlord,
                    'client': proposal.proposer,
                    'property': proposal.property,
                    'lease_value': proposal.proposed_price,
                    'start_date': date.today(),
                    'end_date': date.today() + timedelta(days=365),
                    'status': 'accepted',
                },
            )

            if created:
                logger.info(f"Contract created for Proposal ID: {proposal_id}")
            else:
                logger.info(f"Contract already exists for Proposal ID: {proposal_id}")

            # Call sign_contract to generate signatures
            contract.sign_contract()

        return redirect('view_contract', proposal_id=proposal.id)
    except Exception as e:
        logger.error(f"Error accepting proposal ID {proposal_id}: {e}")
        messages.error(request, "An error occurred while accepting the proposal.")
        return redirect('proposal_list')  # Redirect to a fallback page



def view_contract(request, proposal_id):
    logger.debug(f"Fetching contract for proposal ID: {proposal_id}")

    if not request.user.is_authenticated:
        return HttpResponseForbidden("You must be logged in to view this contract.")

    proposal = get_object_or_404(Proposal, id=proposal_id)
    contract, created = Contract.objects.get_or_create(
        proposal=proposal,
        defaults={
            "landlord": proposal.property.landlord,
            "client": proposal.proposer,
            "property_ref": proposal.property,
            "lease_value": proposal.proposed_price,
            "start_date": proposal.start_date,
            "end_date": proposal.end_date,
            "paid_amount": Contract.paid_amount,
            "status": Contract.payment_status,
        }
    )

    if created:
        logger.info(f"Contract created for proposal ID: {proposal_id}")
        contract.sign_contract()

    # Check if the current user is either the landlord or the client
    if request.user != contract.landlord and request.user != contract.client:
        logger.warning(f"Unauthorized access attempt by user: {request.user}")
        return render(request, 'transaction_status.html', {
            'message': "You are not authorized to view this contract.",
            'transaction': None
        })

    # Prepare the context to render the contract view
    context = {
        'contract': contract,
        'property': contract.property_ref,
        'landlord': contract.landlord,
        'client': contract.client,
        'proposal': proposal,
        'lease_value': contract.lease_value,
        'payment_status': contract.payment_status,
        'start_date': contract.start_date,
        'end_date': contract.end_date,
        'contract_status': contract.payment_status,  # Status comes from the Contract itself
    }

    # Log the contract details if found
    logger.debug(f"Contract found: {contract.id}")

    # Render the contract template
    return render(request, 'contract.html', context)




from django.db import transaction as db_transaction

from django.db import transaction


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate
from django.db import transaction
from decimal import Decimal
import uuid

import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from decimal import Decimal
import uuid
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from .models import User, Wallet, Transaction, Contract, Proposal, Property

@login_required
@db_transaction.atomic
def initiate_transaction(request, user_id=None, transaction_id=None):
    # Handle QR code-based transaction initiation (with user_id and transaction_id in the URL)
    if user_id and transaction_id:
        try:
            # Fetch the user and transaction based on URL parameters
            user = get_object_or_404(User, id=user_id)
            transaction = get_object_or_404(Transaction, id=transaction_id)

            # Ensure that the transaction belongs to the user
            if transaction.sender != user:
                return render(request, 'transaction_status.html', {
                    'message': "Transaction Failed: This transaction does not belong to you.",
                    'transaction': None
                })

            # Return the transaction details page for QR code scan
            return render(request, 'transaction_form.html', {'transaction': transaction})

        except (User.DoesNotExist, Transaction.DoesNotExist):
            return render(request, 'transaction_status.html', {
                'message': "Transaction or User not found.",
                'transaction': None
            })

    # Handle regular POST requests for both user-to-user and property payments
    if request.method == 'POST':
        # Handle user-to-user transaction
        if 'receiver' in request.POST:
            receiver_username = request.POST.get('receiver')
            try:
                amount = Decimal(request.POST.get('amount', 0))
                if amount <= 0:
                    raise ValueError("Invalid transaction amount.")
            except (ValueError, TypeError):
                return render(request, 'transaction_status.html', {
                    'message': "Transaction Failed: Invalid amount.",
                    'transaction': None
                })

            # Authenticate the sender's password
            password = request.POST.get('password')
            user = authenticate(username=request.user.username, password=password)
            if not user:
                return render(request, 'transaction_status.html', {
                    'message': "Transaction Failed: Incorrect password. Please try again.",
                    'transaction': None
                })

            # Fetch the receiver
            try:
                receiver = User.objects.get(username=receiver_username)
            except User.DoesNotExist:
                return render(request, 'transaction_status.html', {
                    'message': f"Transaction Failed: Receiver '{receiver_username}' does not exist.",
                    'transaction': None
                })

            # Ensure wallets exist
            sender_wallet, _ = Wallet.objects.get_or_create(user=request.user, defaults={"balance": Decimal("0.00")})
            receiver_wallet, _ = Wallet.objects.get_or_create(user=receiver, defaults={"balance": Decimal("0.00")})

            # Verify sender's balance
            if sender_wallet.balance < amount:
                transaction_record = Transaction.objects.create(
                    sender=request.user,
                    receiver=receiver,
                    amount=amount,
                    reference=f"TXN-{uuid.uuid4().hex[:8].upper()}",
                    status='failed'
                )
                return render(request, 'transaction_status.html', {
                    'message': "Transaction Failed: Insufficient Funds.",
                    'transaction': transaction_record
                })

            # Perform the transaction
            sender_wallet.balance -= amount
            receiver_wallet.balance += amount
            sender_wallet.save()
            receiver_wallet.save()

            # Record the transaction
            transaction_record = Transaction.objects.create(
                sender=request.user,
                receiver=receiver,
                amount=amount,
                reference=f"TXN-{uuid.uuid4().hex[:8].upper()}",
                status='completed'
            )

            # Generate and save the QR code
            qr_data = f"Transaction ID: {transaction_record.id}, Amount: {transaction_record.amount}, Receiver: {receiver.username}"
            qr = qrcode.make(qr_data)
            qr_io = BytesIO()
            qr.save(qr_io, format='PNG')
            qr_file_name = f"transaction_{transaction_record.id}_qr.png"
            transaction_record.qr_code.save(qr_file_name, ContentFile(qr_io.getvalue()), save=True)

            return render(request, 'transaction_status.html', {
                'message': "Transaction Successful.",
                'transaction': transaction_record
            })

        # Handle property payment transaction
        elif 'property_id' in request.POST:
            property_id = request.POST.get("property_id")
            try:
                amount = Decimal(request.POST.get("amount", 0))
                if amount <= 0:
                    raise ValueError("Invalid transaction amount.")
            except (ValueError, TypeError):
                return render(request, 'transaction_status.html', {
                    'message': "Transaction Failed: Invalid amount.",
                    'transaction': None
                })
            
            password = request.POST.get("password")
            if not request.user.check_password(password):
                return render(request, 'transaction_status.html', {
                    'message': "Transaction Failed: Incorrect password.",
                    'transaction': None
                })
                

            # Fetch the contract and wallets
            contract = Contract.objects.filter(property_ref=property_id, client=request.user).first()
            if not contract:
                return render(request, 'transaction_status.html', {
                    'message': "Transaction Failed: No contract found for this property.",
                    'transaction': None
                })
            if contract.paid_amount >= contract.lease_value:
                return render(request,'transaction_status.html',{
                   'message': "the contract is fully settled",
                    'transaction': None 
                })

            tenant_wallet, _ = Wallet.objects.get_or_create(user=request.user)
            owner_wallet, _ = Wallet.objects.get_or_create(user=contract.landlord)

            # Verify tenant's balance
            if tenant_wallet.balance < amount:
                transaction_record = Transaction.objects.create(
                    sender=request.user,
                    receiver=contract.landlord,
                    amount=amount,
                    reference=f"TXN-{uuid.uuid4().hex[:8].upper()}",
                    status='failed'
                )
                return render(request, 'transaction_status.html', {
                    'message': "Transaction Failed: Insufficient Funds.",
                    'transaction': transaction_record
                })
            
            # Perform the transaction
            tenant_wallet.balance -= amount
            owner_wallet.balance += amount
            tenant_wallet.save()
            owner_wallet.save()

            # Update contract and record transaction
            contract.paid_amount += amount
            contract.save()
            transaction_record = Transaction.objects.create(
                sender=request.user,
                receiver=contract.landlord,
                amount=amount,
                reference=f"TXN-{uuid.uuid4().hex[:8].upper()}",
                status='completed',
                property_id=property_id
            )
            # Generate and save the QR code
            qr_data = f"Transaction ID: {transaction_record.id}, Property ID: {property_id}, Amount: {transaction_record.amount}"
            qr = qrcode.make(qr_data)
            qr_io = BytesIO()
            qr.save(qr_io, format='PNG')
            qr_file_name = f"transaction_{transaction_record.id}_qr.png"
            transaction_record.qr_code.save(qr_file_name, ContentFile(qr_io.getvalue()), save=True)

            return render(request, 'transaction_status.html', {
                'message': "Payment successful.",
                'transaction': transaction_record
            })

        return render(request, 'transaction_status.html', {
            'message': "Invalid transaction request.",
            'transaction': None
        })

    # Render the transaction form for non-POST requests or if no action is taken in POST
    properties = Property.objects.all() 
    return render(request, 'transaction_form.html', {'properties': properties})



# View details of the wallet
@login_required
def wallet_detail(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet = None  # Handle if no wallet exists for this user

    # Fetch the wallet address from the User model
    wallet_address = request.user.wallet_address  # Assuming 'wallet_address' is a field on the User model

    # Pass the wallet and wallet address to the template
    return render(request, 'wallet_detail.html', {
        'wallet': wallet,
        'wallet_address': wallet_address
    })

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
from collections import defaultdict

def transaction_history(request):
    user = request.user
    transactions = Transaction.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).select_related('property', 'sender', 'receiver').order_by('-timestamp')

    transaction_messages = []
    current_balance = user.wallet.balance

    status_messages = {
        'completed': {
            'sender': {
                'property':"Confirmed {reference}, KSH.{amount:,} sent to {receiver_first_name} {receiver_last_name} for property {property} on {timestamp}. Current balance: KSH.{current_balance:,}.",
                'user': "Confirmed {reference}, KSH.{amount:,} sent to {receiver_first_name} {receiver_last_name} on {timestamp}. Current balance: KSH.{current_balance:,}."
            },
            'receiver': {
                'property': "Confirmed {reference}, you have received KSH.{amount:,} from {sender_first_name} {sender_last_name} for property {property} on {timestamp}. Current balance: KSH.{current_balance:,}.",
                'user': "Confirmed {reference}, you have received KSH.{amount:,} from {sender_first_name} {sender_last_name} on {timestamp}. Current balance: KSH.{current_balance:,}."
            }
        },
        'failed': {
            'sender':{
              'property':"Transaction Failed, {reference} You do not have enough funds in your wallet to send KSH.{amount:,}  to {receiver_first_name} {receiver_last_name} for {property} on {timestamp} failed. Current balance: KSH.{current_balance:,}.",               
              'user':"Transaction Failed, {reference} You do not have enough funds in your wallet to send KSH.{amount:,}  to {receiver_first_name} {receiver_last_name} on {timestamp}. Current balance: KSH.{current_balance:,}."   
            }
            },
            
        'pending': "Transaction Pending, {reference}. KSH.{amount} to {receiver_first_name} {receiver_last_name} for {property} is being processed. Current balance: KSH.{current_balance}.",
        'cancelled': "Transaction Cancelled, {reference}. KSH.{amount} to {receiver_first_name} {receiver_last_name} for {property} was not processed. Current balance: KSH.{current_balance}."
    }

    for transaction in transactions:
        status = transaction.status
        transaction_type = 'property' if transaction.property else 'user'
        base_message = status_messages.get(status)

        if status == 'completed':
            if transaction.sender == user:
                message_template = base_message['sender'][transaction_type]
                message = message_template.format(
                    reference=transaction.reference,
                    amount=transaction.amount,
                    receiver_first_name=transaction.receiver.first_name,
                    receiver_last_name=transaction.receiver.last_name,
                    property=transaction.property.name if transaction.property else "",
                    timestamp=transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    current_balance=current_balance
                )
                current_balance -= transaction.amount
            elif transaction.receiver == user:
                message_template = base_message['receiver'][transaction_type]
                message = message_template.format(
                    reference=transaction.reference,
                    amount=transaction.amount,
                    sender_first_name=transaction.sender.first_name,
                    sender_last_name=transaction.sender.last_name,
                    property=transaction.property.name if transaction.property else "",
                    timestamp=transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    current_balance=current_balance
                )
                current_balance += transaction.amount
                
        elif status == 'failed':
            if transaction.sender == user:
                message_template = base_message['sender'][transaction_type]
                message = message_template.format(
                  reference=transaction.reference,
                  amount=transaction.amount,
                  receiver_first_name=transaction.receiver.first_name,
                  receiver_last_name=transaction.receiver.last_name,
                  property=transaction.property.name if transaction.property else "this transaction",
                  timestamp=transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                  current_balance=current_balance
        )

        else:
            # Handle unknown statuses
            message = f"Unknown transaction status for {transaction.reference}. Current balance: KSH.{current_balance}."

        # Append message to transaction_messages
        transaction_messages.append({
            'type': status,
            'message': message,
            'timestamp': transaction.timestamp
        })

    context = {
        'transaction_messages': transaction_messages,
        'transactions': transactions,
    }

    return render(request, 'transaction_history.html', context)




@login_required
def transaction_status(request):
    # Fetch transactions for the logged-in user
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')

    context = {
        'transactions': transactions,
    }
    return render(request, 'transaction_status1.html', context)

def logout_view(request):
    logout(request)
    return redirect('home')  # Redirects to home page after logout


@login_required
@csrf_exempt
@transaction.atomic
def metamask_payment(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        property_id = data.get('property_id')
        amount = Decimal(data.get('amount', 0))
        transaction_hash = data.get('transaction_hash')

        try:
            # Validate data
            if amount <= 0:
                raise ValueError("Invalid amount.")

            # Fetch property and associated contract
            contract = Contract.objects.filter(property_ref=property_id, client=request.user).first()
            if not contract:
                return JsonResponse({'message': 'Transaction Failed: Invalid property ID.'}, status=400)

            # Fetch the tenant and landlord wallet addresses (MetaMask addresses)
            tenant_wallet_address = request.data.get('tenant_wallet_address')
            landlord_wallet_address = contract.landlord.wallet_address  # Assuming landlord's MetaMask address is stored in contract

            if not tenant_wallet_address or not landlord_wallet_address:
                return JsonResponse({'message': 'Missing MetaMask wallet addresses.'}, status=400)

            # Simulate a transaction (balance check and sending the transaction will be done on frontend using Ethers.js)
            # Here, we just check if the provided transaction hash is valid (for now, actual validation is done in the frontend)
            if not transaction_hash:
                return JsonResponse({'message': 'Transaction Failed: Missing transaction hash.'}, status=400)

            # Record the transaction
            Transaction.objects.create(
                sender=request.user,
                receiver=contract.landlord,
                amount=amount,
                reference=f"TXN-{uuid.uuid4().hex[:8].upper()}",
                status='pending',  # Mark the transaction as pending initially
                property_id=property_id,
                transaction_hash=transaction_hash
            )

            # Update contract details and check if the full payment has been made
            contract.paid_amount += amount
            if contract.paid_amount >= contract.proposal.proposed_price:
                contract.proposal.payment_status = "Paid"
                message = "Payment successful. You have cleared the lease value."
            else:
                remaining = contract.proposal.proposed_price - contract.paid_amount
                message = f"Payment successful. Remaining amount: Ksh {remaining:.2f}"

            contract.save()

            return JsonResponse({'message': message}, status=200)

        except Exception as e:
            # Generic error handling
            return JsonResponse({'message': f'Transaction Failed: {str(e)}'}, status=400)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserProfileForm, ProfileForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Profile
from .forms import UserProfileForm, ProfileForm

from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .forms import UserProfileForm, ProfileForm
from .models import Profile

@login_required
def update_profile_view(request):
    user = request.user
    # Retrieve or create the user's profile
    profile, created = Profile.objects.get_or_create(user=user)
    if created:
        print(f"A new profile was created for user: {user.username}")
    else:
        print(f"Existing profile retrieved for user: {user.username}")

    if request.method == 'POST':
        print("Processing POST request...")
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)

        # Initialize forms with POST data and profile/user instances
        user_form = UserProfileForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        # Check if forms are valid
        if user_form.is_valid() and profile_form.is_valid():
            print("Both forms are valid. Saving data...")
            user_form.save()
            profile_form.save()
            print("User and profile successfully updated.")

            # Add a success message
            messages.success(request, 'Your profile has been successfully updated.')

            # Redirect to client dashboard after successful update
            return redirect('client_dashboard')  # Redirect to a profile page or success page
        else:
            # Log form errors for debugging
            print("Form validation failed:")
            print("User form errors:", user_form.errors)
            print("Profile form errors:", profile_form.errors)
    else:
        print("Rendering form for GET request...")
        # Pre-fill forms with existing data
        user_form = UserProfileForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    # Render the update profile page
    return render(request, 'update_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


@login_required
def qr_transaction_view(request, user_id):
    receiver = get_object_or_404(User, id=user_id)
    if request.method == 'GET':
        return render(request, 'transaction_form.html', {
            'receiver': receiver.username
        })
        
        
@login_required
@db_transaction.atomic
def qr_transaction_view(request, user_id, transaction_id):
    try:
        user = get_object_or_404(User, id=user_id)
        transaction = get_object_or_404(Transaction, id=transaction_id)

        # Ensure the transaction belongs to the user
        if transaction.sender != user:
            return render(request, 'transaction_status.html', {
                'message': "Transaction Failed: This transaction does not belong to you.",
                'transaction': None
            })

        # Process the transaction if it hasn't been completed
        if transaction.status == 'pending':
            sender_wallet = Wallet.objects.get(user=transaction.sender)
            receiver_wallet = Wallet.objects.get(user=transaction.receiver)

            if sender_wallet.balance < transaction.amount:
                transaction.status = 'failed'
                transaction.save()
                return render(request, 'transaction_status.html', {
                    'message': "Transaction Failed: Insufficient Funds.",
                    'transaction': transaction
                })

            # Update wallets
            sender_wallet.balance -= transaction.amount
            receiver_wallet.balance += transaction.amount
            sender_wallet.save()
            receiver_wallet.save()

            # Update transaction status
            transaction.status = 'completed'
            transaction.save()

            return render(request, 'transaction_status.html', {
                'message': "Transaction Successful.",
                'transaction': transaction
            })

        return render(request, 'transaction_status.html', {
            'message': "Transaction already processed.",
            'transaction': transaction
        })

    except (User.DoesNotExist, Transaction.DoesNotExist):
        return render(request, 'transaction_status.html', {
            'message': "Transaction or User not found.",
            'transaction': None
        })


@login_required
def transfer_property(request, property_id):
    """
    View to handle property ownership transfer.
    """
    property_obj = get_object_or_404(Property, id=property_id)
    print(f"Property found: {property_obj.name}, ID: {property_obj.id}")

    # Only the current landlord or admin can transfer ownership
    if request.user != property_obj.landlord and not request.user.is_superuser:
        print("Unauthorized access attempt.")
        return HttpResponseForbidden("You are not authorized to transfer this property.")

    if request.method == "POST":
        new_owner_id = request.POST.get('new_owner')
        print(f"New owner ID: {new_owner_id}")
        try:
            new_owner = User.objects.get(id=new_owner_id)
            print(f"New owner found: {new_owner.username}, ID: {new_owner.id}")
            property_obj.transfer_ownership(new_owner)
            print(f"Ownership transferred to {new_owner.username}")
            messages.success(request, f"Ownership of property '{property_obj.name}' has been transferred to {new_owner.username}.")
        except User.DoesNotExist:
            print("User does not exist.")
            messages.error(request, "The selected user does not exist.")
        except Exception as e:
            print(f"An error occurred: {e}")
            messages.error(request, f"An error occurred: {e}")

        return redirect('home')  # Redirect to a property detail page

    # Render a confirmation page or form
    users = User.objects.exclude(id=request.user.id)  # Exclude the current landlord from the dropdown
    return render(request, 'transfer_property.html', {'property': property_obj, 'users': users})

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Wallet

@login_required
def wallet_view(request):
    user_wallet = Wallet.objects.filter(user=request.user).first()
    context = {
        'wallet': user_wallet,
        'user': request.user,
    }
    return render(request, 'wallet_detail.html', context)
