from . import views
from .views import ClientDashboardView, LandlordDashboardView, AdminDashboardView,update_profile,PropertyEditView, PropertyDeleteView
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
]
