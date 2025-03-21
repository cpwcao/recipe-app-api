""
from django.db import models
from django.contrib.auth.models import (AbstractBaseUser, 
                                        BaseUserManager, 
                                        PermissionsMixin)
from django.conf import settings
from django.utils import timezone
# Create your models here.


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