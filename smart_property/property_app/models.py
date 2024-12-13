from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

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


from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class User(AbstractUser):
    ROLES = [
        ('client', 'Client'),
        ('landlord', 'Landlord'),
        ('admin', 'Admin'),
    ]

    role = models.CharField(max_length=10, choices=ROLES, default='client')

    # Custom related names for avoiding clashes with the default fields in AbstractUser
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

    def __str__(self):
        return self.username

    def is_client(self):
        return self.groups.filter(name='Clients').exists()

    def is_landlord(self):
        return self.groups.filter(name='Landlords').exists()

    def is_admin(self):
        return self.groups.filter(name='Admins').exists()

    def setup_roles(self):
        if self.role == 'client':
            client_group, _ = Group.objects.get_or_create(name='Clients')
            self.groups.add(client_group)
        if self.role == 'landlord':
            landlord_group, _ = Group.objects.get_or_create(name='Landlords')
            self.groups.add(landlord_group)
        if self.role == 'admin':
            admin_group, _ = Group.objects.get_or_create(name='Admins')
            self.groups.add(admin_group)
        
        self.save()



class Property(models.Model):
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
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='apartment')
    t_type= models.CharField(max_length=50,choices=lease_type,default='rent')

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


from django.db import models
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Link to the User model
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
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='proposals')
    proposer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proposals')
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # New field
    landlord_response = models.TextField(blank=True, null=True)  # New field
    client_signature = models.CharField(max_length=255, blank=True, null=True)
    landlord_signature = models.CharField(max_length=255, blank=True, null=True)
    def generate_signature(self, user):
       
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))  # Random 8 chars
        signature = f"{user.username}-{random_string}"
        print(f"Generated signature: {signature}")  # Debug print
        return signature
    def sign_contract(self):
     
        if self.status == 'accepted':
         print("sign_contract() method called")  # Debug statement
        # Ensure the proposer is the client and the property has a landlord
         if self.proposer.role == 'client' and self.property.landlord:
            print(f"Generating signatures for client: {self.proposer.username}, landlord: {self.property.landlord.username}")  # Debug statement
            self.client_signature = self.generate_signature(self.proposer)
            self.landlord_signature = self.generate_signature(self.property.landlord)
            print(f"Generated client signature: {self.client_signature}, landlord signature: {self.landlord_signature}")  # Debug statement
            self.save()
    
    def __str__(self):
        return f"Proposal by {self.proposer} for {self.property.name} - {self.proposed_price}"
