from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import exceptions
from django.http import JsonResponse
import logging

logger = logging.getLogger('management')


class CustomTokenObtainPairView(TokenObtainPairView):

	def post(self, request, *args, **kwargs):
		# Call the default post method to get the access and refresh tokens
		response = super().post(request, *args, **kwargs)

		# Extract the refresh token from the response data
		refresh_token = response.data.get('refresh')

		# Set the refresh token in the HttpOnly cookie
		if refresh_token:
			response.set_cookie(
			key='refresh_token',  # Name of the cookie
			value=refresh_token,  # The refresh token
			httponly=True,  # Prevent JavaScript access
			secure=False,
			max_age=3600 * 24 * 7,  # Set the expiration time (1 week)
			samesite='None')

		return response


class CustomTokenRefreshView(TokenRefreshView):

	def post(self, request, *args, **kwargs):
		# Get the refresh token from the HttpOnly cookie
		refresh_token = request.COOKIES.get('refresh_token')

		if not refresh_token:
			raise exceptions.AuthenticationFailed('Refresh token is missing')

		try:
			# Validate the refresh token and create a new access token
			token = RefreshToken(refresh_token)
			data = {
				'access': str(token.access_token),
			}
			return JsonResponse(data)
		except Exception as e:
			raise exceptions.AuthenticationFailed(
				'Invalid or expired refresh token')
