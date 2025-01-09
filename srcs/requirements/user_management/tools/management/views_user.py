from .models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import getUserFromId, getUserData
from rest_framework.decorators import api_view
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.core.exceptions import ObjectDoesNotExist
import logging, json
import os

# Create your views here.

logger = logging.getLogger('management')


@csrf_exempt
def register(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		username = data.get('username')
		password = data.get('password')

		if not username or not password:
			return JsonResponse({'message': 'Username and password are required.'}, status=400)

		if User.objects.filter(username=username).exists():
			return JsonResponse({'message': 'Username already exists.'}, status=409)
		elif not isAllowedusername(username):
			return JsonResponse({'message': 'Username not allowed.'}, status=409)

		user = User.objects.create_user(username, password)
		return JsonResponse(
			{'message': f'User {user.username} created successfully!'}, status=201)

	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)


@csrf_exempt
@api_view(['GET'])
def validate_token(request):
	# Extract the token from the Authorization header
	auth_header = request.headers.get('Authorization')
	if not auth_header or not auth_header.startswith("Bearer "):
		logger.warning("Authorization header missing or invalid")
		return JsonResponse({'message': 'Authorization header missing or invalid'}, status=401)

	token = auth_header.split(" ")[1]
	jwt_auth = JWTAuthentication()

	try:
		validated_token = jwt_auth.get_validated_token(token)
		user = jwt_auth.get_user(validated_token)

		logger.debug("Finished!")

		return JsonResponse({
			'user_id': user.id,
			'username': user.username
		}, status=200)

	except (InvalidToken, TokenError) as e:
		logger.warning(f"Authentication error: {e}")
		return JsonResponse({'message': 'Invalid or expired token'}, status=401)


@csrf_exempt
def userManagement(request):
	user = getUserFromId(request)
	if not user:
		return JsonResponse({'message': 'Invalid token.'}, status=401)

	if request.method == 'POST':  # Will i get the ID or the username?
		data = json.loads(request.body)
		profile_id = data.get('profile_id')
		if not profile_id:
			user_info = getUserData(user)
			return JsonResponse(user_info, status=200)
		else:
			profile = User.objects.get(id=profile_id)
			profile_info = getUserData(profile, user)
			return JsonResponse(profile_info, status=200)

	elif request.method == 'PUT':
		data = json.loads(request.body)
		try:
			username = data.get('username')
			if username:
				if User.objects.filter(username=username).exists():
					return JsonResponse({'message': 'Username already exists.'}, status=409)
				elif not isAllowedusername(username):
					return JsonResponse({'message': 'Username not allowed.'}, status=409)
				else:
					user.username = username
					user.save()
					return JsonResponse({'message': 'Username updated successfully!'}, status=200)

			if data.get('old_password'):
				current_password = data.get('old_password')
				if not current_password or not user.check_password(current_password):
					return JsonResponse({'message': 'Current password is incorrect.'}, status=400)
				else:
					user.set_password(data.get('new_password'))
					user.save()
					return JsonResponse({'message': 'Password updated successfully!'}, status=200)

		except ObjectDoesNotExist:
			return JsonResponse({'message': 'User does not exist.'}, status=404)
		except Exception as e:
			return JsonResponse({'message': f'An error occurred: {str(e)}'}, status=500)

	elif request.method == 'DELETE':
		user.delete()
		return JsonResponse({'message': 'User deleted successfully!'}, status=200)


@csrf_exempt
def avatarUpload(request):
	if request.method == 'POST':
		user_id = request.POST.get('user_id')
		if not user_id:
			return JsonResponse({'message': 'User ID not provided.'}, status=400)

		try:
			user = User.objects.get(id=user_id)
		except User.DoesNotExist:
			return JsonResponse({'message': 'Invalid user ID.'}, status=401)

		if 'files' not in request.FILES:
			return JsonResponse({'message': 'No avatar file provided.'}, status=400)

		avatar = request.FILES['files']
		# Get the file extension
		ext = avatar.name.split('.')[-1]
		# Set the new filename
		avatar.name = f"{user_id}_avatar.{ext}"
		# Delete old avatar if it exists
		if user.avatar and os.path.isfile(f'data/avatars/{avatar.name}'):
			os.remove(user.avatar.path)
		user.avatar = avatar
		user.save()

		# Check if the file exists
		if os.path.exists(user.avatar.path):
			logger.info("File saved successfully.")
		else:
			logger.error("File not saved.")
		return JsonResponse({'message': 'Avatar uploaded successfully!'}, status=200)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)


@csrf_exempt
def listUsers(request):
	if request.method == 'POST':
		req_user = getUserFromId(request)
		users = User.objects.all()
		user_list = []
		for user in users:
			if req_user != user and not is_blocked(
					req_user, user) and not isHidden(user):
				user_list.append({'id': user.id, 'username': user.username})
		return JsonResponse(user_list, status=200, safe=False)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)


@csrf_exempt
def listFriends(request):
	user = getUserFromId(request)
	if not user:
		return JsonResponse({'message': 'Invalid token.'}, status=401)

	if request.method == 'POST':
		friends = user.friends.all()
		friend_list = []
		for friend in friends:
			if not is_blocked(user, friend):
				friend_list.append({
					'id': friend.id,
					'username': friend.username
				})
		return JsonResponse(friend_list, status=200, safe=False)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def listBlockedUsers(request):
	user = getUserFromId(request)
	if not user:
		return JsonResponse({'message': 'Invalid token.'}, status=401)

	if request.method == 'POST':
		blocked_users = user.blocked.all()
		blocked_user_list = []
		for blocked_user in blocked_users:
			blocked_user_list.append({
				'id': blocked_user.id,
				'username': blocked_user.username
			})
		return JsonResponse(blocked_user_list, status=200, safe=False)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)


@csrf_exempt
def manageFriends(request):
	user = getUserFromId(request)
	data = json.loads(request.body)
	friend_username = data.get('friend_username')

	if not user:
		return JsonResponse({'message': 'Invalid token.'}, status=401)

	if not friend_username:
		return JsonResponse({'message': 'Friend ID not provided.'}, status=400)

	try:
		friend = User.objects.get(username=friend_username)
	except User.DoesNotExist:
		return JsonResponse({'message': 'Invalid friend ID.'}, status=401)

	if request.method == 'POST':
		if user.friends.filter(username=friend_username).exists():
			return JsonResponse({'message': f'{friend.username}!'}, status=200)
		else:
			user.friends.add(friend)
			return JsonResponse({'message': 'Friend added successfully!'}, status=200)

	elif request.method == 'DELETE':
		if user.friends.filter(username=friend_username).exists():
			user.friends.remove(friend)
			return JsonResponse({'message': 'Friend removed successfully!'}, status=200)
		else:
			return JsonResponse({'message': 'Friend not found.'}, status=404)


@csrf_exempt
def manageBlocked(request):
	user = getUserFromId(request)
	data = json.loads(request.body)
	blocked_username = data.get('blocked_username')
	if not user:
		return JsonResponse({'message': 'Invalid token.'}, status=401)

	if not blocked_username:
		return JsonResponse({'message': 'Blocked username not provided.'}, status=400)

	try:
		blocked_user = User.objects.get(username=blocked_username)
	except User.DoesNotExist:
		return JsonResponse({'message': 'Invalid blocked username.'}, status=401)

	if request.method == 'POST':
		if user.blocked.filter(username=blocked_username).exists():
			return JsonResponse({'message': 'User already blocked.'}, status=200)
		else:
			user.blocked.add(blocked_user)
			return JsonResponse({'message': 'User blocked successfully!'}, status=200)

	elif request.method == 'DELETE':
		if user.blocked.filter(username=blocked_username).exists():
			user.blocked.remove(blocked_user)
			return JsonResponse({'message': 'User unblocked successfully!'}, status=200)
		else:
			return JsonResponse({'message': 'User not found in blocked list.'}, status=404)


def ping(request):
	return JsonResponse({'message': 'available'}, status=200)


def is_blocked(user, blocked_user):
	# if user.blocked.filter(username=blocked_user.username).exists():
	# 	return True
	if blocked_user.blocked.filter(username=user.username).exists():
		return True
	else:
		return False


def isHidden(hidden):
	if hidden.username == 'DefaultUser':
		return True
	else:
		return False

@csrf_exempt
def findUser(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		username = data.get('username')
		try:
			if not username:
				user = getUserFromId(request)
			else:
				user = User.objects.get(username=username)
		except Exception as e:
			return JsonResponse({'message': f'An error occurred while locating the user: {str(e)}'}, status=500)

		if user:
			return JsonResponse({'id': user.id, 'username': user.username}, status=200)
		else:
			return JsonResponse({'message': 'User not found.'}, status=404)

def isAllowedusername(username):
	forbidden = ['admin', 'root', 'sysadmin', 'PongChat', 'Tournament_Anouncer']
	if username in forbidden:
		return False
	else:
		return True
