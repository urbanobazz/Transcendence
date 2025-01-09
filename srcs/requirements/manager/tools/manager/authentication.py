# manager/authentication.py
import requests
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from .models import User
import logging

logger = logging.getLogger("manager")

class JWTAuthentication(BaseAuthentication):
	def authenticate(self, request):
		auth = request.META.get('HTTP_AUTHORIZATION')
		if not auth:
			return None

		try:
			scheme, token = auth.split()
			if scheme != 'Bearer':
				return None
		except ValueError:
			return None
		
		try:
			response = requests.get(
				f"{settings.USER_MANAGEMENT}/validate-token/",
				headers={'Authorization': f'Bearer {token}'}
			)
			response.raise_for_status()
		except requests.exceptions.RequestException as e:
			logger.warning(f"Error validating token: {e}")
			raise AuthenticationFailed('Error validating token')
		
		user_data = response.json()
		user_id = user_data['user_id']

		user = User(user_id=user_id)

		return (user, None)  # Return the user instance for permissions class



