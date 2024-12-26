from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
import random
import string
from decimal import Decimal
import logging 
from django.db import transaction
# Assign roles to groups during setup
def setup_roles():
    # Ensure the necessary groups exist
    client_group, _ = Group.objects.get_or_create(name='Clients')
    landlord_group, _ = Group.objects.get_or_create(name='Landlords')
    admin_group, _ = Group.objects.get_or_create(name='Admins')

    # Permissions specific to each group
    view_property_permission = Permission.objects.get(codename='view_property')

    # Assign permissions to the client group
    client_group.permissions.add(view_property_permission)
class User(AbstractUser):
    ROLES = [
        ('client', 'Client'),
        ('landlord', 'Landlord'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLES, default='client')
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    wallet_address = models.CharField(max_length=42, blank=True, null=True)  # Assuming Ethereum-like addresses
   
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",  # Specify a custom related_name
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",  # Specify a custom related_name
        blank=True,
    )

    def is_client(self):
       
        return self.groups.filter(name='Clients').exists()

    def is_landlord(self):
       
        return self.groups.filter(name='Landlords').exists()

    def is_admin(self):
       
        return self.groups.filter(name='Admins').exists()

    def setup_roles(self):
        """
        Assign the user to a group based on their role.
        """
        if self.role == 'client':
            client_group, _ = Group.objects.get_or_create(name='Clients')
            self.groups.add(client_group)
        elif self.role == 'landlord':
            landlord_group, _ = Group.objects.get_or_create(name='Landlords')
            self.groups.add(landlord_group)
        elif self.role == 'admin':
            admin_group, _ = Group.objects.get_or_create(name='Admins')
            self.groups.add(admin_group)
        
        self.save()

    @property
    def wallet(self):
        wallet, _ = Wallet.objects.get_or_create(user=self)
        return wallet

    def save(self, *args, **kwargs):
        is_new_user = self.pk is None  # Check if the user is being created
        super().save(*args, **kwargs)  # Save the user
        if is_new_user:
            Wallet.objects.get_or_create(user=self)

class Property(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing ID field
    landlord = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="properties")
    name = models.CharField(max_length=255, default='test')
    description = models.TextField(default='test')
    price = models.DecimalField(max_digits=10, decimal_places=2,default='123')
    location = models.CharField(max_length=255,default='test')
    created_at = models.DateTimeField(auto_now_add=True)
    number_of_units=models.IntegerField()
    size=models.IntegerField()
    baths=models.IntegerField()
    beds=models.IntegerField()
    amenities = models.ManyToManyField('Amenity', blank=True, related_name='properties',default='gym')
    contact_number = models.CharField(max_length=15, blank=True, null=True,default='0711111')
    utilities = models.TextField(blank=True, null=True, help_text="List included utilities (e.g., water, electricity).",default='water')
    nearby_features = models.TextField(blank=True, null=True,default='school')

    lease_type=[
        ('rent','Rent'),
        ('sale','Sale'),
        ('lease','Lease')
    ]
    CATEGORY_CHOICES = [
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('Home', 'home'),
        ('Office', 'office'),
        ('Garage', 'garage'),
    ]
    STATUS_CHOICES = [
    ('available', 'Available'),
    ('occupied', 'Occupied'),
    ('sold', 'Sold'),
]
    FURNISHING_CHOICES = [
    ('furnished', 'Furnished'),
    ('semi-furnished', 'Semi-Furnished'),
    ('unfurnished', 'Unfurnished'),
]
    furnishing_status = models.CharField(max_length=50, choices=FURNISHING_CHOICES, default='unfurnished')

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='available')

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='apartment')
    t_type= models.CharField(max_length=50,choices=lease_type,default='rent')

    def __str__(self):
        return self.name

class Amenity(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='media/property_images')
    image_id = models.CharField(max_length=5)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.image_id} of {self.property}"


class Lease(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'client'})
    start_date = models.DateField()
    end_date = models.DateField()
    lease_value = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    lease_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f"Lease {self.lease_id}"


class Review(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'client'})
    review = models.TextField(max_length=1000)
    stars = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    def __str__(self):
        return f"Review by {self.tenant} for {self.property}"



class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Proposal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    payment_status = models.CharField(
        max_length=20,
        choices=[('Pending', 'Pending'), ('Paid', 'Paid')],
        default='Pending'
    )
   
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='proposals')
    proposer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proposals')
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # New field
    landlord_response = models.TextField(blank=True, null=True)  # New field
   
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    def generate_signature(self, user):
        print(f"Generating signature for user: {user}")  # Debug
        print(f"User username: {user.username if user else 'No user found'}")  # Debug
        if not user or not user.username:
            return "Invalid-User"
    
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return f"{user.username}.{random_string}"

    def payment_status(self):
        """Dynamically calculate the payment status."""
        if self.proposal.proposed_price <= self.paid_amount:
            return "PAID"
        return "PENDING"

    def sign_contract(self):
        if self.status == 'accepted':
            self.client_signature = self.generate_signature(self.proposer)
            self.landlord_signature = self.generate_signature(self.property.landlord)
            print(f"Saving signatures: {self.client_signature}, {self.landlord_signature}")  # Debug
        self.save()

    def __str__(self):
        return f"Proposal by {self.proposer} for {self.property.name} - {self.proposed_price}"
    from django.core.exceptions import ObjectDoesNotExist
from .models import Property, User  # Assuming these are in the same app



from django.core.exceptions import ObjectDoesNotExist

# Utility functions for default values
def get_default_property():
    # Create or get a default property and assign a landlord
    default_landlord_id = get_default_landlord()
    property, created = Property.objects.get_or_create(
        name="Default Property",
        defaults={
            "location": "Default Location",
            "description": "Default property description",
            "landlord_id": 1,
            "baths":2,
            "beds":3,
            "size":2345,
            "number_of_units": 5# Assign the default landlord's ID
        }
    )
    return property.id  

def get_default_landlord():
    default_landlord, created = User.objects.get_or_create(
        username="default_landlord",
        defaults={"password": "password123"}
    )
    return default_landlord.id 

def get_default_user_john():
    john, created = User.objects.get_or_create(
        username="john",
        defaults={"password": "password123"}
    )
    return john.id  

class Contract(models.Model):
    proposal = models.OneToOneField(Proposal, on_delete=models.CASCADE)
    landlord = models.ForeignKey(User, on_delete=models.CASCADE)
    client = models.ForeignKey(
        User, related_name="client_contracts", on_delete=models.CASCADE
    )
    property_ref = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="contracts")
    lease_value = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    landlord_signature = models.CharField(max_length=100, null=True, blank=True)
    client_signature = models.CharField(max_length=100, null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=10, choices=Proposal.STATUS_CHOICES, default='pending')

    @property
    def payment_status(self):
        """Dynamically calculate the payment status."""
        if self.proposal.proposed_price <= self.paid_amount:
            return "PAID"
        return "PENDING"

    def generate_signature(self, user):
        """Generate a signature based on the username and a random string."""
        print(f"Generating signature for user: {user}")  # Debugging
        if not user or not user.username:
            return "Invalid-User"

        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return f"{user.username}.{random_string}"

    def sign_contract(self):
        """Generate signatures for the landlord and client and save the contract."""
        if self.proposal.status == 'accepted' and not self.landlord_signature and not self.client_signature:
            self.client_signature = self.generate_signature(self.client)
            self.landlord_signature = self.generate_signature(self.landlord)
            logging.debug(f"Generated Client Signature: {self.client_signature}")
            logging.debug(f"Generated Landlord Signature: {self.landlord_signature}")
            self.save()  # Save the contract
            logging.info("Contract saved successfully!")

    # Set up logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)
  
class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # Ensures wallet is deleted when user is deleted
        related_name='wallet'
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=45785.0)

    def __str__(self):
        return f"{self.user.username}'s Wallet - Balance: {self.balance}"


logger = logging.getLogger(__name__)

class Transaction(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_IN_PROGRESS = 'in_progress'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_IN_PROGRESS, 'In Progress'),
    ]

    sender = models.ForeignKey(User, related_name='sent_transactions', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_transactions', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=50, unique=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_PENDING)
    property = models.ForeignKey('Property', null=True, blank=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)  # Tracks when the transaction was completed

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def validate_transaction(self):
        """
        Validates transaction before processing.
        """
        sender_wallet = self.sender.wallet
        receiver_wallet = self.receiver.wallet

        # Ensure wallets exist
        if sender_wallet is None or receiver_wallet is None:
            raise ValueError("Sender or receiver wallet not found.")

        # Check sufficient balance
        if sender_wallet.balance < self.amount:
            raise ValueError("Insufficient funds in sender's wallet.")

        # Validate property (if applicable)
        if self.property:
            if self.property.status != 'available':
                raise ValueError("Property is not available for transaction.")
            if self.amount != self.property.price:
                raise ValueError("Transaction amount does not match property price.")

    def process_transaction(self):
        """
        Process the transaction and update related wallets and property status.
        """
        try:
            # Validate transaction
            self.validate_transaction()

            sender_wallet = self.sender.wallet
            receiver_wallet = self.receiver.wallet

            # Perform atomic transaction
            with transaction.atomic():
                sender_wallet.balance -= self.amount
                receiver_wallet.balance += self.amount
                sender_wallet.save()
                receiver_wallet.save()

                # Update property status (if applicable)
                if self.property:
                    if self.property.t_type == 'sale':
                        self.property.status = 'sold'
                    elif self.property.t_type in ['rent', 'lease']:
                        self.property.status = 'occupied'
                    self.property.save()

                # Mark transaction as completed
                self.status = self.STATUS_COMPLETED
                self.completed_at = timezone.now()
                self.save()

        except ValueError as ve:
            logger.error(f"Transaction validation failed: {ve}")
            self.status = self.STATUS_FAILED
            self.save()
            raise ve
        except Exception as e:
            logger.error(f"Transaction processing failed: {e}")
            self.status = self.STATUS_FAILED
            self.save()
            raise e
        transaction = Transaction.objects.create(
    sender=sender_user,
    receiver=receiver_user,
    amount=property_obj.price,  
    property=property_obj
)

    # def update_payment_status(self):
    #     """Update the payment status based on the paid amount and proposed price."""
    #     if self.paid_amount >= self.proposed_price:
    #         self.payment_status = 'Paid'
    #     else:
    #         self.payment_status = 'Pending'
    #     self.save()
