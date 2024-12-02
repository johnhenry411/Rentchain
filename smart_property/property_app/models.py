from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator


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
    property_name = models.CharField(max_length=100, default='Property Name')
    property_description = models.TextField(default='Property description')
    address = models.CharField(max_length=100, default='Property location')

    landlord = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'landlord'})
    
    main_image = models.ImageField(upload_to='media/property_images')
    property_value = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return self.property_name


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='media/property_images')
    image_id = models.CharField(max_length=5)

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
