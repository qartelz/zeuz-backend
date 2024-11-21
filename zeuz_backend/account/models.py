from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Permission, Group
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

# Create your models here.


class UserManager(BaseUserManager):
    def create_user(self, email, name, phone_number, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, name, phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    groups = models.ManyToManyField(
        Group,
        related_name='account_user_groups',  
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='account_user_permissions',  
        blank=True
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone_number']

    def __str__(self):
        return self.email


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, max_length=300)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    last_updated = models.DateTimeField(auto_now=True,null=True,blank=True)

    def __str__(self):
        return f'{self.user.name} - Profile'
    
    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:  
            Profile.objects.create(user=instance)

    
class BeetleCoins(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coins = models.PositiveIntegerField(default=1000000)
    used_coins = models.PositiveIntegerField(default=0) 
    def __str__(self):
        return f'{self.user.name} - BeetleCoins'
    
    def save(self, *args, **kwargs):
        """Override the save method to automatically update the `coins` field whenever `used_coins` changes."""
        self.coins = 1000000 - self.used_coins  
        super().save(*args, **kwargs)

    def use_coins(self, amount):
        """Reduces the available coins and increases the used coins."""
        if amount <= 0:
            raise ValidationError("Amount to use must be greater than zero.")
        
        if self.coins < amount:
            raise ValidationError("Insufficient coins.")
        

        self.used_coins += amount
        self.save()

    def return_coins(self, amount):
        """Return coins back to available coins and decrease used coins."""
        if amount <= 0:
            raise ValidationError("Amount to return must be greater than zero.")
        
        if self.used_coins < amount:
            raise ValidationError("Cannot return more coins than have been used.")
        

        self.used_coins -= amount
        self.save()
    
   
@receiver(post_save, sender=User)
def create_beetle_coins(sender, instance, created, **kwargs):
    if created:
        BeetleCoins.objects.create(user=instance, used_coins=0) 

