from django.db import models

class tenants(models.Model):
    name= models.CharField(max_length=100,default='name')
    email =models. EmailField()
    