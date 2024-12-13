from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Property, PropertyImage, Lease, Review, Profile,Proposal

# Customizing the User model admin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    list_display = ['username', 'email', 'role', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser', 'is_active']

# Registering the Property model
@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'landlord', 'price', 'category', 't_type', 'number_of_units', 'created_at']
    search_fields = ['name', 'location', 'category', 'landlord__username']
    list_filter = ['category', 't_type']
    ordering = ['-created_at']

# Registering the PropertyImage model
@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ['property', 'image_id', 'uploaded_at']
    search_fields = ['property__name', 'image_id']
    list_filter = ['uploaded_at']

# Registering the Lease model
@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = ['property', 'tenant', 'start_date', 'end_date', 'lease_value', 'lease_id']
    search_fields = ['property__name', 'tenant__username', 'lease_id']
    list_filter = ['start_date', 'end_date']

# Registering the Review model
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['property', 'tenant', 'stars']
    search_fields = ['property__name', 'tenant__username']
    list_filter = ['stars']

# Registering the Profile model
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'address', 'updated_at']
    search_fields = ['user__username', 'phone_number', 'address']
    list_filter = ['updated_at']
admin.site.register(Proposal)