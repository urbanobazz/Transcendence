from rest_framework.decorators import api_view, permission_classes
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.permissions import IsAuthenticated
from django.test import RequestFactory
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import requests, logging, os, json

logger = logging.getLogger("manager")


@api_view(["POST"])
def register(request):
    """Register user to database"""
    username = request.data.get('username')
    if username and username.startswith('42_'):
        return JsonResponse({'message': 'Username cannot begin with "42_"'}, status=400)
    response = requests.post(settings.USER_MANAGEMENT + "/register/",
                             json=request.data)

    return JsonResponse(data=response.json(),
                        status=response.status_code,
                        safe=False)


@api_view(["POST"])
def login(request, OAuth=False):
    """Authenticate user with simpleJWT library and save refresh token as HTTP Only cookie"""
    if not OAuth:
        username = request.data.get('username')
        if username and username.startswith('42_'):
            return JsonResponse({'message': 'Username cannot begin with "42_"'}, status=400)

    response = requests.post(
        settings.USER_MANAGEMENT + "/token/",
        json=request.data,
        headers={"Content-Type": "application/json"},
    )

    response_data = response.json()
    if 'refresh' in response_data:
        del response_data['refresh']

    django_response = JsonResponse(data=response_data,
                                   status=response.status_code,
                                   safe=False)

    if 'refresh_token' in response.cookies:
        refresh_token = response.cookies['refresh_token']
        django_response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=True,
            max_age=3600 * 24 * 7,  # 1 week
            samesite='None',  # For cross-origin cookie
        )

    return django_response


@api_view(["POST"])
def logout(request):
    """Remove HTTP Only Cookie"""
    response = JsonResponse({'message': 'Logged out successfully'})
    response.delete_cookie('refresh_token')
    return response


@api_view(["GET", "POST", "PUT", "DELETE", "HEAD"])
@permission_classes([IsAuthenticated])
def user(request):
    """GET gets all info from authenticated user
	POST should return all user info based on id/username
	PUT edit profile, user should be able to change username etc
	DELETE user can delete account"""
    if request.method == "GET":
        user = request.user
        data = {
            "user_id": user.user_id,
        }
        response = requests.post(settings.USER_MANAGEMENT + "/user/",
                                 json=data)

        return JsonResponse(data=response.json(),
                            status=response.status_code,
                            safe=False)
    elif request.method == "POST":
        data = {
            "user_id": request.user.user_id,
            "profile_id": request.data.get("user_id"),
        }
        response = requests.post(settings.USER_MANAGEMENT + "/user/",
                                 json=data)
        return JsonResponse(data=response.json(),
                            status=response.status_code,
                            safe=False)
    elif request.method == "HEAD":
        user = request.user
        data = {
            "user_id": user.user_id,
        }
        response = requests.post(settings.USER_MANAGEMENT + "/user/",
                                 json=data)

        return HttpResponse(status=response.status_code)
    elif request.method == "PUT":
        user = request.user
        username = request.data.get('newUsername')
        if username and username.startswith('42_'):
            return JsonResponse({'message': 'Username cannot begin with "42_"'}, status=400)
        data = {
            "user_id": user.user_id,
            "old_password": request.data.get("oldPassword"),
            "new_password": request.data.get("newPassword"),
            "username": username,
        }
        logger.debug(f"edit profile data {data}")
        response = requests.put(settings.USER_MANAGEMENT + "/user/",
                                 json=data)
        return JsonResponse(data=response.json(),
                            status=response.status_code,
                            safe=False)

@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
def friends(request):
    """ GET: return all friends of authenticated user
		POST: befriend username
		DELETE: unfriend username"""
    if (request.method == "GET"):
        user = request.user
        data = {
            "user_id": user.user_id,
        }
        response = requests.post(settings.USER_MANAGEMENT + "/friends/",
                                 json=data)
        return JsonResponse(data=response.json(),
                            status=response.status_code,
                            safe=False)

    elif (request.method == "POST"):
        user_id = request.user.user_id
        friend_username = request.data.get("friend_username")
        data = {
            "user_id": user_id,
            "friend_username": friend_username,
        }
        response = requests.post(settings.USER_MANAGEMENT + "/friends/manage/",
                                 json=data)
        return JsonResponse(data=response.json(),
                            status=response.status_code,
                            safe=False)

    elif (request.method == "DELETE"):
        user_id = request.user.user_id
        friend_username = request.data.get("friend_username")
        data = {
            "user_id": user_id,
            "friend_username": friend_username,
        }
        response = requests.delete(settings.USER_MANAGEMENT +
                                   "/friends/manage/",
                                   json=data)
        return JsonResponse(data=response.json(),
                            status=response.status_code,
                            safe=False)


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def block(request):
    """ POST: block username
		DELETE: unblock username"""
    if (request.method == "POST"):
        user_id = request.user.user_id
        blocked_username = request.data.get("blocked_username")
        data = {
            "user_id": user_id,
            "blocked_username": blocked_username,
        }
        response = requests.post(settings.USER_MANAGEMENT +
                                 "/friends/blocked/",
                                 json=data)
        return JsonResponse(data=response.json(),
                            status=response.status_code,
                            safe=False)

    elif (request.method == "DELETE"):
        user_id = request.user.user_id
        blocked_username = request.data.get("blocked_username")
        data = {
            "user_id": user_id,
            "blocked_username": blocked_username,
        }
        response = requests.delete(settings.USER_MANAGEMENT +
                                   "/friends/blocked/",
                                   json=data)
        return JsonResponse(data=response.json(),
                            status=response.status_code,
                            safe=False)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search(request):
    """return all registered users on platform"""
    response = requests.post(
        settings.USER_MANAGEMENT + "/search/",
        json={"user_id": request.user.user_id},
    )

    return JsonResponse(data=response.json(),
                        status=response.status_code,
                        safe=False)


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def multi(request):
    """GET:  user wants to see all running multi-player games
	DELETE: user wants to cancel a game based on id"""
    if request.method == "GET":
        user_id = request.user.user_id

        response = requests.post(
            settings.USER_MANAGEMENT + "/multi/",
            json={"user_id": user_id},
        )

        response_data = {}
        response_data["games"] = response.json()
        response_data["user_id"] = user_id

        return JsonResponse(data=response_data,
                            status=response.status_code,
                            safe=False)
    elif request.method == "DELETE":
        user_id = request.user.user_id
        game_id = request.data.get("game_id")

        logger.debug(f"delete game {game_id} by user {user_id}")
        response = requests.delete(
            settings.USER_MANAGEMENT + "/multi/delete/",
            json={"user_id": user_id, "game_id": game_id},
        )
        return JsonResponse(data=response.json(),
                            status=response.status_code,
                            safe=False)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def joinMulti(request):
    """GET:  user wants to see all running multi-player games
	POST: user wants to join a running game based on id"""

    logger.info(f"MULTIJOIN {request}")
    if request.method == "POST":
        # Extract game_id and user_id from the request data
        user_id = request.user.user_id  # User's ID from the request context
        game_id = request.data.get(
            "game_id")  # Expecting "game_id" in POST body

        if not game_id:
            return JsonResponse({"error": "Missing game_id in request data"},
                                status=400)

        # Prepare payload for user management service
        payload = {"user_id": user_id, "game_id": game_id}

        # Forward the request to the user management service
        response = requests.post(f"{settings.USER_MANAGEMENT}/multi/join/",
                                 json=payload)

        payload = {"user_id": user_id, "game_id": game_id, "message" : response.json()}

        # Return the response from the user management service
        return JsonResponse(data=payload,
                            status=response.status_code,
                            safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def createMulti(request):
    """Creates a new multiplayergame for authenticated user"""
    user = request.user

    data = {
        "user_id": user.user_id,
        "is_ai": False,
        "game_name": request.data.get('game_name'),
        "game_speed": request.data.get('game_speed'),
        "power_ups": request.data.get('power_ups')
    }
    logger.debug(f"create multiplayer: {data}")
    response = requests.post(settings.USER_MANAGEMENT + "/multi/create/",
                             json=data)

    response_data = {}
    response_data["game"] = response.json()
    response_data["user_id"] = user.user_id

    return JsonResponse(data=response_data,
                        status=response.status_code,
                        safe=False)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def tournaments(request):
    """GET: user wants to see all running tournaments
	POST: user wants to join a tournament based on ID"""
    if (request.method == "GET"):
        user_id = request.user.user_id

        response = requests.post(settings.USER_MANAGEMENT + "/tournaments/", json={'user_id': user_id})

        response_data = {}
        response_data["games"] = response.json()
        response_data["user_id"] = user_id

        return JsonResponse(data=response_data,
                            status=response.status_code,
                            safe=False)

    elif (request.method == "POST"):
        user_id = request.user.user_id
        game_id = request.data.get("game_id")

        if not game_id:
            return JsonResponse({"error": "Missing game_id in request data"},
                                status=400)

        data = {"user_id": user_id, "game_id": game_id}

        response = requests.post(
            f"{settings.USER_MANAGEMENT}/tournaments/join/", json=data)

        return JsonResponse(data=response.json(),
                            status=response.status_code,
                            safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def createTournament(request):
    """Creates a new tournament for authenticated user"""
    user = request.user

    data = {
        "user_id": user.user_id,
        "tournament_name": request.data.get("game_name"),
        "n_players": request.data.get("n_players"),
        "game_speed": request.data.get('game_speed'),
        "power_ups": request.data.get('power_ups')
    }
    logger.debug(f"create tournament: {data}")
    response = requests.post(settings.USER_MANAGEMENT + "/tournaments/create/",
                             json=data)

    response_data = {}
    response_data["game"] = response.json()
    response_data["user_id"] = user.user_id

    return JsonResponse(data=response_data,
                        status=response.status_code,
                        safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def tournamentRun(request):
    """POST: runs round of tournament with tournament_id"""
    game_id = request.data.get("game_id")

    if not game_id:
        return JsonResponse({"error": "Missing game_id in request data"},
                            status=400)

    data = {
        "tournament_id": game_id,
        "user_id": request.user.user_id,
    }

    response = requests.post(f"{settings.USER_MANAGEMENT}/tournaments/run/",
                             json=data)

    logger.info(f"tournamentRun response: {response.json()}")

    return JsonResponse(data=response.json(),
                        status=response.status_code,
                        safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def tournamentInfo(request):
    # returns tournament owner id, and user id of user making api call

    response = requests.post(f"{settings.USER_MANAGEMENT}/tournaments/info/",
                             json=request.data)

    return JsonResponse(data=response.json(),
                        status=response.status_code,
                        safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def tournamentLeave(request):
    # Playes wants to leave tournament
    data = {
        "tournament_id": request.data.get("tournament_id"),
        "user_id": request.user.user_id
    }

    logger.info(f"data: {data}")
    response = requests.post(f"{settings.USER_MANAGEMENT}/tournaments/leave/",
                             json=data)

    return JsonResponse(data=response.json(),
                        status=response.status_code,
                        safe=False)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def tournamentRank(request):
    # returns final ranking of torunament

    response = requests.post(f"{settings.USER_MANAGEMENT}/tournaments/rank/",
                             json=request.data)

    return JsonResponse(data=response.json(),
                        status=response.status_code,
                        safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat(request):
    # user can chat to a user based on id/username?
    return JsonResponse({"message": "live chat"}, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def invite(request):
    # user can invite friends to play, based on username/id and game id
    return JsonResponse({"message": "invite"}, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def avatar(request):
    """User can upload an avatar."""
    user = request.user

    file = request.FILES.get("profile-picture")
    if not file:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    files = {"files": (file.name, file.read(), file.content_type)}
    data = {"user_id": user.user_id}

    response = requests.post(settings.USER_MANAGEMENT + "/user/avatar/",
                             data=data,
                             files=files)

    return JsonResponse(data=response.json(),
                        status=response.status_code,
                        safe=False)


@api_view(["POST"])
def tokenRefresh(request):
    """Refresh JWT token."""
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        return JsonResponse({'message': 'Refresh token is missing, manager'},
                            status=401)

    response = requests.post(settings.USER_MANAGEMENT + "/token/refresh/",
                             cookies={'refresh_token': refresh_token})

    return JsonResponse(data=response.json(),
                        status=response.status_code,
                        safe=False)


@api_view(['POST'])
def oauth_callback(request):
    code = request.data.get('code')
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    redirect_uri = request.data.get('redirect_uri')

    # Step 1: Exchange authorization code for access token
    token_url = "https://api.intra.42.fr/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }
    token_response = requests.post(token_url, data=token_data)
    token_json = token_response.json()

    if 'access_token' not in token_json:
        return JsonResponse({"message": "Failed to obtain access token"},
                            status=400)

    access_token = token_json['access_token']

    # Step 2: Use access token to retrieve user information
    user_info_url = "https://api.intra.42.fr/v2/me"
    user_info_response = requests.get(
        user_info_url, headers={"Authorization": f"Bearer {access_token}"})
    user_info = user_info_response.json()
    avatar = None

    data = {'username': "42_" + user_info['login'], 'password': 'none'}

    # Step 3: Try to register user (might already be registered and return 409)
    register_response = requests.post(settings.USER_MANAGEMENT + "/register/",
                                      json=data)

    if register_response.status_code != 409 and register_response.status_code != 201:
        return JsonResponse(data=register_response.json(),
                            status=register_response.status_code,
                            safe=False)
    elif register_response.status_code == 201:
        avatar = user_info.get('image', {}).get('link')

    # Step 4: Login user
    rf = RequestFactory()
    login_request = rf.post('http://manager:8001/login/',
                            json.dumps(data),
                            content_type='application/json')
    login_response = login(login_request, True)
    logger.info(f"login response: \n{login_response.content}")

    response_content = login_response.content.decode('utf-8')

    # return tokens + info to front-end
    final_data = json.loads(response_content)
    final_data['username'] = user_info['login']
    final_data['avatar'] = avatar

    return JsonResponse(data=final_data,
                        status=login_response.status_code,
                        safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_avatar(request):
    user_id = request.user.user_id
    avatar_url = request.data.get('avatar')

    if avatar_url:
        avatar_response = requests.get(avatar_url)
        if avatar_response.status_code == 200:
            avatar_file = SimpleUploadedFile(
                name=avatar_url.split('/')[-1],
                content=avatar_response.content,
                content_type=avatar_response.headers['Content-Type'])

            files = {
                "files": (avatar_file.name, avatar_file.read(),
                          avatar_file.content_type)
            }
            data = {"user_id": user_id}

            upload_response = requests.post(settings.USER_MANAGEMENT +
                                            "/user/avatar/",
                                            data=data,
                                            files=files)

            return JsonResponse(data=upload_response.json(),
                                status=upload_response.status_code,
                                safe=False)
    else:
        return JsonResponse({"message": "no avatar link found"}, status=200)
