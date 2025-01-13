from . import views
from .views import ClientDashboardView, LandlordDashboardView, AdminDashboardView,PropertyEditView, PropertyDeleteView,submit_proposal,view_contract,initiate_transaction,delete_user,WalletListView,TransactionListView,ContractListView,ProposalListView,PropertyListView, logout_view, update_profile_view,qr_transaction_view
from django.urls import path

urlpatterns = [
    path ('',views.home,name='home'),
    path('client/dashboard/', ClientDashboardView.as_view(), name='client_dashboard'),
    path('landlord/dashboard/', LandlordDashboardView.as_view(), name='landlord_dashboard'),
    path('admins/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('signup/', views.client_signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('landlord/property/edit/<int:property_id>/', PropertyEditView.as_view(), name='property_edit'),
    path('landlord/property/delete/<int:property_id>/', PropertyDeleteView.as_view(), name='property_delete'),
    path('property/<int:id>/', views.property_detail, name='property_detail'),
    path('property/<int:property_id>/propose/', submit_proposal, name='submit_proposal'),
    path('contract/<int:proposal_id>/', view_contract, name='view_contract'),
    path('transaction/', initiate_transaction, name='initiate_transaction'),
    path('wallet/', views.wallet_detail, name='wallet_detail'),
    path('wallet/create/', views.create_wallet, name='create_wallet'),
    path('transaction-history/', views.transaction_history, name='transaction_history'),
    path('transactions/status/', views.transaction_status, name='transaction_status'),
    path('delete-user/<int:user_id>/', delete_user, name='delete_user'),
    path('wallets/', WalletListView.as_view(), name='manage_wallets'),
    path('transactions/', TransactionListView.as_view(), name='view_transactions'),
    path('Contracts/', ContractListView.as_view(), name='view_contracts'),
    path('Proposals/', ProposalListView.as_view(), name='view_proposals'),
    path('admins/properties/', PropertyListView.as_view(), name='property_list'),
    path('metamask_payment/', views.metamask_payment, name='metamask_payment'),
    path('logout/', logout_view, name='logout'),
    path('profile/update/', update_profile_view, name='update_profile'),
    path('qr_transaction_view/qr/<int:user_id>/<int:transaction_id>/', views.qr_transaction_view, name='qr_transaction_view'),
    path('property/<int:property_id>/transfer/', views.transfer_property, name='transfer_property'),
    
    ]
