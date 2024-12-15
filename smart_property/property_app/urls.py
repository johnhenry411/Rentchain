from . import views
from .views import ClientDashboardView, LandlordDashboardView, AdminDashboardView,update_profile,PropertyEditView, PropertyDeleteView,submit_proposal,view_contract,initiate_transaction
from django.urls import path

urlpatterns = [
    path ('',views.home,name='home'),
    path('client/dashboard/', ClientDashboardView.as_view(), name='client_dashboard'),
    path('landlord/dashboard/', LandlordDashboardView.as_view(), name='landlord_dashboard'),
    path('admins/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('signup/', views.client_signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('update-profile/', update_profile, name='update_profile'),
    path('landlord/property/edit/<int:property_id>/', PropertyEditView.as_view(), name='property_edit'),
    path('landlord/property/delete/<int:property_id>/', PropertyDeleteView.as_view(), name='property_delete'),
    path('property/<int:id>/', views.property_detail, name='property_detail'),
    path('property/<int:property_id>/propose/', submit_proposal, name='submit_proposal'),
    path('contract/<int:proposal_id>/', view_contract, name='view_contract'),
    path('transaction/', initiate_transaction, name='initiate_transaction'),
    path('wallet/', views.wallet_detail, name='wallet_detail'),
    path('wallet/create/', views.create_wallet, name='create_wallet'),
    path('transaction-history/', views.transaction_history, name='transaction_history'),

    ]
