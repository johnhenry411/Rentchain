from django.contrib import admin
from django.urls import path,include
from propery_app import urls as property_urls
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include(property_urls))
]
