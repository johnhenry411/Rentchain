from django.contrib import admin
from django.urls import path,include
from property_app import urls as property_urls
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include(property_urls))
]
