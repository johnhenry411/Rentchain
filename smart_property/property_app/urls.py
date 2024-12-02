from . import views
from .views import ClientDashboardView, LandlordDashboardView, AdminDashboardView
from django.urls import path

urlpatterns = [
    path ('',views.home,name='home'),
    path('client/dashboard/', ClientDashboardView.as_view(), name='client_dashboard'),
    path('landlord/dashboard/', LandlordDashboardView.as_view(), name='landlord_dashboard'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('signup/', views.client_signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
]
