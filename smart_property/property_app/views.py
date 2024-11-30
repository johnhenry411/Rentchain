from django.shortcuts import render
from .models import tenants

def home(request):
    tenant=tenants.objects.all()
    return render(request, 'index.html',{'tenant':tenant})