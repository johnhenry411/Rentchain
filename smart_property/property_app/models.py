from django.db import models

class tenants(models.Model):
    name= models.CharField(max_length=100,default='name')
    email =models. EmailField()
    user_id=models. IntegerField()
    
    def __str__(self):
        return self.name

class landlords(models.Model):
    name = models.CharField(max_length=100, default='name')
    email = models.EmailField()
    
    def __str__(self):
        return self.name
  

class property(models.Model):
    property_name =models.CharField(max_length=100,default='prperty_name')
    property_description=models.TextField(default='property description')
    address = models.CharField(max_length=100,default='property location')
    landlord=models.ForeignKey(landlords, on_delete=models.CASCADE)
    main_image=models.ImageField(upload_to='media/propery_image')
    property_value=models.IntegerField(max_length=12)
    
    def __str__(self):
        return self.property_name
    
    
class property_images(models.Model):
    property=models.ForeignKey(property, on_delete=models.CASCADE)
    image=models.ImageField(upload_to='media/propery_image')
    image_id=models.CharField(max_length=5)
    def __str__(self):
        return self.image_id

class lease(models.Models):
    property=models.ForeignKey(property, on_delete=models.CASCADE)
    tenant=models.ForeignKey(tenants, on_delete=models.CASCADE)
    start_date=models.DateField()
    end_date=models.DateField()
    lease_value=models.IntegerField(max_length=12)
    lease_id=models.Random()
    
    def __str__(self):
        return self.lease_id

class reviews(models.Model):
    property=models.ForeignKey(property, on_delete=models.CASCADE)
    tenant=models.ForeignKey(tenants, on_delete=models.CASCADE)
    review=models.TextField(max_length=1000)
    stars=models.IntegerField(max_length=1)