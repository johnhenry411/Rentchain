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
from .models import User,Lease,Property, PropertyImage, Proposal,Transaction,Wallet,Contract,Review
from property_app.utils import get_dashboard_url
from .forms import ProfileUpdateForm,PropertyForm, PropertyImageForm,ProposalForm  
from django.forms import modelformset_factory
from django.views import View
from django.contrib import messages
from django.db.models import Prefetch, Sum
from decimal import Decimal
import uuid
from django.db.models import Q
import logging
from django.contrib.auth import logout

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
    if not request.user.is_authenticated:
        return redirect('login')

    property = get_object_or_404(Property, id=property_id)

    if request.method == 'POST':
        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.property = property
            proposal.proposer = request.user
            proposal.save()

            # Create the related contract using the proposal data
            Contract.objects.create(
                proposal=proposal,
                landlord=property.landlord,
                client=request.user,
                property=property,
                lease_value=form.cleaned_data['proposed_price'],
                start_date=form.cleaned_data.get('start_date', None),
                end_date=form.cleaned_data.get('end_date', None),
            )

            return redirect('property_detail', id=property.id)
    else:
        form = ProposalForm()

    return render(request, 'submit_proposal.html', {'form': form, 'property': property})

from django.db import transaction

def accept_proposal(request, proposal_id):
    with transaction.atomic():
        proposal = get_object_or_404(Proposal, id=proposal_id)
        proposal.status = 'accepted'
        proposal.save()

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

# Call sign_contract to generate signatures
    contract.sign_contract()
    return redirect('view_contract', proposal_id=proposal.id)


def view_contract(request, proposal_id):
    if not request.user.is_authenticated:
        return HttpResponseForbidden("You must be logged in to view this contract.")

    proposal = get_object_or_404(Proposal, id=proposal_id)
    try:
        contract = Contract.objects.get(proposal=proposal)
    except Contract.DoesNotExist:
        logger.error("No Contract matches the given query.")
        return render(request, 'transaction_status.html', {
                    'message': "No Contract matches the given query.",
                    'transaction': None
                })

    logger.debug(f"Request User: {request.user}, Landlord: {contract.landlord}, Client: {contract.client}")

    if request.user != contract.landlord and request.user != contract.client:
        logger.warning("Unauthorized access attempt.")
        return render(request, 'transaction_status.html', {
                    'message': "You are Not authorized to view this contract",
                    'transaction': None
                })

    # Prepare contract data
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
    }

    return render(request, 'contract.html', context)


from django.db import transaction as db_transaction

from django.db import transaction


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate
from django.db import transaction
from decimal import Decimal
import uuid

@login_required
@transaction.atomic
def initiate_transaction(request):
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

            transaction_record = Transaction.objects.create(
                sender=request.user,
                receiver=receiver,
                amount=amount,
                reference=f"TXN-{uuid.uuid4().hex[:8].upper()}",
                status='completed'
            )

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

    # Authenticate the tenant's password
   # Authenticate the tenant's password
            password = request.POST.get("password")
            if not request.user.check_password(password):
                    return render(request, 'transaction_status.html', {
                             'message': "Transaction Failed: Incorrect password.",
                             'transaction': None
                    })
            # Fetch the contract and wallets
            contract = Contract.objects.filter(property_id=property_id, client=request.user).first()
            proposal=Proposal.objects.filter(property_id=property_id,client=request.user).first()
            if not contract:
                 return render(request, 'transaction_status.html', {
                'message': "Transaction Failed: No contract found for this property.",
                'transaction': None
            })

            tenant_wallet, _ = Wallet.objects.get_or_create(user=request.user)
            owner_wallet, _ = Wallet.objects.get_or_create(user=contract.landlord)
        
    # Verify tenant's balance
            if tenant_wallet.balance < amount:
                return render(request, 'transaction_status.html', {
                    'message': "Transaction Failed: Insufficient balance.",
                    'transaction': None
                })
    # Perform the transaction
          

            if contract.paid_amount >= contract.proposal.proposed_price:
                        contract.proposal.payment_status = "Paid"
                        message = "Payment cancelled. The property is totally paid."
            else:
                tenant_wallet.balance -= amount
                owner_wallet.balance += amount
                tenant_wallet.save()
                owner_wallet.save()

                # Proceed with payment processing
                contract.paid_amount += amount
                remaining_amount = contract.proposal.proposed_price - contract.paid_amount
                if contract.paid_amount >= contract.proposal.proposed_price:
                     contract.proposal.payment_status = "Paid"
                     message = "Payment successful. You have cleared the lease value."
                else:
                    message = f"Payment successful. Remaining amount to be paid: Ksh {remaining_amount:.2f}"
                transaction_record = Transaction.objects.create(
                    sender=request.user,
                receiver=contract.landlord,
                amount=amount,
                reference=f"TXN-{uuid.uuid4().hex[:8].upper()}",
                status='completed',
                property_id=property_id  # You might need to adjust this based on your model
            )
                proposal.save()
            contract.save()

            return render(request, 'transaction_status.html', {
                        'message': message,
                        'transaction': None
             }) 

# Render the transaction form for non-POST requests
    properties = Property.objects.all()  # Adjust filtering logic as needed
    return render(request, 'transaction_form.html', {'properties': properties})   # Render your payment page


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
from collections import defaultdict

def transaction_history(request):
    user = request.user
    transactions = Transaction.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).select_related('property').order_by('-timestamp')

    transaction_messages = []
    current_balance = user.wallet.balance

    # Status-based message handling
    status_messages = {
        'completed': {
            'sender': "Confirmed {reference}, KSH.{amount} sent to {receiver} for {property} on {timestamp}.",
            'receiver': "Confirmed {reference}, you have received KSH.{amount} from {sender} for {property} on {timestamp}."
        },
        'failed': "Transaction Failed, {reference}! KSH.{amount} sent to {receiver} for {property} on {timestamp} failed. Please try again.",
        'pending': "Transaction Pending, {reference}. KSH.{amount} to {receiver} for {property} is being processed.",
        'cancelled': "Transaction Cancelled, {reference}. KSH.{amount} to {receiver} for {property} was not processed."
    }

    for transaction in transactions:
        status = transaction.status
        base_message = status_messages.get(status)

        if status == 'completed':
            if transaction.sender == user:
                message = base_message['sender'].format(
                    reference=transaction.reference,
                    amount=transaction.amount,
                    receiver=transaction.receiver.username,
                    property=transaction.property.name if transaction.property else "this transaction",
                    timestamp=transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                )
                current_balance -= transaction.amount
            elif transaction.receiver == user:
                message = base_message['receiver'].format(
                    reference=transaction.reference,
                    amount=transaction.amount,
                    sender=transaction.sender.username,
                    property=transaction.property.name if transaction.property else "this transaction",
                    timestamp=transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                )
                current_balance += transaction.amount
        elif status in status_messages:  # Handle other statuses
            message = base_message.format(
                reference=transaction.reference,
                amount=transaction.amount,
                receiver=transaction.receiver.username,
                property=transaction.property.name if transaction.property else "this transaction",
                timestamp=transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            )
        else:
            # Handle unknown statuses
            message = f"Unknown transaction status for {transaction.reference}."

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
