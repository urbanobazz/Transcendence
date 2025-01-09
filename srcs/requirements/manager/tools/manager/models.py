from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid

# Create your models here.
# manager/models.py (or another suitable file)
class User:
	def __init__(self, user_id, **kwargs):
		self.user_id = user_id
		self.is_authenticated = True  # Simulate authentication
		for key, value in kwargs.items():
			setattr(self, key, value)

	def __str__(self):
		return self.user_id
