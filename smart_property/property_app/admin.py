from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Property, PropertyImage, Lease, Review, Profile,Proposal,Wallet,Transaction

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

from django.core.exceptions import ValidationError



from django.contrib import admin
from .models import Wallet

class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    actions = ['add_funds']

    # Action to add funds to a user's wallet
    def add_funds(self, request, queryset):
        for wallet in queryset:
            # Example: Add 100.00 to the selected wallets
            wallet.balance += 100.00
            wallet.save()
        self.message_user(request, "Funds have been added to the selected wallets.")

    add_funds.short_description = "Add Funds"

admin.site.register(Wallet, WalletAdmin)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['reference', 'amount', 'sender', 'receiver', 'status', 'timestamp']
    search_fields = ['reference', 'amount', 'sender', 'receiver', 'status', 'timestamp']
    list_filter = ['reference', 'amount', 'sender', 'receiver']
    ordering = ['timestamp']