""
from django.db import models
from django.contrib.auth.models import (AbstractBaseUser, 
                                        BaseUserManager, 
                                        PermissionsMixin)
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
 
# Create your models here.

import uuid
import os
def recipe_image_file_path(instance,filename):
    """Generate file path for recipe images."""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('uploads/recipe/', filename)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError('User must have an email address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        return user
    
    def create_superuser(self, email, password):
        """Create and return a new superuser."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        
        return user
    
    def create_staffuser(self, email, password):
        """Create and return a new staff user."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Manager for users.""" 
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    username = models.CharField(max_length=255, unique=False,default='unknown')
    date_joined = models.DateTimeField(default=timezone.now)
    first_name = models.CharField(max_length=255,default='unknown')
    last_name = models.CharField(max_length=255,default='unknown')
    
    objects = UserManager()
    USERNAME_FIELD = 'email'


class Recipe(models.Model):
    """Recipe object."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    tags = models.ManyToManyField('Tag')  # 改为 ManyToManyField
    ingredients = models.ManyToManyField('Ingredient')  # 改为 ManyToManyField
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True) 
    image = models.ImageField(null=True,upload_to=recipe_image_file_path)
    # attachments = models.FileField(upload_to=recipe_image_file_path)
    def create(self, serializer):
        """Create a new recipe."""
        serializer.save(user=self.request.user)
        return Response(serializer.data, status_code=status.HTTP_201_CREATED)

    def __str__(self):
        return self.title
    

class Tag(models.Model):
    """Tag for filtering recipes."""
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name

class Ingredient(models.Model):
    """Ingredient to be used in a recipe."""
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    
    def __str__(self):
        return self.name
